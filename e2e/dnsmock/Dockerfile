# E2E-only image: an authoritative mock DNS server for the Phase 4 journey.
#
# `alpine` + `python3` + one stdlib-only script, so `make e2e` builds this from
# images that are already on the machine — no PyPI, no pip, no dnspython.
FROM alpine:3.20

RUN apk add --no-cache python3

COPY dnsmock.py /opt/dnsmock/dnsmock.py

EXPOSE 53/udp
EXPOSE 8053

CMD ["python3", "/opt/dnsmock/dnsmock.py"]
