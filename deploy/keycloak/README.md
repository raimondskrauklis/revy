# deploy/keycloak

**Server bundle:** copy `config/` to `/opt/revy/keycloak/config/` (or your volume) and run `docker compose` from there.

See **`config/README.md`** for full steps.

Local dev: `infra/keycloak/docker-compose.yml` (H2 in-memory, theme caches off).
