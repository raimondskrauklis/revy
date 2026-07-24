# Deploy User Migration — Root → `deploy`

## Why

CI/CD was configured to SSH into the droplet as `root` using key `github_actions_key`. Login failed with:

```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

Root cause: `/etc/ssh/sshd_config` has `PermitRootLogin no`, which blocks **all** root logins over SSH — key-based or otherwise. This is a correct security setting and should **not** be reverted. Instead, a dedicated non-root `deploy` user was created for CI/CD to use.

---

## What was done on the droplet

1. **Created `deploy` user, added to `docker` group** (so it can run `docker` commands without `sudo`):
   ```bash
   adduser --disabled-password --gecos "" deploy
   usermod -aG docker deploy
   ```

2. **Set up `deploy`'s SSH directory:**
   ```bash
   mkdir -p /home/deploy/.ssh
   chmod 700 /home/deploy/.ssh
   touch /home/deploy/.ssh/authorized_keys
   chmod 600 /home/deploy/.ssh/authorized_keys
   chown -R deploy:deploy /home/deploy/.ssh
   ```

3. **Fixed ownership of directories the deploy workflow writes to:**
   ```bash
   mkdir -p /mnt/revy/backend
   chown deploy:deploy /mnt/revy
   chown deploy:deploy /mnt/revy/backend

   # redis-data must stay owned by uid 999 (the redis container's internal user)
   chown -R 999:999 /mnt/revy/redis-data
   chmod -R 750 /mnt/revy/redis-data
   ```
   Note: `999:999` will display as `dnsmasq:systemd-journal` in `ls -la` on this droplet — that's just how those numeric IDs resolve in `/etc/passwd`/`/etc/group` here. The important thing is the *numeric* UID/GID match what the Redis container expects.

4. **Generated a new SSH keypair as the `deploy` user** (not as root, and not landing in `/root/.ssh`):
   ```bash
   su - deploy
   ssh-keygen -t ed25519 -f ~/.ssh/revy_deploy_key -N "" -C "github-actions-deploy"
   cat ~/.ssh/revy_deploy_key.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

5. **Private key handling:**
   - The private key (`~/.ssh/revy_deploy_key`, no passphrase) content was copied into the GitHub Actions secret `SSH_PRIVATE_KEY`, replacing the old root key.
   - The private key file was deleted from the droplet after being saved as the GitHub secret — the server only needs the public half in `authorized_keys`.
   - The old root key (`github_actions_key` in `/root/.ssh/`) should also be considered compromised (it was pasted in a chat) and can be removed from `authorized_keys` / deleted, since root login is disabled anyway.

6. **Verification before touching CI:**
   ```bash
   ssh -i ~/.ssh/revy_deploy_key deploy@<DROPLET_IP>
   ```
   Confirms key auth works, and confirms `deploy` has an active shell with `docker` group membership (group membership only takes effect on a fresh login — not on the pre-existing root shell used for setup).

---

## Required changes to `deploy.yml`

### 1. Change SSH username from `root` to `deploy`

Every `appleboy/ssh-action@v1.0.3` step currently has:
```yaml
username: root
```
Change all five occurrences (lines ~293, ~343, ~367, ~397, ~427 in the original file) to:
```yaml
username: deploy
```

Affected steps:
- `Ensure Redis is running with health check`
- `Run database migrations on droplet`
- `Deploy backend container`
- `Deploy frontend container`
- `Deploy Celery workers`
- `Deployment summary`

### 2. Remove the `chown`/`chmod` lines in the Redis step

In the **"Ensure Redis is running with health check"** step, remove:
```yaml
mkdir -p /mnt/revy/redis-data
chown -R 999:999 /mnt/revy/redis-data
chmod -R 750 /mnt/revy/redis-data
```
`deploy` cannot `chown` files to a different UID (999) — that's a root-only operation regardless of file permissions, so this will fail (or silently no-op with an error) once the workflow runs as `deploy`. Ownership was already fixed permanently in the manual setup above, so these lines are no longer needed. It's fine to keep the `mkdir -p /mnt/revy/redis-data` line (or drop it too, since the directory already exists) — just be sure to remove the two `chown`/`chmod` lines.

### 3. Confirm `deploy` can access everything the scripts touch

The workflow scripts reference:
- `/mnt/revy/backend/.env` (via `ENV_FILE_PATH`) — must be readable by `deploy`
- `/mnt/revy/redis-data` — owned by uid 999, `deploy` doesn't need direct access to it, only Docker (running under root's daemon socket, which `deploy` can talk to via the `docker` group) does
- Docker socket (`/var/run/docker.sock`) — accessible because `deploy` is in the `docker` group

If `.env` at `/mnt/revy/backend/.env` doesn't already exist or isn't readable by `deploy`, create/adjust it:
```bash
chown deploy:deploy /mnt/revy/backend/.env
chmod 640 /mnt/revy/backend/.env
```

### 4. GitHub Actions secrets

No secret **names** need to change — `DROPLET_IP` and `SSH_PRIVATE_KEY` stay the same. Only the **value** of `SSH_PRIVATE_KEY` changes, to the new `deploy` user's private key.

---

## Rollout checklist

- [ ] Confirm `ssh -i revy_deploy_key deploy@<DROPLET_IP>` works manually
- [ ] Confirm `deploy` can run `docker ps` without `sudo` in that session
- [ ] Update `SSH_PRIVATE_KEY` GitHub secret with the new key
- [ ] Edit `deploy.yml`: `username: root` → `username: deploy` (5 places)
- [ ] Edit `deploy.yml`: remove `chown -R 999:999` / `chmod -R 750` lines from Redis step
- [ ] Confirm `/mnt/revy/backend/.env` is readable by `deploy`
- [ ] Delete private key file from the droplet (if still present)
- [ ] Optionally remove old root key from `/root/.ssh/authorized_keys` (root login is already disabled, but the key itself was exposed and should not remain trusted anywhere)
- [ ] Push change, watch the `deploy-production` job run end to end
