-- deploy/sql/postgres-extensions.sql
-- Run once per database via DO admin / doadmin (managed PostgreSQL 17).
-- Apply to `revy`, `revy_test`, and `keycloak` databases as needed.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
