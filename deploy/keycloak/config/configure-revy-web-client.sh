#!/usr/bin/env bash
# deploy/keycloak/config/configure-revy-web-client.sh
#
# Idempotent Keycloak Admin CLI setup for the revy-web SPA client.
# Fixes OIDC logout: post_logout_redirect_uri must be allowed on the client or
# Keycloak returns "Invalid redirect uri" and the SSO session survives sign-out.
#
# Run on the droplet from this directory (requires revy-kc + .env):
#   chmod +x configure-revy-web-client.sh
#   ./configure-revy-web-client.sh
#
# Optional overrides:
#   KC_CONTAINER=revy-kc KC_REALM=revy APP_ORIGIN=https://revy.createit.digital ./configure-revy-web-client.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "error: .env not found in $SCRIPT_DIR" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

KC_CONTAINER="${KC_CONTAINER:-revy-kc}"
KC_REALM="${KC_REALM:-revy}"
KC_WEB_CLIENT_ID="${KC_WEB_CLIENT_ID:-revy-web}"
APP_ORIGIN="${APP_ORIGIN:-https://revy.createit.digital}"

KCADM=(docker exec "$KC_CONTAINER" /opt/keycloak/bin/kcadm.sh)

if ! docker ps --format '{{.Names}}' | grep -qx "$KC_CONTAINER"; then
  echo "error: container $KC_CONTAINER is not running" >&2
  exit 1
fi

echo "Configuring Keycloak client ${KC_WEB_CLIENT_ID} in realm ${KC_REALM}..."

"${KCADM[@]}" config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user "${KC_BOOTSTRAP_ADMIN_USERNAME:?}" \
  --password "${KC_BOOTSTRAP_ADMIN_PASSWORD:?}"

CLIENT_UUID="$("${KCADM[@]}" get clients -r "$KC_REALM" -q "clientId=$KC_WEB_CLIENT_ID" --fields id --format csv --noquotes | tail -n1)"
if [[ -z "$CLIENT_UUID" || "$CLIENT_UUID" == "id" ]]; then
  echo "error: client ${KC_WEB_CLIENT_ID} not found in realm ${KC_REALM}" >&2
  exit 1
fi

REDIRECT_URIS=(
  "http://localhost:5173/*"
  "http://127.0.0.1:5173/*"
  "${APP_ORIGIN}/*"
)
WEB_ORIGINS=(
  "http://localhost:5173"
  "http://127.0.0.1:5173"
  "${APP_ORIGIN}"
)

REDIRECT_CSV=$(IFS=,; echo "${REDIRECT_URIS[*]}")
WEB_ORIGIN_CSV=$(IFS=,; echo "${WEB_ORIGINS[*]}")

# "+" = inherit Valid redirect URIs as Valid post logout redirect URIs (Keycloak OIDC).
"${KCADM[@]}" update "clients/${CLIENT_UUID}" -r "$KC_REALM" \
  -s "redirectUris=[\"${REDIRECT_URIS[0]}\",\"${REDIRECT_URIS[1]}\",\"${REDIRECT_URIS[2]}\"]" \
  -s "webOrigins=[\"${WEB_ORIGINS[0]}\",\"${WEB_ORIGINS[1]}\",\"${WEB_ORIGINS[2]}\"]" \
  -s 'attributes.post.logout.redirect.uris=+' \
  -s 'publicClient=true' \
  -s 'standardFlowEnabled=true' \
  -s 'directAccessGrantsEnabled=false'

echo "OK: ${KC_WEB_CLIENT_ID} (${CLIENT_UUID})"
echo "  redirectUris: ${REDIRECT_CSV}"
echo "  webOrigins: ${WEB_ORIGIN_CSV}"
echo "  post.logout.redirect.uris: + (inherit redirect URIs)"
echo ""
echo "Verify logout end-to-end: sign in → sign out → Keycloak must redirect back to ${APP_ORIGIN}/login without 'Invalid redirect uri'."
