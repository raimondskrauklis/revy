# deploy/keycloak/config/Dockerfile
# BUILD-TIME ONLY — must match runtime .env where overlapping (KC_DB=postgres).
# Rebuild after changes: docker compose build --no-cache

FROM quay.io/keycloak/keycloak:26.0

ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

RUN /opt/keycloak/bin/kc.sh build

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
