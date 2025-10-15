#!/usr/bin/env bash
set -euo pipefail

FILE="${1:-audit-bundle.json}"
if [[ ! -f "$FILE" ]]; then
  echo "error: $FILE not found" >&2
  exit 1
fi

# Write sha256 checksum
sha256sum "$FILE" | awk '{print $1}' > "${FILE}.sha256"
echo "wrote ${FILE}.sha256"

# Optional GPG detached signature
if command -v gpg >/dev/null 2>&1; then
  if [[ -n "${GPG_KEY:-}" ]]; then
    TMPGNUPG=$(mktemp -d)
    chmod 700 "$TMPGNUPG"
    export GNUPGHOME="$TMPGNUPG"
    echo "$GPG_KEY" | gpg --batch --yes --import
    PASS="${GPG_PASSPHRASE:-}"
    if [[ -n "$PASS" ]]; then
      echo "$PASS" | gpg --batch --yes --pinentry-mode loopback --passphrase-fd 0 --output "${FILE}.asc" --armor --detach-sign "$FILE" || true
    else
      gpg --batch --yes --output "${FILE}.asc" --armor --detach-sign "$FILE" || true
    fi
    echo "wrote ${FILE}.asc"
    rm -rf "$TMPGNUPG"
  fi
fi

exit 0
