#!/usr/bin/env bash
# deploy/keycloak/config/fetch-webhook-providers.sh
# Download vymalo webhook JARs into providers/ and verify sha256.
set -euo pipefail

VERSION="0.10.0-rc.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/providers"
mkdir -p "${OUT_DIR}"

CORE_JAR="keycloak-webhook-provider-core-${VERSION}-all.jar"
HTTP_JAR="keycloak-webhook-provider-http-${VERSION}-all.jar"
BASE_URL="https://github.com/vymalo/keycloak-webhook/releases/download/v${VERSION}"

curl -fsSL -o "${OUT_DIR}/${CORE_JAR}" "${BASE_URL}/${CORE_JAR}"
curl -fsSL -o "${OUT_DIR}/${HTTP_JAR}" "${BASE_URL}/${HTTP_JAR}"

printf '%s  %s\n' \
  "3ab87a1fc539143923cac007d13ca92853895b8240963f6ab12d04622f3a7f97" "${OUT_DIR}/${CORE_JAR}" \
  "e5614443bdc8f9bba85ea0dd08e234b34099594b4069e6495f034636979eb3b9" "${OUT_DIR}/${HTTP_JAR}" \
  | sha256sum -c -

echo "OK: ${OUT_DIR}/${CORE_JAR}"
echo "OK: ${OUT_DIR}/${HTTP_JAR}"
