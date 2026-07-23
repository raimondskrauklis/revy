# docs/starter-pack/SCAFFOLD_P5_EXECUTION.md

# P5 — Repo identity & automation (execution)

Phase **P5** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md) § Locked exclusions. **P5 only.**

**Status:** **Deferred** — do **not** execute until product owner explicitly invokes Phase 5.

**Goal:** Agents and CI match Revy, not KP.

**Authority:** `internal-docs/starter-pack/AGENTS.md`, `internal-docs/product/revy/README.md`.

## Decisions locked for P5

- **New** `.github/workflows/ci.yml` — lint + test + build; do **not** enable tests in KP `deploy.yml`. `backend/scripts/seed_test_data.py` is a Revy **no-op stub** — do not grow KP seed entities; new `ci.yml` must not depend on it (unit tests use mocks).
- Root `AGENTS.md` = starter-pack content + Revy pointer to `docs/starter-pack/` and `internal-docs/product/revy/`.
- Slim `.cursorrules` to pointer + link modular rules; do not import KP domain entities.
- Wire `internal-docs/` mention in agent docs (contributors with access).
- `SKIP_CI_TESTS` in legacy `deploy.yml` stays until separate deploy program retires that workflow.

## Out of scope for P5

- Full production droplet deploy / DOCR pipeline redesign
- Keycloak realm automation
- Revy review pipeline features

---

## P5.1 — Root AGENTS.md

**What:** Add `AGENTS.md` at repo root; Revy-specific section: stack, `docs/starter-pack/`, env canon, locked exclusions summary.

**Files:** `AGENTS.md`

**Deliverable:** File exists; links to `docs/starter-pack/README.md`.

## P5.2 — Replace KP .cursorrules + audit rules

**What:** Short `.cursorrules` pointing to `AGENTS.md` and `docs/starter-pack/`. **Audit** `.cursor/rules/` — remove or replace **KP-only** rules that mislead Revy work (`deep-investigation-*`, `color-tokens.mdc` with `--tp-*`, `scope-calculator-pattern.mdc`). **Keep** `sentry-mcp.mdc` (active workspace policy). Prefer AGENTS.md over a duplicate `revy.mdc` unless a glob-scoped rule is needed (e.g. `frontend/` + `--app-*` tokens).

**Files:** `.cursorrules`, `.cursor/rules/` (delete/replace KP files as needed)

**Deliverable:** `.cursorrules` no longer references KP entities or `--tp-*`; `rg --tp- .cursor/rules/` — no misleading token rules (or files removed).

## P5.3 — Revy CI workflow

**What:** `ci.yml` on PR: backend `pipenv run lint` + `pytest tests/unit/`; frontend `npm run lint` + `npm test` + `npm run build`; uses `TEST_DATABASE_URL` secret only if integration tests added later.

**Files:** `.github/workflows/ci.yml`

**Deliverable:** Workflow file valid YAML; no reference to `seed_test_data.py`.

## P5.4 — README contributor entry

**What:** Minimal root `README.md` — what Revy is, quick start link to `DEV_BOOTSTRAP.md`, not KP platform.

**Files:** `README.md`

**Deliverable:** README links `docs/starter-pack/DEV_BOOTSTRAP.md`.

## P5.5 — Doc sync

**What:** Update findings locked exclusions; README execution table P5 Done.

| Doc | Change |
|-----|--------|
| `docs/starter-pack/SCAFFOLD_FINDINGS.md` | Mark exclusions resolved |
| `docs/starter-pack/README.md` | P5 status |

**Deliverable:** README P5 row Done + sha.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/ -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run && npm run build
```

**Human gate:** Open test PR and confirm `ci.yml` checks pass on GitHub.

**Deploy:** CI only — no droplet change.

**Next:** **none** (final phase).
