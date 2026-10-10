#!/usr/bin/env python3
"""Authoritative mock DNS for the Phase 4 E2E journey — **E2E tooling only**.

The DNS verifier in the control plane resolves a domain's authoritative
nameservers and asks *them* for the proof TXT record, so proving ownership in a
test needs a real authoritative answer, not a stubbed resolver. This process is
that nameserver:

* it is authoritative for one zone (``MOCK_ZONE``, default ``e2e.test``) and
  serves the zone apex's NS record plus the A of that nameserver;
* the journey registers the TXT record it just minted through the tiny control
  API (``POST /record``) — the token is minted by the API at runtime, so it
  cannot be baked into a zone file;
* anything **outside** the zone is forwarded verbatim to the container's own
  resolver, so pointing the api/worker at this mock (``dns:`` in the compose
  overlay) does not break resolution for the rest of the e2e stack.

Stdlib only, on purpose: the image is ``alpine`` + ``python3``, so the journey
pulls and builds nothing that is not already cached locally.

Environment:
  MOCK_ZONE           zone served authoritatively (default ``e2e.test``)
  MOCK_IP             the address this mock answers with (its own static IP)
  MOCK_DNS_PORT       UDP port to serve on (default 53)
  MOCK_CONTROL_PORT   HTTP port for the control API (default 8053)
"""

from __future__ import annotations

import json
import os
import socket
import struct
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ZONE = (os.environ.get("MOCK_ZONE") or "e2e.test").strip(".").lower()
MOCK_IP = (os.environ.get("MOCK_IP") or "172.31.253.53").strip()
DNS_PORT = int(os.environ.get("MOCK_DNS_PORT") or "53")
CONTROL_PORT = int(os.environ.get("MOCK_CONTROL_PORT") or "8053")

#: Five seconds: long enough for a whole verify run (discover NS → resolve glue →
#: ask for the TXT), short enough that a re-run never reads a stale record from
#: an intermediate resolver's cache.
TTL = 5
NAMESERVER_HOST = f"ns1.{ZONE}"

TYPE_A = 1
TYPE_NS = 2
TYPE_TXT = 16
TYPE_SOA = 6

#: Flags: QR | AA | RD | RA, with the rcode OR-ed in. Authoritative on purpose —
#: the verifier treats a non-authoritative answer for the TXT as unproven.
FLAGS = 0x8580
RCODE_NXDOMAIN = 3
RCODE_SERVFAIL = 2

_lock = threading.Lock()
_records: dict[str, dict[int, list[str]]] = {
    ZONE: {TYPE_NS: [NAMESERVER_HOST], TYPE_A: [MOCK_IP]},
    NAMESERVER_HOST: {TYPE_A: [MOCK_IP]},
}


def upstream_resolver() -> str:
    """The first nameserver in ``/etc/resolv.conf`` — Docker's embedded DNS.

    Forwarding to it (rather than to a public resolver) keeps the mock's own
    lookups inside the e2e network, so the journey needs no external DNS.
    """
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "nameserver":
                    return parts[1]
    except OSError:
        pass
    return "127.0.0.11"


UPSTREAM = upstream_resolver()


# --- record storage (control API surface) -------------------------------------


def in_zone(name: str) -> bool:
    candidate = name.strip(".").lower()
    return candidate == ZONE or candidate.endswith("." + ZONE)


def set_record(name: str, record_type: int, value: str) -> None:
    key = name.strip(".").lower()
    with _lock:
        _records.setdefault(key, {}).setdefault(record_type, [])
        if value not in _records[key][record_type]:
            _records[key][record_type].append(value)


def clear_record(name: str, record_type: int | None = None) -> None:
    key = name.strip(".").lower()
    with _lock:
        if record_type is None:
            _records.pop(key, None)
            return
        bucket = _records.get(key)
        if bucket:
            bucket.pop(record_type, None)


def snapshot() -> dict[str, dict[str, list[str]]]:
    with _lock:
        return {
            name: {str(rtype): list(values) for rtype, values in types.items()}
            for name, types in _records.items()
        }


# --- wire format --------------------------------------------------------------


def encode_name(name: str) -> bytes:
    out = b""
    for label in name.strip(".").split("."):
        raw = label.encode("ascii")
        out += bytes([len(raw)]) + raw
    return out + b"\x00"


def encode_txt(value: str) -> bytes:
    """TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes."""
    raw = value.encode("utf-8")
    chunks = [raw[index : index + 255] for index in range(0, len(raw), 255)] or [b""]
    return b"".join(bytes([len(chunk)]) + chunk for chunk in chunks)


