# deploy/nginx — Revy staging (createit.digital)

Production-ready vhosts for **revy.createit.digital** + **auth.revy.createit.digital**.  
TLS: DNS-01 (no port 80) — see `docs/utils/CERTBOT_DIGITALOCEAN_DNS_RENEWAL.md`.

## Files

| File | Install path |
|------|----------------|
| `revy.createit.digital.conf` | `/etc/nginx/sites-available/revy.createit.digital` |
| `auth.revy.createit.digital.conf` | `/etc/nginx/sites-available/auth.revy.createit.digital` |
| `nginx-http.snippet` | inside `http { }` in `/etc/nginx/nginx.conf` |

Templates with `<domain>` placeholders: `internal-docs/starter-pack/deploy/nginx/*.example`.

## Deploy

```bash
# From repo on droplet
sudo cp deploy/nginx/nginx-http.snippet /etc/nginx/conf.d/revy-rate-limit.conf
# Or paste limit_req_zone line into nginx.conf http {}

sudo cp deploy/nginx/revy.createit.digital.conf /etc/nginx/sites-available/
sudo cp deploy/nginx/auth.revy.createit.digital.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/revy.createit.digital /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/auth.revy.createit.digital /etc/nginx/sites-enabled/

# Remove certbot stub / port-80 blocks from sites-enabled
sudo nginx -t && sudo systemctl reload nginx
```

## Wiring

| Service | Host port | Container |
|---------|-----------|-----------|
| API | `127.0.0.1:8000` | `revy-api` |
| SPA | `127.0.0.1:5173` | `revy-web` |
| Keycloak | `127.0.0.1:8080` | `revy-kc` |
| KC health | `127.0.0.1:9000` | `revy-kc` (not public) |

Cert: `/etc/letsencrypt/live/revy.createit.digital/{fullchain,privkey}.pem`
