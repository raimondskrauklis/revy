# Revy — environment templates

Canonical env examples for local development and production. Copy from here — do not commit real `.env` files.

## Where variables live

| Group | Local dev | Production droplet | GitHub Actions |
|-------|-----------|-------------------|----------------|
| Backend | `backend/.env` | `/mnt/revy_volume/backend/.env` | `CI_*` test secrets |
| Frontend `VITE_*` | `frontend/.env.local` | Baked at CI build — **not** on droplet | Repository secrets |
| Keycloak | — | `/mnt/revy_volume/keycloak/config/` | `deploy/keycloak/config/` |
| Deploy | — | — | `DOCR_TOKEN`, `DROPLET_IP`, `SSH_PRIVATE_KEY` |
| Nginx vhosts | — | `/etc/nginx/sites-available/` | `deploy/nginx/*.conf` |

Production frontend is static `serve -s dist` — changing `VITE_*` requires **rebuild + redeploy** of `revy-web`.

**Production URLs (`createit.digital`):** SPA/API `https://revy.createit.digital`, Keycloak `https://auth.revy.createit.digital` (not `/auth` on the app host).

## Files

| File | Copy to |
|------|---------|
| `backend/.env.example` | `backend/.env` (local dev — canonical) |
| `backend.env.production.example` | droplet `/mnt/revy_volume/backend/.env` (deploy phase) |
| `frontend.env.local.example` | `frontend/.env.local` |
| `frontend.env.production.example` | GitHub Actions secrets (build-time `VITE_*`) |
| `github-actions.secrets.example` | GitHub → Settings → Secrets checklist |
| `deploy.workflow.env.example` | Reference for `.github/workflows/deploy.yml` |

## Quick start (local)

```bash
cp backend/.env.example backend/.env
# Set DATABASE_URL / TEST_DATABASE_URL to your DO managed cluster (see deploy/sql/postgres-extensions.sql)
docker compose -f backend/docker-compose.yml up -d   # Redis only
```

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
