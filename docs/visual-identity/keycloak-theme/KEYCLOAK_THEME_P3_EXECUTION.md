// docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_P3_EXECUTION.md

# P3 — Bake + docker-compose sync (execution)

Phase **P3** of [`KEYCLOAK_THEME_GENERAL_PLAN.md`](./KEYCLOAK_THEME_GENERAL_PLAN.md). Baseline: [`KEYCLOAK_THEME_FINDINGS.md`](./KEYCLOAK_THEME_FINDINGS.md) Q1–Q13. **P3 only — optional, deferred.**

**Goal:** The same theme is repeatable without tribal `docker cp`, and the deploy compose can bake it in.

## Decisions locked for P3
- Layers on `revy-keycloak:26.0` (built image with vymalo webhook JARs + `start --optimized`), not stock KC 26.
- Prerequisite: `docker compose build` in `deploy/keycloak/config/` must produce `revy-keycloak:26.0` first.
- Bind-mount: absolute `/mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro`.

## Out of scope for P3
- Executing a recreate on production. Compose update is a template for the next deploy cycle.
- Keycloak version upgrade.
- Admin/account/email/favicon themes.

---

## P3.1 — Create infra/keycloak/Dockerfile

**What:** `infra/keycloak/Dockerfile` — **separate file** from `deploy/keycloak/config/Dockerfile`. `FROM revy-keycloak:26.0` (built image with webhook JARs, `start --optimized`). `COPY themes/revy /opt/keycloak/themes/revy`. No `kc.sh build` — base image already ran it. No providers — already in base.

**Files:** New — `infra/keycloak/Dockerfile`

**Deliverable:** `docker inspect revy-keycloak:26.0 > /dev/null` (prerequisite image exists). `docker build -t revy-keycloak-themed:26.0 infra/keycloak/` succeeds; `docker run --rm revy-keycloak-themed:26.0 ls /opt/keycloak/themes/revy/login/theme.properties` returns the file.

---

## P3.2 — Update deploy compose for bind-mount

**What:** Update `deploy/keycloak/config/docker-compose.yml` — add `volumes:` entry: `/mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro` on the `keycloak` service. The volume line is **active** — it will take effect on the next `docker compose up -d` (whenever ops runs the recreate). Comment the bind-mount notes: "Revy custom theme, C6 ops-owned recreate path. Bundled themes live in JARs — mounting whole themes/ dir is safe." Do **not** `docker compose up -d` in this phase — only the file change.

**Files:** Edit — `deploy/keycloak/config/docker-compose.yml`

**Deliverable:** Compose file has the bind-mount volume active (not commented); `docker compose -f deploy/keycloak/config/docker-compose.yml config` validates. Volume does not need to exist on the validate host.

---

## P3.3 — Document ops recreate option

**What:** Create `infra/keycloak/OPS_RECREATE.md` documenting: (1) how to run `docker compose build` from `deploy/keycloak/config/` to pick up the theme; (2) the bind-mount path `/mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro`; (3) the rollback path if the recreate fails (docker tag previous image, `docker run` restored version); (4) note that `docker cp` apply still works as a fallback. **Files:** New — `infra/keycloak/OPS_RECREATE.md`.

**Files:** New — `infra/keycloak/OPS_RECREATE.md`

**Deliverable:** `infra/keycloak/OPS_RECREATE.md` exists with bind-mount path, build steps, rollback procedure, and `docker cp` fallback note.

---

## P3.4 — Doc sync (final subphase)

**What:** Update execution README status rows for P0–P3 (Done + shas). Grep siblings in `docs/visual-identity/keycloak-theme/`: confirm README, findings, general plan, all 4 execution files exist and are consistent. No changelog entry needed (no user-facing SPA change).

**Files:** Edit — `docs/visual-identity/keycloak-theme/README.md`

**Deliverable:** README table shows all phases Done with commit shas.

---

**Phase gate** (no pytest/Vitest — build validation):

```bash
docker compose -f deploy/keycloak/config/docker-compose.yml config > /dev/null
docker build -t revy-keycloak-themed:26.0 infra/keycloak/
docker run --rm revy-keycloak-themed:26.0 ls /opt/keycloak/themes/revy/login/theme.properties
```

**Deploy:** commit + final push. PR update: `feat(keycloak-theme): P3 — bake, compose sync, doc sync`.

**Next:** **none** — final phase. Program complete.
