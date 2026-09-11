#!/usr/bin/env bash
# Generate strong secrets into a target env file (default: .env).
#
# Usage: ./scripts/generate_secrets.sh [--force|--keep-existing] [env-file]
#
# Safety: JWT_SECRET and ENCRYPTION_KEY are the platform's root credentials —
# rotating ENCRYPTION_KEY permanently destroys every encrypted secret value,
# and rotating JWT_SECRET invalidates all outstanding access tokens. The
# script therefore REFUSES to overwrite existing real values unless --force
# (or FORCE=1) is passed, and says what would break before doing it.
set -euo pipefail

FORCE="${FORCE:-0}"
KEEP_EXISTING="${KEEP_EXISTING:-0}"
TARGET=""

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --keep-existing) KEEP_EXISTING=1 ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$arg"; else echo "unexpected argument: $arg" >&2; exit 2; fi
      ;;
  esac
done
TARGET="${TARGET:-.env}"
touch "$TARGET"

gen_jwt() { openssl rand -hex 32; }
gen_fernet() { python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null \
  || python3 - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
}

# A key is "real" when present and not a CHANGE_ME placeholder or empty.
existing_real_keys() {
  local key
  for key in JWT_SECRET ENCRYPTION_KEY; do
    if grep -qE "^${key}=." "$TARGET" && ! grep -qE "^${key}=CHANGE_ME" "$TARGET"; then
      echo "$key"
    fi
  done
}

REAL_KEYS="$(existing_real_keys)"

if [ -n "$REAL_KEYS" ] && [ "$KEEP_EXISTING" = "1" ] && [ "$FORCE" != "1" ]; then
  echo "[generate_secrets] $TARGET already has: $(echo "$REAL_KEYS" | tr '\n' ' ')(KEEP_EXISTING=1) — leaving untouched."
  exit 0
fi

if [ -n "$REAL_KEYS" ] && [ "$FORCE" != "1" ]; then
  echo "[generate_secrets] REFUSING to rotate existing keys in $TARGET: $(echo "$REAL_KEYS" | tr '\n' ' ')" >&2
  echo "[generate_secrets] Blast radius if you proceed:" >&2
  case " $REAL_KEYS " in
    *ENCRYPTION_KEY*) echo "[generate_secrets]   - ENCRYPTION_KEY: every encrypted secret value becomes permanently undecryptable" >&2 ;;
  esac
  case " $REAL_KEYS " in
    *JWT_SECRET*) echo "[generate_secrets]   - JWT_SECRET: all outstanding access tokens are invalidated (everyone logged out)" >&2 ;;
  esac
  echo "[generate_secrets] Re-run with --force to rotate anyway, or --keep-existing to leave them untouched." >&2
  exit 1
fi

echo "[generate_secrets] writing fresh secrets into $TARGET"
replace_or_append() {
  local key="$1" value="$2" file="$3"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >>"$file"
  fi
}
replace_or_append "JWT_SECRET" "$(gen_jwt)" "$TARGET"
replace_or_append "ENCRYPTION_KEY" "$(gen_fernet)" "$TARGET"

echo "[generate_secrets] done. Do NOT commit $TARGET."
