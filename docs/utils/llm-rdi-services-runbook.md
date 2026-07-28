# llm.rdi.services — Full Setup Runbook

Target: `134.199.190.250` → `llm.rdi.services`

Purpose: standalone droplet running an OpenAI-compatible translation proxy (LiteLLM) in front
of an Anthropic-format backend, fronted by Nginx with a Let's Encrypt certificate.

Run everything below as a sudo-capable user over SSH on the droplet, in order.

---

## 0. Confirm DNS is live

Before touching the droplet, confirm the `A` record resolves:

```bash
dig +short llm.rdi.services
```

Expected output:

```text
134.199.190.250
```

If nothing comes back yet, wait a few minutes for propagation before continuing.

---

## 1. System update and base packages

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3-pip \
  python3-venv \
  nginx \
  certbot \
  python3-certbot-nginx \
  ufw \
  curl
```

---

## 2. Firewall — open 22, 80, 443

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status numbered
```

Expected:

```text
OpenSSH        ALLOW IN   Anywhere
Nginx Full     ALLOW IN   Anywhere
```

Also confirm, in the DigitalOcean control panel, that the Cloud Firewall attached to this
droplet allows inbound `22`, `80`, and `443` — UFW and the Cloud Firewall are separate layers
and both must allow the ports.

---

## 3. Install LiteLLM proxy

```bash
mkdir -p ~/rtu-proxy && cd ~/rtu-proxy
python3 -m venv venv
source venv/bin/activate
pip install 'litellm[proxy]'
```

---

## 4. Configure the model mapping

Create the env file:

```bash
nano ~/rtu-proxy/.env
```

Contents:

```ini
RTU_AUTH_TOKEN=paste-your-rtu-token-here
PROXY_MASTER_KEY=pick-a-long-random-string
```

Create the LiteLLM config:

```bash
nano ~/rtu-proxy/config.yaml
```

Contents:

```yaml
model_list:
  - model_name: rtu-opus-5
    litellm_params:
      model: anthropic/azure_ai/claude-opus-5
      api_base: https://llm.ai.rtu.lv
      api_key: os.environ/RTU_AUTH_TOKEN

  - model_name: rtu-sonnet-5
    litellm_params:
      model: anthropic/azure_ai/claude-sonnet-5
      api_base: https://llm.ai.rtu.lv
      api_key: os.environ/RTU_AUTH_TOKEN

  - model_name: rtu-fable-5
    litellm_params:
      model: anthropic/azure_ai/claude-fable-5
      api_base: https://llm.ai.rtu.lv
      api_key: os.environ/RTU_AUTH_TOKEN

general_settings:
  master_key: os.environ/PROXY_MASTER_KEY
```

---

## 5. Test LiteLLM locally before wiring up Nginx

```bash
cd ~/rtu-proxy
source venv/bin/activate
set -a; source .env; set +a
litellm --config config.yaml --port 4000
```

In a second terminal on the droplet:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rtu-sonnet-5",
    "messages": [{"role": "user", "content": "Say hi in one word"}]
  }'
```

Confirm you get a normal OpenAI-style JSON response back. Stop the foreground process
(`Ctrl+C`) once confirmed — it'll be run as a service in step 9.

---

## 6. Initial Nginx config (HTTP only, for the cert challenge)

```bash
sudo nano /etc/nginx/sites-available/llm.rdi.services
```

Contents:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name llm.rdi.services;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 404;
    }
}
```

Enable the site and remove the default if it's still linked:

```bash
sudo ln -s /etc/nginx/sites-available/llm.rdi.services /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Get the certificate (HTTP-01, port 80 open)

```bash
sudo certbot --nginx -d llm.rdi.services
```

Follow the prompts (email address, terms agreement). Certbot will fetch the certificate and
typically rewrite `/etc/nginx/sites-available/llm.rdi.services` itself to add the `ssl_certificate`
lines and a `443` block automatically.

Verify:

```bash
sudo certbot certificates
```

Expected to show:

```text
Certificate Name: llm.rdi.services
Domains: llm.rdi.services
```

---

## 8. Switch renewal to DNS-01 (so port 80 can close later)

```bash
sudo apt install -y python3-certbot-dns-digitalocean

