# Certbot Renewal with DigitalOcean DNS-01

## Purpose

Configure automatic Let's Encrypt certificate renewal for:

- `revy.createit.digital`
- `auth.revy.createit.digital`

without requiring inbound TCP port `80`.

The server uses:

- DigitalOcean Droplet
- DigitalOcean DNS
- Nginx
- Certbot installed through APT
- `certbot-dns-digitalocean`
- Let's Encrypt DNS-01 validation

---

## Final result

The migration was completed successfully.

The existing certificate:

```text
Certificate Name: revy.createit.digital
Domains: revy.createit.digital auth.revy.createit.digital
Key Type: ECDSA
Certificate Path: /etc/letsencrypt/live/revy.createit.digital/fullchain.pem
Private Key Path: /etc/letsencrypt/live/revy.createit.digital/privkey.pem
Expiry Date: 2026-10-22 11:31:01+00:00
```

was reconfigured to use the DigitalOcean DNS plugin.

The final Certbot dry-run returned:

```text
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/revy.createit.digital/fullchain.pem (success)
```

This confirms that Certbot can renew the certificate using DNS-01 without accessing port `80`.

---

## Why DNS-01 was selected

The default Certbot Nginx, standalone, and webroot authenticators use the HTTP-01 challenge.

HTTP-01 requires Let's Encrypt to connect to:

```text
http://<domain>/.well-known/acme-challenge/...
```

over public TCP port `80`.

The DigitalOcean DNS plugin instead creates a temporary TXT record similar to:

```text
_acme-challenge.revy.createit.digital
```

After Let's Encrypt validates the TXT record, the plugin removes it.

Therefore:

- Port `80` is not needed for certificate renewal.
- Port `443` remains available for HTTPS traffic.
- Wildcard certificates would also be possible later, if required.

---

## 1. Identify the Certbot installation type

The installed Certbot executable was checked:

```bash
command -v certbot
```

Result:

```text
/usr/bin/certbot
```

The version was checked:

```bash
certbot --version
```

Result:

```text
certbot 2.9.0
```

Because Certbot was located at `/usr/bin/certbot`, it was installed through the operating system package manager rather than Snap.

This distinction is important because Certbot plugins must be installed for the same Certbot installation.

A Snap plugin cannot be loaded by an APT-installed Certbot.

---

## 2. Install the matching DigitalOcean plugin

The APT-compatible DigitalOcean plugin was installed:

```bash
sudo apt update
sudo apt install python3-certbot-dns-digitalocean
```

The installed plugins were then checked:

```bash
sudo certbot plugins
```

The required plugin appeared:

```text
* dns-digitalocean
Description: Obtain certificates using a DNS TXT record
Interfaces: Authenticator, Plugin
```

This confirmed that the active `/usr/bin/certbot` installation could load the plugin.

An unused Snap installation of the plugin may be removed if desired:

```bash
sudo snap remove certbot-dns-digitalocean
```

This is optional and does not affect the APT Certbot installation.

---

## 3. Create a DigitalOcean API token

A DigitalOcean API token is required so Certbot can:

1. Read the DNS zone.
2. Create the temporary ACME TXT record.
3. Delete the TXT record after validation.

The token should have only the required domain/DNS permissions rather than unrestricted account access.

The DNS zone for `createit.digital` must be hosted on DigitalOcean DNS.

This can be checked with:

```bash
dig NS createit.digital +short
```

Expected authoritative nameservers:

```text
ns1.digitalocean.com.
ns2.digitalocean.com.
ns3.digitalocean.com.
```

The domain registrar itself may be elsewhere, but the authoritative nameservers must point to DigitalOcean for this plugin to manage the challenge records.

---

## 4. Store the DigitalOcean token securely

A protected secrets directory was created:

```bash
sudo install -d -m 700 /etc/letsencrypt/secrets
```

The credentials file was created:

```bash
sudo nano /etc/letsencrypt/secrets/digitalocean.ini
```

File contents:

