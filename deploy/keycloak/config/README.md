# Keycloak — droplet deploy bundle (KC 26)

Copy this **entire `config/` folder** to the server:

```text
/opt/revy/keycloak/config/
  .env
  .env.example
  docker-compose.yml
  docker-compose.simple.yml
  Dockerfile
  README.md
```

All commands run **from that directory** — no `-f` paths, no absolute `env_file` paths.

## First deploy

```bash
cd /opt/revy/keycloak/config
cp .env.example .env
chmod 600 .env
# edit .env — passwords, DB URL, KC_HOSTNAME

docker network create revy-net 2>/dev/null || true
docker compose build
docker compose up -d
curl -sf http://127.0.0.1:9000/health/ready
curl -s https://auth.example.com/realms/revy/.well-known/openid-configuration | head
```

## Production vs simple

| File | Use |
|------|-----|
| `docker-compose.yml` | **Default production** — custom image, `start --optimized`, fast restarts |
| `docker-compose.simple.yml` | Troubleshooting only — stock image, `start`, slower cold boot |

## Build-time vs runtime

| Dockerfile (`kc.sh build`) | `.env` (every start) |
|----------------------------|----------------------|
| `KC_DB=postgres` | `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD` |
| `KC_HEALTH_ENABLED=true` | `KC_HOSTNAME`, `KC_HOSTNAME_STRICT` |
| `KC_METRICS_ENABLED=true` | `KC_HTTP_ENABLED`, `KC_PROXY_*`, `KC_BOOTSTRAP_*` |

After changing Dockerfile: `docker compose build --no-cache && docker compose up -d`

## Restart / upgrade

```bash
cd /opt/revy/keycloak/config
docker compose down
docker compose build --no-cache   # after Dockerfile or KC version bump
docker compose up -d --force-recreate
```

## Checks

| | |
|-|-|
| Health | `curl -sf http://127.0.0.1:9000/health/ready` |
| Nginx | `deploy/nginx/auth.example.com.conf` |
| API env | `KEYCLOAK_URL=http://keycloak:8080` and `KEYCLOAK_ISSUER=https://auth.example.com/realms/revy` in `/opt/revy/backend/.env` |

## Identity webhook (vymalo 0.10.0-rc.1)

Keycloak sends identity events to Revy over **internal** `revy-net` (no public nginx route).

1. Set `KEYCLOAK_WEBHOOK_SECRET` in backend `.env` (same value as `WEBHOOK_HTTP_AUTH_PASSWORD` in KC `.env`).
2. Rebuild KC after Dockerfile changes: `docker compose build --no-cache && docker compose up -d`.
3. Register a test user in KC (or Google federated signup).
4. Verify delivery + user row:

```bash
# API logs
docker logs revy-api 2>&1 | grep keycloak_webhook

# PostgreSQL (replace connection as needed)
psql "$DATABASE_URL" -c "SELECT delivery_id, event_type, received_at FROM keycloak_webhook_deliveries ORDER BY received_at DESC LIMIT 5;"
psql "$DATABASE_URL" -c "SELECT email, keycloak_user_id, status FROM users ORDER BY created_at DESC LIMIT 5;"
```

Full tier-A/B smoke: `docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md` (includes `revy-web` logout settings in Admin Console).
