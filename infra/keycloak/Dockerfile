# infra/keycloak/Dockerfile
# Layers Revy login theme onto the built revy-keycloak:26.0 image.
# Prerequisite: deploy/keycloak/config/docker-compose.yml `docker compose build` must
# produce revy-keycloak:26.0 first (KC 26 with vymalo webhook JARs, start --optimized).
#
# Build from repo root:
#   docker build -t revy-keycloak-themed:26.0 -f infra/keycloak/Dockerfile infra/keycloak/

FROM revy-keycloak:26.0

# Directory theme — placed alongside bundled JAR themes, KC auto-discovers.
COPY themes/revy /opt/keycloak/themes/revy

# No kc.sh build needed — base image already ran it.
# No provider JARs needed — already in base.