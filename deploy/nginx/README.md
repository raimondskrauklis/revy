# deploy/nginx — Revy example vhosts

Production-ready nginx templates for an **app.example.com** + **auth.example.com** layout.  
TLS: DNS-01 (no port 80) — see `docs/utils/CERTBOT_DNS_RENEWAL.md`.

Replace `app.example.com` / `auth.example.com` with your real domains before installing.

## Files

| File | Install path |
|------|----------------|
| `app.example.com.conf` | `/etc/nginx/sites-available/app.example.com` |
| `auth.example.com.conf` | `/etc/nginx/sites-available/auth.example.com` |
| `nginx-http.snippet` | inside `http { }` in `/etc/nginx/nginx.conf` |

## Deploy

```bash
# From repo on server
sudo cp deploy/nginx/nginx-http.snippet /etc/nginx/conf.d/revy-rate-limit.conf
# Or paste limit_req_zone line into nginx.conf http {}

sudo cp deploy/nginx/app.example.com.conf /etc/nginx/sites-available/app.example.com
sudo cp deploy/nginx/auth.example.com.conf /etc/nginx/sites-available/auth.example.com
sudo ln -sf /etc/nginx/sites-available/app.example.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/auth.example.com /etc/nginx/sites-enabled/

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

Cert: `/etc/letsencrypt/live/app.example.com/{fullchain,privkey}.pem`