```ini
dns_digitalocean_token = YOUR_DIGITALOCEAN_API_TOKEN
```

The file ownership and permissions were restricted:

```bash
sudo chown root:root /etc/letsencrypt/secrets/digitalocean.ini
sudo chmod 600 /etc/letsencrypt/secrets/digitalocean.ini
```

Verification:

```bash
sudo stat /etc/letsencrypt/secrets/digitalocean.ini
```

The credentials file must not be committed to Git, copied into application containers, or exposed in logs.

---

## 5. Inspect the existing certificate

Existing certificates were listed:

```bash
sudo certbot certificates
```

Result:

```text
Certificate Name: revy.createit.digital
Serial Number: 5fedeafd2a45ebd7ce3963ef76a4fd0b2a7
Key Type: ECDSA
Domains: revy.createit.digital auth.revy.createit.digital
Expiry Date: 2026-10-22 11:31:01+00:00
Certificate Path: /etc/letsencrypt/live/revy.createit.digital/fullchain.pem
Private Key Path: /etc/letsencrypt/live/revy.createit.digital/privkey.pem
```

Both required hostnames were already included in one certificate.

This means both Nginx virtual hosts can use:

```nginx
ssl_certificate /etc/letsencrypt/live/revy.createit.digital/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/revy.createit.digital/privkey.pem;
```

---

## 6. Reconfigure the existing certificate

The existing certificate renewal configuration was changed from HTTP/Nginx validation to DigitalOcean DNS validation:

```bash
sudo certbot reconfigure \
  --cert-name revy.createit.digital \
  --dns-digitalocean \
  --dns-digitalocean-credentials /etc/letsencrypt/secrets/digitalocean.ini \
  --dns-digitalocean-propagation-seconds 30
```

Certbot output:

```text
Simulating renewal of an existing certificate for revy.createit.digital and auth.revy.createit.digital
Waiting 30 seconds for DNS changes to propagate

Successfully updated configuration.
Changes will apply when the certificate renews.
```

This command tested the DNS-01 configuration before saving it.

The certificate itself was not unnecessarily replaced because it was still valid. Certbot updated the renewal configuration that will be used during the next real renewal.

---

## 7. Verify the saved renewal configuration

The relevant renewal settings can be inspected with:

```bash
sudo grep -E \
  '^(authenticator|installer|dns_digitalocean)' \
  /etc/letsencrypt/renewal/revy.createit.digital.conf
```

Expected entries include:

```ini
authenticator = dns-digitalocean
dns_digitalocean_credentials = /etc/letsencrypt/secrets/digitalocean.ini
dns_digitalocean_propagation_seconds = 30
```

Do not manually edit the renewal configuration unless necessary. Prefer `certbot reconfigure` so Certbot validates and writes the settings itself.

---

## 8. Test automatic renewal

A simulated renewal was run:

```bash
sudo certbot renew \
  --cert-name revy.createit.digital \
  --dry-run
```

Result:

```text
Processing /etc/letsencrypt/renewal/revy.createit.digital.conf

Simulating renewal of an existing certificate for revy.createit.digital and auth.revy.createit.digital
Waiting 30 seconds for DNS changes to propagate

Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/revy.createit.digital/fullchain.pem (success)
```

This is the key success condition.

It confirms:

- The API token is valid.
- The credentials file is readable by Certbot.
- DigitalOcean DNS can be updated.
- Both domain names can be validated.
- The saved certificate renewal configuration works.
- Public inbound port `80` is no longer required for renewal.

---

## 9. Ensure Nginx reloads after a real renewal

After Certbot renews a certificate, Nginx must reload before it starts serving the new certificate files.

Create a deployment hook:

```bash
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh >/dev/null <<'EOF'
#!/bin/sh
systemctl reload nginx
EOF
```

Make it executable:

```bash
sudo chmod 755 /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

Test the renewal and deployment hook together:

```bash
sudo certbot renew \
  --cert-name revy.createit.digital \
  --dry-run \
  --run-deploy-hooks
