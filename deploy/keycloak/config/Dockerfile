# deploy/keycloak/config/Dockerfile
# BUILD-TIME ONLY — must match runtime .env where overlapping (KC_DB=postgres).
# Rebuild after changes: docker compose build --no-cache
#
# vymalo/keycloak-webhook 0.10.0-rc.1 (KC 26):
#   core sha256: 3ab87a1fc539143923cac007d13ca92853895b8240963f6ab12d04622f3a7f97
#   http sha256: e5614443bdc8f9bba85ea0dd08e234b34099594b4069e6495f034636979eb3b9

FROM quay.io/keycloak/keycloak:26.0

ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

ARG VYMALO_WEBHOOK_VERSION=0.10.0-rc.1

USER root
RUN mkdir -p /opt/keycloak/providers \
    && curl -fsSL \
      -o "/opt/keycloak/providers/keycloak-webhook-provider-core-${VYMALO_WEBHOOK_VERSION}-all.jar" \
      "https://github.com/vymalo/keycloak-webhook/releases/download/v${VYMALO_WEBHOOK_VERSION}/keycloak-webhook-provider-core-${VYMALO_WEBHOOK_VERSION}-all.jar" \
    && curl -fsSL \
      -o "/opt/keycloak/providers/keycloak-webhook-provider-http-${VYMALO_WEBHOOK_VERSION}-all.jar" \
      "https://github.com/vymalo/keycloak-webhook/releases/download/v${VYMALO_WEBHOOK_VERSION}/keycloak-webhook-provider-http-${VYMALO_WEBHOOK_VERSION}-all.jar"
USER keycloak

RUN /opt/keycloak/bin/kc.sh build

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
