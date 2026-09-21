#!/usr/bin/env bash
# infra/keycloak/scripts/apply_theme.sh
# Apply revy theme to production revy-kc container.
# Run on the droplet: bash /mnt/revy_volume/keycloak-themes/scripts/apply_theme.sh
# Requires: docker access (user in docker group).

set -euo pipefail

CONTAINER="revy-kc"
THEME_SRC="/mnt/revy_volume/keycloak-themes"
THEME_DST="/opt/keycloak/themes/revy"
CACHE_DIR="/opt/keycloak/data/tmp/kc-gzip-cache"
TS=$(date +%s)

echo "=== Revy Keycloak theme apply ==="
echo "Timestamp: $TS"

# 1. Backup prior theme copy if it exists
if docker exec "$CONTAINER" test -d "$THEME_DST" 2>/dev/null; then
  BACKUP_DIR="$THEME_SRC/.prev-$TS"
  echo "Backing up current theme to $BACKUP_DIR ..."
  mkdir -p "$BACKUP_DIR"
  docker cp "$CONTAINER:$THEME_DST" "$BACKUP_DIR/"
  echo "Backup complete."
else
  echo "No prior theme copy — skipping backup."
fi

# 2. Copy theme into container
echo "Copying theme to $CONTAINER:$THEME_DST ..."
docker cp "$THEME_SRC/revy" "$CONTAINER:$THEME_DST"
echo "Copy complete."

# 3. Delete gzip cache
echo "Deleting gzip cache ..."
docker exec "$CONTAINER" rm -rf "$CACHE_DIR"
echo "Cache deleted."

# 4. Restart
echo "Restarting $CONTAINER ..."
docker restart "$CONTAINER"

# 5. Wait for health
echo "Waiting for Keycloak health ..."
for i in $(seq 1 20); do
  if curl -sf http://127.0.0.1:8080/health/ready 2>/dev/null; then
    echo "Keycloak healthy!"
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo "ERROR: Keycloak did not become healthy after 60s" >&2
    exit 1
  fi
  sleep 3
done

# 6. Done
echo ""
echo "=== Apply complete ==="
echo "Next: Admin UI -> realm revy -> loginTheme = revy"
echo "Backup: $BACKUP_DIR (if prior copy existed)"