```

Check Nginx afterward:

```bash
sudo systemctl status nginx --no-pager
```

---

## 10. Verify the Certbot timer

Check the automatic renewal schedule:

```bash
systemctl list-timers --all | grep -i certbot
```

For an APT-installed Certbot, the timer is normally:

```text
certbot.timer
```

Inspect it:

```bash
sudo systemctl status certbot.timer --no-pager
```

Enable it if it is not already enabled:

```bash
sudo systemctl enable --now certbot.timer
```

Confirm the next scheduled run:

```bash
systemctl list-timers certbot.timer
```

Certbot normally checks certificates regularly and renews them only when they are sufficiently close to expiration.

---

## 11. Allow HTTPS in UFW

Before removing HTTP access, allow HTTPS:

```bash
sudo ufw allow 'Nginx HTTPS'
```

Alternatively:

```bash
sudo ufw allow 443/tcp
```

Check the firewall:

```bash
sudo ufw status numbered
```

The expected final inbound rules are approximately:

```text
OpenSSH                    ALLOW IN    Anywhere
Nginx HTTPS                ALLOW IN    Anywhere
OpenSSH (v6)               ALLOW IN    Anywhere (v6)
Nginx HTTPS (v6)           ALLOW IN    Anywhere (v6)
```

For stronger security, the SSH rule should later be restricted to trusted administration IP addresses where practical.

---

## 12. Remove port 80 from UFW

Because the DNS renewal dry-run succeeded, port `80` can now be removed from UFW.

Current rules included:

```text
Nginx HTTP                 ALLOW IN    Anywhere
Nginx HTTP (v6)            ALLOW IN    Anywhere (v6)
```

Remove the Nginx HTTP profile:

```bash
sudo ufw delete allow 'Nginx HTTP'
```

Check the result:

```bash
sudo ufw status numbered
```

If the profile-based command does not match the existing rule, remove rules by their displayed numbers:

```bash
sudo ufw delete <RULE_NUMBER>
```

When deleting by rule number, run `sudo ufw status numbered` again after each deletion because rule numbers are recalculated.

---

## 13. Remove port 80 from the DigitalOcean Cloud Firewall

UFW and the DigitalOcean Cloud Firewall are separate firewall layers.

In the DigitalOcean control panel, inspect the firewall attached to the Droplet and remove the inbound rule:

```text
TCP 80
```

Keep at minimum:

```text
TCP 443   HTTPS
TCP 22    SSH
```

Prefer restricting TCP `22` to trusted source IP addresses rather than allowing it globally.

Port `443` must be allowed in both:

- DigitalOcean Cloud Firewall
- UFW on the Droplet

---

## 14. Remove HTTP listeners from Nginx

After DNS renewal has been verified and port `443` is allowed, the HTTP server blocks can be removed.

Delete complete blocks containing:

```nginx
listen 80;
listen [::]:80;
```

A temporary HTTPS-only configuration can look like this:

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name auth.revy.createit.digital;

    ssl_certificate /etc/letsencrypt/live/revy.createit.digital/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/revy.createit.digital/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Temporary until the Keycloak reverse proxy is configured.
    return 404;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name revy.createit.digital;

    ssl_certificate /etc/letsencrypt/live/revy.createit.digital/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/revy.createit.digital/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Temporary until the Revy application is configured.
    return 404;
}
```

Test before reloading:

```bash
sudo nginx -t
```

Apply the configuration:

```bash
sudo systemctl reload nginx
```

Confirm active listeners:

```bash
sudo ss -lntp | grep -E ':(80|443)\b'
```

Expected result:

- Nginx listens on TCP `443`.
- Nothing listens publicly on TCP `80`.

---

## Important Nginx correction

The original `auth.revy.createit.digital` HTTPS block contained:

```nginx
return 301 https://$host$request_uri;
```

inside the port `443` server.

That redirects an HTTPS request back to the exact same HTTPS URL and creates an infinite redirect loop.

For example:

```text
https://auth.revy.createit.digital/
→ https://auth.revy.createit.digital/
→ https://auth.revy.createit.digital/
```

