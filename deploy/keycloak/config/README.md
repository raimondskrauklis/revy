# Keycloak — droplet deploy bundle (KC 26)

Copy this **entire `config/` folder** to the droplet:

```text
/mnt/revy_volume/keycloak/config/
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
cd /mnt/revy_volume/keycloak/config
cp .env.example .env
chmod 600 .env
# edit .env — passwords, DB URL

docker network create revy-net 2>/dev/null || true
docker compose build
docker compose up -d
curl -sf http://127.0.0.1:9000/health/ready
curl -s https://auth.revy.createit.digital/realms/revy/.well-known/openid-configuration | head
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
cd /mnt/revy_volume/keycloak/config
docker compose down
docker compose build --no-cache   # after Dockerfile or KC version bump
docker compose up -d --force-recreate
```

## Checks

| | |
|-|-|
| Health | `curl -sf http://127.0.0.1:9000/health/ready` |
| Nginx | `deploy/nginx/auth.revy.createit.digital.conf` |
| API env | `KEYCLOAK_URL=http://keycloak:8080` in `/mnt/revy/backend/.env` |
