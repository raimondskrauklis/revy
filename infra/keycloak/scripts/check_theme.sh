#!/usr/bin/env bash
# infra/keycloak/scripts/check_theme.sh
# Fail-closed check for the revy Keycloak login theme.
# Run from repo root: bash infra/keycloak/scripts/check_theme.sh
# Exit 0 = pass, non-zero = fail with details.

set -euo pipefail

THEME_DIR="infra/keycloak/themes/revy/login"
PROPS="$THEME_DIR/theme.properties"
CSS="$THEME_DIR/resources/css/revy-login.css"
MSG_EN="$THEME_DIR/messages/messages_en.properties"
MSG_LV="$THEME_DIR/messages/messages_lv.properties"

errors=0
warn() { echo "FAIL: $*" >&2; errors=$((errors + 1)); }

# ── 1. theme.properties exists and has required keys ──
if [[ ! -f "$PROPS" ]]; then
  warn "theme.properties not found at $PROPS"
else
  for key in parent styles darkMode; do
    if ! grep -q "^${key}=" "$PROPS"; then
      warn "$PROPS missing $key"
    fi
  done
fi

# ── 2. CSS file exists ──
if [[ ! -f "$CSS" ]]; then
  warn "revy-login.css not found at $CSS"
fi

# ── 3. Messages: EN exists ──
if [[ ! -f "$MSG_EN" ]]; then
  warn "messages_en.properties not found at $MSG_EN"
fi

# ── 4. Messages: LV exists ──
if [[ ! -f "$MSG_LV" ]]; then
  warn "messages_lv.properties not found at $MSG_LV"
fi

# ── 5. LV keys subset of EN keys ──
if [[ -f "$MSG_EN" ]] && [[ -f "$MSG_LV" ]]; then
  en_keys=$(grep -E '^[^#=]+=' "$MSG_EN" | cut -d= -f1 | sort -u)
  lv_keys=$(grep -E '^[^#=]+=' "$MSG_LV" | cut -d= -f1 | sort -u)
  extra=$(comm -23 <(echo "$lv_keys") <(echo "$en_keys"))
  if [[ -n "$extra" ]]; then
    warn "LV keys not present in EN: $extra"
  fi
fi

# ── 6. All #hex in revy-login.css from token block or documented layout hex list ──
if [[ -f "$CSS" ]]; then
  # Extract all unique #hex values from CSS (case-insensitive)
  hex_values=$(grep -oE '#[0-9a-fA-F]{3,8}' "$CSS" | sort -u)

  # Token block hex (from tokens.revy.css html.dark L63–106)
  token_hex="#07140c #0d1c14 #1e3a28 #2f5840 #4a7a5c #d5ead0 #c5e0b8 #86a882 #5e7c5c #132418 #1b3322 #a8dc84 #a8d4e8 #d4a84b #e06b6b"

  # Documented layout hex (KC class overrides listed in CSS header comment)
  layout_hex="#000000 #07140c #0d1c14 #1e3a28 #2f5840 #4a7a5c #d5ead0 #c5e0b8 #86a882 #5e7c5c #132418 #1b3322 #a8dc84 #a8d4e8 #d4a84b #e06b6b"

  # Combine accepted hex
  accepted="$token_hex $layout_hex"

  for hex in $hex_values; do
    hex_lower=$(echo "$hex" | tr '[:upper:]' '[:lower:]')
    found=0
    for acc in $accepted; do
      acc_lower=$(echo "$acc" | tr '[:upper:]' '[:lower:]')
      if [[ "$hex_lower" == "$acc_lower" ]]; then
        found=1
        break
      fi
    done
    if [[ $found -eq 0 ]]; then
      warn "Unlisted hex in revy-login.css: $hex (not in token block or documented layout hex list)"
    fi
  done
fi

# ── result ──
if [[ $errors -eq 0 ]]; then
  echo "check_theme.sh: PASS — $THEME_DIR"
  exit 0
else
  echo "check_theme.sh: FAIL — $errors error(s)" >&2
  exit 1
fi