Until the Keycloak proxy is configured, use:

```nginx
return 404;
```

Later this block should be replaced by the actual Keycloak `proxy_pass` configuration.

An HTTP-to-HTTPS redirect belongs only in a port `80` server block. If port `80` is intentionally closed, no HTTP redirect block is needed.

---

## Behaviour after closing port 80

After port `80` is removed:

```text
http://revy.createit.digital
```

will not redirect to HTTPS. The connection will time out or be rejected.

Users must access:

```text
https://revy.createit.digital
```

and:

```text
https://auth.revy.createit.digital
```

This does not affect certificate renewal because validation now uses DigitalOcean DNS.

Browsers that automatically upgrade to HTTPS may still appear to work normally, but plain HTTP connectivity itself is intentionally unavailable.

---

## Final verification checklist

Run:

```bash
sudo certbot certificates
```

Confirm both names are present:

```text
revy.createit.digital
auth.revy.createit.digital
```

Check the renewal authenticator:

```bash
sudo grep -E \
  '^(authenticator|dns_digitalocean)' \
  /etc/letsencrypt/renewal/revy.createit.digital.conf
```

Run the renewal test:

```bash
sudo certbot renew \
  --cert-name revy.createit.digital \
  --dry-run
```

Test Nginx:

```bash
sudo nginx -t
```

Check services:

```bash
sudo systemctl is-active nginx
sudo systemctl is-active certbot.timer
```

Check listening ports:

```bash
sudo ss -lntp | grep -E ':(80|443)\b'
```

Check UFW:

```bash
sudo ufw status numbered
```

Test HTTPS locally:

```bash
curl -I https://revy.createit.digital
curl -I https://auth.revy.createit.digital
```

Inspect the certificate presented externally:

```bash
echo | openssl s_client \
  -connect revy.createit.digital:443 \
  -servername revy.createit.digital 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

---

## Current status

Completed:

- [x] APT Certbot installation identified.
- [x] DigitalOcean DNS plugin installed for the active Certbot installation.
- [x] Existing certificate contains both required hostnames.
- [x] DigitalOcean credentials configured.
- [x] Certificate renewal changed to DNS-01.
- [x] Certbot reconfiguration simulation succeeded.
- [x] Full renewal dry-run succeeded.

Remaining operational steps:

- [ ] Add/confirm inbound TCP `443` in UFW.
- [ ] Add/confirm inbound TCP `443` in the DigitalOcean Cloud Firewall.
- [ ] Add and test the Nginx deployment reload hook.
- [x] Replace certbot stub vhosts with full configs — `internal-docs/starter-pack/deploy/nginx/revy.createit.digital.conf`, `auth.revy.createit.digital.conf` (443 only).
- [ ] Remove legacy port `80` server blocks from `/etc/nginx/sites-enabled/` if still present.
- [ ] Remove inbound TCP `80` from UFW.
- [ ] Remove inbound TCP `80` from the DigitalOcean Cloud Firewall.
- [ ] Verify only TCP `443` remains publicly exposed for web traffic.
- [ ] Deploy Keycloak compose — `internal-docs/starter-pack/deploy/keycloak/docker-compose.production.example.yml`.

---

## Recovery notes

If DNS renewal later fails, inspect:

```bash
sudo journalctl -u certbot.service --since "24 hours ago"
sudo tail -n 200 /var/log/letsencrypt/letsencrypt.log
```

Check that:

- `/etc/letsencrypt/secrets/digitalocean.ini` still exists.
- Its permissions remain `600`.
- The DigitalOcean token is active.
- The token has sufficient DNS permissions.
- `createit.digital` is still hosted on DigitalOcean DNS.
- The Certbot plugin is still installed.
- The renewal configuration still uses `dns-digitalocean`.

Re-run:

```bash
sudo certbot renew \
  --cert-name revy.createit.digital \
  --dry-run
```

before making firewall changes if the DNS provider, API token, or Certbot installation is changed.
