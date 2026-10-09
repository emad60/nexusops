#!/usr/bin/env bash
# NexusOps agent installer (protocol v2).
#
#   sudo NEXUSOPS_ENROLL_TOKEN=nxk_... NEXUSOPS_SERVER=https://cp.example.com \
#        bash agent/install.sh
#
#   # or, for an already-enrolled node:
#   sudo NEXUSOPS_TOKEN=nxa_... NEXUSOPS_SERVER=https://cp.example.com bash agent/install.sh
#
# The credential travels through the environment, never as a command-line
# argument: argv is visible in `ps`, /proc and shell history. Re-running the
# script upgrades in place and preserves an already-stored node credential.
#
# Transport is HTTPS-only. A plain-HTTP URL is refused here unless it targets
# loopback (a local test control plane), and the agent itself never disables
# certificate verification — point NEXUSOPS_CA_BUNDLE at a private CA instead.
set -euo pipefail

SERVER="${NEXUSOPS_SERVER:-}"
TOKEN="${NEXUSOPS_TOKEN:-}"
ENROLL_TOKEN="${NEXUSOPS_ENROLL_TOKEN:-}"
INTERVAL="${NEXUSOPS_INTERVAL:-30}"
CA_BUNDLE="${NEXUSOPS_CA_BUNDLE:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --ca-bundle) CA_BUNDLE="$2"; shift 2 ;;
    # Accepted for backwards compatibility with the v1 invocation, but the
    # token is still best delivered through the environment.
    --token) TOKEN="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SERVER" ]]; then
  echo "usage: NEXUSOPS_ENROLL_TOKEN=nxk_... $0 --server https://<control-plane>" >&2
  exit 2
fi

# HTTPS-only, with a loopback exemption for local testing. This mirrors the
# agent's own check so a misconfigured URL fails before anything is installed.
case "$SERVER" in
  https://*) : ;;
  http://localhost*|http://127.0.0.1*|http://[::1]*|http://169.254.*) : ;;
  http://*)
    echo "refusing open HTTP server URL '$SERVER': credentials would be sent in the clear." >&2
    echo "Use https:// (terminate TLS at your edge)." >&2
    exit 2 ;;
  *)
    echo "invalid server URL '$SERVER': expected an https:// base URL" >&2
    exit 2 ;;
esac

if [[ -z "$TOKEN" && -z "$ENROLL_TOKEN" ]]; then
  # Hidden prompt: never echoed, never in argv.
  read -r -s -p "Enrollment token (nxk_...): " ENROLL_TOKEN
  echo
fi

INSTALL_DIR=/usr/local/lib/nexusops-agent
CONF_DIR=/etc/nexusops-agent
TOKEN_FILE="$CONF_DIR/token"
ENV_FILE=/etc/default/nexusops-agent

install -d -m 0755 "$INSTALL_DIR"
install -m 0755 "$(dirname "$0")/nexusops_agent.py" "$INSTALL_DIR/nexusops_agent.py"

# Owner-only config directory BEFORE any secret is written: a 0644 window
# between create and chmod would expose the credential to every local user.
install -d -m 0700 "$CONF_DIR"

umask 077
if [[ -n "$TOKEN" ]]; then
  # An already-enrolled node credential. Written atomically, mode 0600.
  printf '%s' "$TOKEN" > "$TOKEN_FILE.new"
  chmod 600 "$TOKEN_FILE.new"
  mv -f "$TOKEN_FILE.new" "$TOKEN_FILE"
fi

# Configuration file. Non-secret keys plus, at most, a one-time enrollment token
# the agent consumes on first start and then drops. ``EnvironmentFile=-`` in the
# systemd unit tolerates the file being absent.
{
  echo "NEXUSOPS_SERVER=$SERVER"
  echo "NEXUSOPS_INTERVAL=$INTERVAL"
  echo "NEXUSOPS_TOKEN_FILE=$TOKEN_FILE"
  if [[ -n "$CA_BUNDLE" ]]; then
    echo "NEXUSOPS_CA_BUNDLE=$CA_BUNDLE"
  fi
  if [[ -n "$ENROLL_TOKEN" ]]; then
    echo "NEXUSOPS_ENROLL_TOKEN=$ENROLL_TOKEN"
  fi
} > "$ENV_FILE.new"
# World-readable only when it carries no secret.
if [[ -n "$ENROLL_TOKEN" ]]; then
  chmod 600 "$ENV_FILE.new"
else
  chmod 644 "$ENV_FILE.new"
fi
mv -f "$ENV_FILE.new" "$ENV_FILE"

if command -v systemctl >/dev/null 2>&1; then
  install -m 0644 "$(dirname "$0")/nexusops-agent.service" /etc/systemd/system/nexusops-agent.service
  systemctl daemon-reload
  systemctl enable --now nexusops-agent
  # Clear the one-time enrollment token from the env file now that the service
  # has started and stored its own credential.
  if [[ -n "$ENROLL_TOKEN" ]]; then
    sed -i '/^NEXUSOPS_ENROLL_TOKEN=/d' "$ENV_FILE"
    systemctl restart nexusops-agent
  fi
  echo "installed: systemctl status nexusops-agent"
else
  echo "systemd not found; start manually:"
  echo "  set -a; . $ENV_FILE; set +a; python3 $INSTALL_DIR/nexusops_agent.py"
fi
