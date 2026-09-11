#!/usr/bin/env bash
# NexusOps agent installer.
#
#   sudo ./install.sh --server https://nexusops-host:8443 --token nxa_...
#
# Copies the agent to /usr/local/lib/nexusops-agent, installs a systemd unit
# and starts the service. Re-running updates in place. Systems without systemd:
# run the agent under your supervisor of choice (see docs/agent.md).
set -euo pipefail

SERVER="" TOKEN="" INTERVAL="30"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER="$2"; shift 2 ;;
    --token) TOKEN="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SERVER" || -z "$TOKEN" ]]; then
  echo "usage: $0 --server URL --token nxa_... [--interval SECONDS]" >&2
  exit 2
fi

INSTALL_DIR=/usr/local/lib/nexusops-agent
ENV_FILE=/etc/default/nexusops-agent

install -d -m 0755 "$INSTALL_DIR"
install -m 0755 "$(dirname "$0")/nexusops_agent.py" "$INSTALL_DIR/nexusops_agent.py"

# Create the env file with owner-only mode BEFORE any secret is written: the
# enrollment token is the server's full identity, and a 0644 window between
# create and chmod would expose it to every local user.
install -m 0600 /dev/null "$ENV_FILE"
cat >"$ENV_FILE" <<EOF
NEXUSOPS_SERVER=$SERVER
NEXUSOPS_TOKEN=$TOKEN
NEXUSOPS_INTERVAL=$INTERVAL
EOF
chmod 600 "$ENV_FILE"

if command -v systemctl >/dev/null 2>&1; then
  install -m 0644 "$(dirname "$0")/nexusops-agent.service" /etc/systemd/system/nexusops-agent.service
  systemctl daemon-reload
  systemctl enable --now nexusops-agent
  echo "installed: systemctl status nexusops-agent"
else
  echo "systemd not found; start manually:"
  echo "  NEXUSOPS_SERVER=$SERVER NEXUSOPS_TOKEN=$TOKEN python3 $INSTALL_DIR/nexusops_agent.py"
fi
