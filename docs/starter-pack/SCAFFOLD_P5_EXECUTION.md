# docs/starter-pack/SCAFFOLD_P5_EXECUTION.md

# P5 — Agent & cursor identity (execution)

Phase **P5** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md) § Locked exclusions.

**Status:** **Done** (2026-07-25) — agent/cursor alignment. Deploy workflow already Revy-branded; no separate `ci.yml`.

**Goal:** Agents and contributor docs match **Revy**, not KP Analytics.

**Authority:** `internal-docs/starter-pack/AGENTS.md`, `internal-docs/product/revy/README.md`.

## Decisions (rescoped from original P5)

- **Deploy / CI** — `.github/workflows/deploy.yml` is already `CI/CD - Revy`; **no** new `ci.yml`. Flip `SKIP_CI_TESTS` when secrets are ready (deploy program, not P5).
- **Cursor** — modular `.cursor/rules/` from starter-pack (`--app-*`, not `--tp-*`); remove KP deep-investigation / corpus skills.
- **Root entry** — `AGENTS.md` + slim `.cursorrules` pointer + minimal `README.md`.

## Out of scope

- Full droplet / DOCR pipeline redesign
- Keycloak realm automation
- Enabling CI tests (separate ops when secrets exist)

---

## P5.1 — Root AGENTS.md ✅

**Deliverable:** [AGENTS.md](../../AGENTS.md) — Revy context, `docs/starter-pack/`, `internal-docs/` map, skills index.

## P5.2 — Cursor rules & skills ✅

**Deliverable:**

- [`.cursorrules`](../../.cursorrules) — pointer only
- [`.cursor/rules/`](../../.cursor/rules/) — `00-core`, `backend-python`, `frontend-react`, `app-color-tokens`, `app-i18n`, `testing`, `sentry-mcp`
- Removed KP rules: `color-tokens` (`--tp-*`), `deep-investigation-*`, `scope-calculator-pattern`
- Removed KP corpus skills (`author-*-corpus`, `corpus-program`)

## P5.3 — README ✅

**Deliverable:** [README.md](../../README.md) — quick start → `DEV_BOOTSTRAP.md`, link `AGENTS.md`.

## P5.4 — Doc sync ✅

| Doc | Change |
|-----|--------|
| `SCAFFOLD_FINDINGS.md` | Locked exclusions updated |
| `README.md` (this folder) | P5 Done |
| `SCAFFOLD_GENERAL_PLAN.md` | P5 scope note |

---

**Phase gate** (sanity):

```bash
# backend/
pipenv run lint && pipenv run pytest tests/unit/ -q

# frontend/
npm run lint && npm test -- --run && npm run build
```

**Next:** none (final scaffold phase).