sudo install -d -m 700 /etc/letsencrypt/secrets
sudo nano /etc/letsencrypt/secrets/digitalocean.ini
```

Contents:

```ini
dns_digitalocean_token = YOUR_DIGITALOCEAN_API_TOKEN
```

Lock down permissions:

```bash
sudo chown root:root /etc/letsencrypt/secrets/digitalocean.ini
sudo chmod 600 /etc/letsencrypt/secrets/digitalocean.ini
```

Reconfigure the certificate to use DNS-01:

```bash
sudo certbot reconfigure \
  --cert-name llm.rdi.services \
  --dns-digitalocean \
  --dns-digitalocean-credentials /etc/letsencrypt/secrets/digitalocean.ini \
  --dns-digitalocean-propagation-seconds 30
```

Test renewal:

```bash
sudo certbot renew --cert-name llm.rdi.services --dry-run
```

Expected:

```text
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/llm.rdi.services/fullchain.pem (success)
```

Add the Nginx reload hook so a real renewal takes effect automatically:

```bash
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh >/dev/null <<'EOF'
#!/bin/sh
systemctl reload nginx
EOF
sudo chmod 755 /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

Confirm the renewal timer is active:

```bash
systemctl status certbot.timer
sudo systemctl enable --now certbot.timer
```

---

## 9. Run LiteLLM as a permanent service

```bash
sudo nano /etc/systemd/system/rtu-proxy.service
```

Contents — replace **all four** occurrences of `youruser` with your actual username (check with
`whoami`); it's easy to only change the `User=` line and miss the other three, which causes the
service to fail silently with `Result: resources` and no journal output:

```ini
[Unit]
Description=LiteLLM RTU translation proxy
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/rtu-proxy
EnvironmentFile=/home/youruser/rtu-proxy/.env
ExecStart=/home/youruser/rtu-proxy/venv/bin/litellm --config config.yaml --port 4000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rtu-proxy
sudo systemctl status rtu-proxy --no-pager
```

Sanity check before moving on — confirm no `youruser` is left anywhere in the unit:

```bash
sudo systemctl cat rtu-proxy | grep youruser
```

This should print nothing. If it prints a line, that line still needs fixing.

---

## 10. Final Nginx config (443 only, proxying to LiteLLM)

```bash
sudo nano /etc/nginx/sites-available/llm.rdi.services
```

Replace the entire file with:

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name llm.rdi.services;

    ssl_certificate /etc/letsencrypt/live/llm.rdi.services/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/llm.rdi.services/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 11. End-to-end test over HTTPS

```bash
curl https://llm.rdi.services/v1/chat/completions \
  -H "Authorization: Bearer $PROXY_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rtu-sonnet-5",
    "messages": [{"role": "user", "content": "hi"}]
  }'
```

Confirm a valid response comes back over HTTPS.

---

## 12. Close port 80 (once DNS-01 renewal is confirmed working)

Only do this after step 8's dry-run succeeded.

```bash
sudo ufw delete allow 'Nginx HTTP'
sudo ufw status numbered
```

If the profile name doesn't match an existing rule, delete by rule number instead:

```bash
sudo ufw delete <RULE_NUMBER>
```

Also remove the `TCP 80` inbound rule from the DigitalOcean Cloud Firewall attached to this
droplet in the control panel, keeping only `22` and `443`.

Confirm nothing is listening on 80 anymore:

```bash
sudo ss -lntp | grep -E ':(80|443)\b'
```

Expected: only `443` shows up.

---

## 13. Configure Cursor

