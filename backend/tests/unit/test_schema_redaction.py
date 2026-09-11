"""Outbound-schema redaction: monitor probe credentials and webhook targets.

Regression coverage for two metadata-leak findings:

* MonitorOut returned probe headers and the full URL verbatim — probe headers
  are where users put ``Authorization: Bearer …`` / ``X-API-Key`` and monitor
  URLs commonly carry ``?token=…`` query credentials. Values are masked / the
  query stripped on the way out; the full values stay server-side.
* ChannelOut.display_target used to keep the URL *path* — but for the most
  common webhook families (Slack ``/services/T/B/XXXX``, Discord
  ``/api/webhooks/{id}/{token}``, Telegram ``/bot<TOKEN>/sendMessage``) the
  credential IS the path segment, so the masked reference was not masked.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.enums import MonitorStatus
from app.schemas.monitor import MonitorOut, is_sensitive_header, mask_sensitive_headers
from app.services.notification_service import mask_target

# --- MonitorOut: header masking ----------------------------------------------------


def test_mask_sensitive_headers_masks_credential_bearing_names() -> None:
    headers = {
        "Authorization": "Bearer topsecret",
        "X-API-Key": "nxo_live_abc",
        "Cookie": "session=xyz",
        "X-Auth-Token": "tok",
        "X-Custom-Trace": "plain-value",
    }
    masked = mask_sensitive_headers(headers)
    assert masked["Authorization"] == "******"
    assert masked["X-API-Key"] == "******"
    assert masked["Cookie"] == "******"
    assert masked["X-Auth-Token"] == "******"
    assert masked["X-Custom-Trace"] == "plain-value"  # innocent headers stay usable
    # The original dict is untouched.
    assert headers["Authorization"] == "Bearer topsecret"


def test_is_sensitive_header_is_case_insensitive() -> None:
    assert is_sensitive_header("authorization")
    assert is_sensitive_header("PRIVATE-TOKEN")
    assert is_sensitive_header("x-session-id")
    assert not is_sensitive_header("accept")


def _monitor_out(url: str, headers: dict[str, str]) -> MonitorOut:
    now = datetime.now(UTC)
    return MonitorOut.model_validate(
        {
            "id": uuid4(),
            "created_at": now,
            "updated_at": now,
            "name": "cred-hygiene",
            "url": url,
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 10.0,
            "expected_status": 200,
            "headers": headers,
            "skip_tls_verify": False,
            "follow_redirects": True,
            "enabled": True,
            "status": MonitorStatus.UP,
            "consecutive_failures": 0,
            "consecutive_successes": 1,
            "failure_threshold": 3,
            "success_threshold": 2,
            "next_check_at": now + timedelta(seconds=60),
        }
    )


def test_monitor_out_strips_url_query_credentials() -> None:
    out = _monitor_out("https://status.example.com/health?token=supersecret&x=1", {})
    dumped = out.model_dump(mode="json")
    assert "supersecret" not in dumped["url"]
    assert dumped["url"] == "https://status.example.com/health"


def test_monitor_out_masks_header_values() -> None:
    out = _monitor_out(
        "https://status.example.com/health",
        {"Authorization": "Bearer topsecret", "X-API-Key": "nxo_live_abc", "Accept": "text/html"},
    )
    dumped = out.model_dump(mode="json")
    assert dumped["headers"]["Authorization"] == "******"
    assert dumped["headers"]["X-API-Key"] == "******"
    assert dumped["headers"]["Accept"] == "text/html"
    serialized = str(dumped)
    assert "topsecret" not in serialized and "nxo_live_abc" not in serialized


# --- channel display_target: path-embedded credentials ------------------------------


def test_mask_target_hides_slack_path_credential() -> None:
    url = "https://hooks.slack.com/services/T0000000/B0000000/XXXXXXXXXXXXXXXXXXXX"
    display = mask_target("WEBHOOK", {"url": url})
    assert display.startswith("https://hooks.slack.com/")
    assert "services" not in display
    assert "XXXXXXXXXXXXXXXXXXXX" not in display


def test_mask_target_hides_discord_and_telegram_path_credentials() -> None:
    discord = mask_target(
        "WEBHOOK",
        {"url": "https://discord.com/api/webhooks/1234567890/aBcDeFgHiJkLmNoPqRsTuVwXyZ"},
    )
    assert "aBcDeFgHiJkLmNoPqRsTuVwXyZ" not in discord
    assert "1234567890" not in discord

    telegram = mask_target(
        "WEBHOOK",
        {"url": "https://api.telegram.org/bot123456:ABC-DEF1234567890/sendMessage"},
    )
    assert "123456" not in telegram
    assert "ABC-DEF" not in telegram


def test_mask_target_also_drops_query_credentials() -> None:
    display = mask_target("WEBHOOK", {"url": "https://example.com/hook?key=secretvalue"})
    assert "secretvalue" not in display


def test_mask_target_email_keeps_recipients() -> None:
    display = mask_target("EMAIL", {"recipients": ["ops@example.com", "oncall@example.com"]})
    assert display == "ops@example.com (+1 more)"


def test_mask_target_empty_url_is_blank() -> None:
    assert mask_target("WEBHOOK", {"url": ""}) == ""
