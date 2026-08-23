#!/usr/bin/env bash
# Generate strong secrets into a target env file (default: .env).
# Usage: ./scripts/generate_secrets.sh [env-file]
set -euo pipefail

TARGET="${1:-.env}"
touch "$TARGET"

gen_jwt() { openssl rand -hex 32; }
gen_fernet() { python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null \
  || python3 - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
}

replace_or_append() {
  local key="$1" value="$2" file="$3"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >>"$file"
  fi
}

if [ -f "$TARGET" ] && grep -qE "^JWT_SECRET=(CHANGE_ME|.*)" "$TARGET" && ! grep -qE "^JWT_SECRET=CHANGE_ME" "$TARGET" && [ "${KEEP_EXISTING:-0}" = "1" ]; then
  echo "[generate_secrets] $TARGET already has a JWT_SECRET (KEEP_EXISTING=1) — leaving untouched."
  exit 0
fi

echo "[generate_secrets] writing fresh secrets into $TARGET"
replace_or_append "JWT_SECRET" "$(gen_jwt)" "$TARGET"
replace_or_append "ENCRYPTION_KEY" "$(gen_fernet)" "$TARGET"

echo "[generate_secrets] done. Do NOT commit $TARGET."