1. **Cursor → Settings → Cursor Settings → Models**
2. Under **API Keys**:
   - Enable **OpenAI API Key**, paste in `PROXY_MASTER_KEY`
   - Enable **Override OpenAI Base URL** → `https://llm.rdi.services/v1`
3. Under **Models**, **Add Model** for each of `rtu-opus-5`, `rtu-sonnet-5`, `rtu-fable-5`, and
   toggle them on.
4. If Anthropic BYOK is also enabled in Cursor, turn it off to avoid conflicts.
5. Select one of the `rtu-*` models from the model picker in a chat.

Note: Cursor's tab autocomplete and inline edit (Cmd/Ctrl+K) always use Cursor's own backend and
will not route through this proxy — only chat/agent mode does.

---

## Full verification checklist

```bash
# Certificate
sudo certbot certificates

# Renewal authenticator
sudo grep -E '^(authenticator|dns_digitalocean)' /etc/letsencrypt/renewal/llm.rdi.services.conf

# Renewal dry run
sudo certbot renew --cert-name llm.rdi.services --dry-run

# Nginx
sudo nginx -t
sudo systemctl is-active nginx

# Proxy service
sudo systemctl is-active rtu-proxy
sudo journalctl -u rtu-proxy --since "10 minutes ago"

# Timer
sudo systemctl is-active certbot.timer

# Listening ports
sudo ss -lntp | grep -E ':(80|443)\b'

# Firewall
sudo ufw status numbered

# HTTPS reachable
curl -I https://llm.rdi.services

# Certificate details as seen externally
echo | openssl s_client -connect llm.rdi.services:443 -servername llm.rdi.services 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

---

## Recovery notes

If DNS-01 renewal fails later:

```bash
sudo journalctl -u certbot.service --since "24 hours ago"
sudo tail -n 200 /var/log/letsencrypt/letsencrypt.log
```

Check:

- `/etc/letsencrypt/secrets/digitalocean.ini` still exists, still `600`, still `root:root`.
- The DigitalOcean token is still valid and has DNS permissions.
- `rdi.services` is still hosted on DigitalOcean DNS (`dig NS rdi.services +short`).
- The renewal config still lists `authenticator = dns-digitalocean`.

If the proxy itself misbehaves:

```bash
sudo systemctl status rtu-proxy --no-pager
sudo journalctl -u rtu-proxy -n 200 --no-pager
```

Restart if needed:

```bash
sudo systemctl restart rtu-proxy
```

### Known issues seen during setup

**`ModuleNotFoundError: No module named 'prisma'` on an auth failure.** LiteLLM's error handler
imports `prisma` (used for DB-backed key storage) even when no database is configured, so an
auth failure crashes with this confusing secondary error instead of a clean 401. Fix:

```bash
source ~/rtu-proxy/venv/bin/activate
pip install prisma
sudo systemctl restart rtu-proxy
```

**`Malformed API Key passed in. Ensure Key has 'Bearer ' prefix.`** This usually doesn't mean
the key is wrong — it means `$PROXY_MASTER_KEY` was empty in the shell you ran `curl` from
(systemd's `EnvironmentFile=` only feeds the service, not your login shell). Before testing with
curl, either load it into that shell:

```bash
set -a; source ~/rtu-proxy/.env; set +a
echo $PROXY_MASTER_KEY   # confirm it's not blank
```

or just paste the literal key directly into the `-H "Authorization: Bearer ..."` header.

**`rtu-proxy.service` fails with `Result: resources` and an empty journal.** This means systemd
couldn't even find the executable — almost always caused by a leftover `youruser` placeholder in
`WorkingDirectory`, `EnvironmentFile`, or `ExecStart` in the unit file (see step 9). Check with:

```bash
sudo systemctl cat rtu-proxy | grep youruser
```

If anything prints, fix that line, then `sudo systemctl daemon-reload && sudo systemctl restart rtu-proxy`.
