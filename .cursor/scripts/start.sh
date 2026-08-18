#!/usr/bin/env bash
# .cursor/scripts/start.sh
# Per-boot service reconciliation: start PostgreSQL + Redis, ensure the app role/db/
# extensions exist, and apply Alembic migrations. Idempotent; returns after services
# are ready. Long-running app processes (API, web) run as terminals (see environment.json).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

PG_MAJOR=16
DB_ROLE="revy_app"
DB_PASSWORD="revy_local_pw"

echo "==> [start] PostgreSQL"
sudo pg_ctlcluster "${PG_MAJOR}" main start 2>/dev/null || true
for _ in $(seq 1 30); do
  sudo -u postgres psql -tAc "SELECT 1" >/dev/null 2>&1 && break
  sleep 1
done

echo "==> [start] Redis"
if ! redis-cli ping >/dev/null 2>&1; then
  sudo redis-server /etc/redis/redis.conf --daemonize yes
fi

echo "==> [start] ensure role / databases / extensions"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_ROLE}') THEN
    CREATE ROLE ${DB_ROLE} LOGIN PASSWORD '${DB_PASSWORD}' SUPERUSER;
  END IF;
END \$\$;
SQL
for db in revy revy_test; do
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1 \
    || sudo -u postgres createdb -O "${DB_ROLE}" "${db}"
  sudo -u postgres psql -d "${db}" -v ON_ERROR_STOP=1 \
    -f "${REPO_ROOT}/deploy/sql/postgres-extensions.sql" >/dev/null
done

echo "==> [start] Alembic migrations"
cd "${REPO_ROOT}/backend"
pipenv run alembic upgrade head

echo "==> [start] services ready (Postgres 5432, Redis 6379)"