def parse_question(packet: bytes) -> tuple[str, int, int, int]:
    """Return ``(qname, qtype, qclass, end_offset)``; ``end_offset`` is -1 on junk."""
    if len(packet) < 12:
        return "", 0, 0, -1
    offset = 12
    labels: list[str] = []
    while True:
        if offset >= len(packet):
            return "", 0, 0, -1
        length = packet[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0:
            # A compression pointer is legal in an answer, never in a question.
            return "", 0, 0, -1
        offset += 1
        if offset + length > len(packet):
            return "", 0, 0, -1
        labels.append(packet[offset : offset + length].decode("ascii", "replace"))
        offset += length
    if offset + 4 > len(packet):
        return "", 0, 0, -1
    qtype, qclass = struct.unpack("!HH", packet[offset : offset + 4])
    return ".".join(labels).lower(), qtype, qclass, offset + 4


def resource_record(rtype: int, rdata: bytes, owner: str) -> bytes:
    """One RR whose owner name is compressed to the question name at offset 12."""
    return b"\xc0\x0c" + struct.pack("!HHIH", rtype, 1, TTL, len(rdata)) + rdata


def respond(
    packet: bytes, end_offset: int, answers: list[bytes], rcode: int = 0
) -> bytes:
    transaction_id = struct.unpack("!H", packet[:2])[0]
    header = struct.pack(
        "!HHHHHH", transaction_id, FLAGS | rcode, 1, len(answers), 0, 0
    )
    return header + packet[12:end_offset] + b"".join(answers)


def answer(packet: bytes) -> bytes | None:
    """Answer from the zone, or ``None`` when the name is not ours to answer."""
    qname, qtype, qclass, end = parse_question(packet)
    if end < 0:
        return None
    if qclass != 1 or not in_zone(qname):
        return None
    with _lock:
        values = list(_records.get(qname, {}).get(qtype, []))
    records = [resource_record(qtype, _rdata(qtype, value), qname) for value in values]
    return respond(packet, end, records)


def _rdata(rtype: int, value: str) -> bytes:
    if rtype == TYPE_A:
        return socket.inet_aton(value)
    if rtype == TYPE_TXT:
        return encode_txt(value)
    return encode_name(value)


def servfail(packet: bytes) -> bytes:
    _, _, _, end = parse_question(packet)
    if end < 0:
        end = len(packet)
    return respond(packet, end, [], RCODE_SERVFAIL)


def forward(packet: bytes) -> bytes:
    """Relay a query outside the zone to the container's own resolver, verbatim."""
    if not UPSTREAM:
        return servfail(packet)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3.0)
            sock.sendto(packet, (UPSTREAM, 53))
            return sock.recvfrom(4096)[0]
    except OSError:
        return servfail(packet)


def serve_dns() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DNS_PORT))
    while True:
        try:
            packet, peer = sock.recvfrom(4096)
        except OSError:
            continue
        reply = answer(packet) or forward(packet)
        try:
            sock.sendto(reply, peer)
        except OSError:
            continue


# --- control API --------------------------------------------------------------


class ControlHandler(BaseHTTPRequestHandler):
    """The journey's only way to publish a record — no shell, no shared volume."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # the journey reads /records when it needs to; headers are noise

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _type_of(self, raw: object) -> int | None:
        if isinstance(raw, int):
            return raw
        return {"A": TYPE_A, "NS": TYPE_NS, "TXT": TYPE_TXT, "SOA": TYPE_SOA}.get(
            str(raw or "TXT").upper()
        )

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's contract
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"zone": ZONE, "address": MOCK_IP, "upstream": UPSTREAM})
        elif path == "/records":
            self._send(200, {"zone": ZONE, "records": snapshot()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's contract
        if urlparse(self.path).path != "/record":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, TypeError):
            self._send(400, {"error": "body must be JSON"})
            return
        name = str(payload.get("name") or "")
        value = str(payload.get("value") or "")
        record_type = self._type_of(payload.get("type"))
        if not in_zone(name):
            # Refusing foreign names keeps the mock authoritative for one zone
            # only — a record outside it could never be reached anyway.
            self._send(400, {"error": f"name is outside the zone {ZONE}"})
            return
        if record_type is None or not value:
            self._send(400, {"error": "type and value are required"})
            return
        set_record(name, record_type, value)
        self._send(200, {"name": name.strip(".").lower(), "type": record_type})

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's contract
        parsed = urlparse(self.path)
        if parsed.path != "/record":
            self._send(404, {"error": "not found"})
            return
        query = parse_qs(parsed.query)
        name = (query.get("name") or [""])[0]
        record_type = self._type_of((query.get("type") or [""])[0])
        clear_record(name, record_type)
        self._send(200, {"cleared": name.strip(".").lower()})


def main() -> None:
    threading.Thread(target=serve_dns, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", CONTROL_PORT), ControlHandler).serve_forever()


if __name__ == "__main__":
    main()
