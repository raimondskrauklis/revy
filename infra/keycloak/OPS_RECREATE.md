# infra/keycloak/OPS_RECREATE.md

# Revy Keycloak — ops recreate with baked theme

This doc covers two apply paths for the Revy login theme on production Keycloak.

## Path A: Docker Compose rebuild (preferred for next recreate)

When ops next runs a full Keycloak container recreate:

1. **Ensure theme files are on the volume:**
   ```bash
   rsync -az infra/keycloak/themes/revy/ infra/keycloak/scripts/ sec-vm:/mnt/revy_volume/keycloak-themes/
   ```

2. **Rebuild from `deploy/keycloak/config/`:**
   ```bash
   cd deploy/keycloak/config/
   docker compose build
   docker compose up -d
   ```

3. **If using the bind-mount path** (compose already has `/mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro`), the theme is picked up automatically — no `docker cp` needed.

4. **Set realm loginTheme** (already done — re-verify):
   ```bash
   docker exec revy-kc /opt/keycloak/bin/kcadm.sh get realms/revy --fields loginTheme
   ```

## Path B: docker cp apply (fallback, always works)

```bash
rsync -az infra/keycloak/themes/revy/ infra/keycloak/scripts/ sec-vm:/mnt/revy_volume/keycloak-themes/
bash /mnt/revy_volume/keycloak-themes/scripts/apply_theme.sh
```

## Rollback

If a recreate fails:

1. **Tag the previous image:**
   ```bash
   docker tag revy-keycloak:26.0 revy-keycloak:26.0-broken
   docker pull <previous-good-image>  # or restore from backup registry
   ```

2. **Run the restored version** via the same compose file.

3. **If the issue is theme-specific,** simply unset `loginTheme` on the realm:
   ```bash
   docker exec revy-kc /opt/keycloak/bin/kcadm.sh update realms/revy -s loginTheme=""
   ```
   This falls back to the default Keycloak legacy theme.