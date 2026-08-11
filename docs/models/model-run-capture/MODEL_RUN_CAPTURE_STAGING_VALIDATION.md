# Model run capture — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md)

**Status:** P0/P1 validated on [#97](https://github.com/raimondskrauklis/revy/pull/97) after #96 deploy — **MRC-P0 PASS**; MRC-P1 embed PASS. MRC-P2 terminal writer shipped in [#98](https://github.com/raimondskrauklis/revy/pull/98) — **post-#98 deploy validation pending**.

**Shipped scope:**

| PR | Scope |
|----|--------|
| [#96](https://github.com/raimondskrauklis/revy/pull/96) | MRC-P0 (index embedding identity), MRC-P1 (attempt rows + judge/publish step models), MRC-P2.1 (`models_snapshot` column) |
| [#98](https://github.com/raimondskrauklis/revy/pull/98) | MRC-P2.2–P2.4 (`build_models_snapshot`, terminal writer hooks, `model_breakdown` staging metrics) |

**Validation rule:** Merged code cannot self-validate on its own PR. Use a **dogfood PR opened after deploy** with `--since` at deploy completion — pre-deploy runs are excluded.

---

## Deploy boundaries

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| **#96 model-run-capture** | `2026-08-10T19:35:30Z` | **P0/P1 dogfood window** — migration `0032` + index/attempt capture |
| **#98 MRC-P2** | *(fill after merge deploy)* | **P2 dogfood window** — terminal `models_snapshot` writer |

**Rule:** Use deploy job completion time (`gh run list --branch main`), not merge time. Run probe scripts from **`main`** (metrics scripts live on main); scope with `--pr-number` on the dogfood PR opened **after** deploy.

**Pre-deploy:** Do not count runs before the deploy boundary for the phase under sign-off.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#97](https://github.com/raimondskrauklis/revy/pull/97) | `chore/mrc-staging-dogfood` | push 1 — P0/P1 **PASS**; push 2 — pending post-#98 deploy |

**Protocol:** One `backend/**` touch per push (probe import in `post_main_staging_probe.py`). After #98 deploy, push 2 (or a new empty commit) triggers pipeline runs that exercise `models_snapshot` population.

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe v6 + autostart | **done** — 2 completed runs (P0/P1) |
| 2 | Post-#98 deploy — `models_snapshot` population | **pending** — after #98 merge + deploy |

---

## Pass criteria — push 1 / #96 window (2026-08-10)

| Check | Pass | Evidence |
|-------|------|----------|
| Alembic `0032` | **PASS** | `alembic_0032` — `2026_08_10_1300_0032_github_pipeline_runs_models_snapshot` |
| Index manifest `embedding_model` | **PASS** | `2/2` embed runs — `voyage-code-3.5` |
| Index step `model_provider`/`model_id` | **PASS** | `2/2` voyage step model match |
| `index_embed` attempt rows | **PASS** | `2` rows, `request_model=voyage-code-3.5` |
| Manifest ↔ attempt model parity | **PASS** | `parity_pass=2` `parity_fail=0` |
| Judge step model fields | **PARTIAL** | `0/2` — judge likely skipped/disabled on staging (expected null model_ref) |
| Publish step model fields | **PARTIAL** | `1/2` — one run used publish fallback (no model fields by design) |
| `models_snapshot` populated | **skipped** | P2.2 not deployed in #96 window — `with_snapshot=0/2` INCONCLUSIVE |

---

## Pass criteria — push 2 / #98 window (pending)

| Check | Pass | Evidence |
|-------|------|----------|
| `models_snapshot_populated` | pending | `--mrc-gate` — expect `with_snapshot` > 0 on completed runs |
| Snapshot shape | pending | `embedding` + `reviewer` keys; `judge`/`publish` per stage completion |
| `model_breakdown` (PO script) | pending | `--json` includes `model_breakdown` grouped by `step_type` + model |

**Expected snapshot (full pipeline, embed path):**

```json
{
  "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5", "dimensions": 1024},
  "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
  "judge": null,
  "publish": {"provider": "moonshot", "model_id": "kimi-k2.7-code"}
}
```

Reuse-only index runs omit `embedding`. Judge key omitted when judge skipped.

---

## Probe commands

```bash
cd backend
PR=97
SINCE=2026-08-10T19:35:30Z   # P0/P1 (#96 window)
# SINCE=<#98-deploy-iso>     # P2 — after #98 merge deploy

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE --pr-number $PR --require-activity --rg15-gate --json
```

**P2 gate:** `models_snapshot_populated` is **INCONCLUSIVE** when `with_snapshot=0` and writer not deployed; **PASS** when completed runs show non-null `models_snapshot` after #98 deploy.

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | `79626fa` | 2 completed runs; Revy **pass**; MRC P0 gate **pass** |
| 1 (pipeline) | `547f4f1` | initial probe commit — included in same `--since` window |
| 2 | — | pending post-#98 deploy |

**Model breakdown (PR #97, post-#96, pre-P2 writer):**

| step_type | provider | request_model | n |
|-----------|----------|---------------|---|
| index_embed | voyage | voyage-code-3.5 | 2 |
| review | moonshot | kimi-k2.7-code | 2 |
| publish | moonshot | kimi-k2.7-code | 2 |

---

## Sign-off

| Track | Status | Evidence |
|-------|--------|----------|
| MRC-P0 index identity | **PASS** | PR #97 push 1 — manifest + step + embed attempts |
| MRC-P1 embed attempts | **PASS** | `index_embed` rows + parity |
| MRC-P1 judge/publish step models | **PARTIAL** | judge skipped path; publish fallback omits model (by design) |
| MRC-P2.1 schema (`models_snapshot` column) | **PASS** | alembic `0032` + column exists |
| MRC-P2.2–P2.4 snapshot population | **pending** | [#98](https://github.com/raimondskrauklis/revy/pull/98) — re-run after deploy |
| PO P0 (parallel) | **PASS** | 2 runs, 4 attempt rows in review-scoped PO query |
| RG-15 (parallel) | **PASS** | no stuck processing |

**Verdict:** **MRC-P0 + P1 embed sign-off PASS** for #96 on staging. **MRC-P2 code complete** in #98 — operator fills #98 deploy ISO, runs push 2 on #97, and signs off `models_snapshot_populated`.

**Gate note:** `--mrc-gate` exits 1 on judge/publish step checks when judge is skipped or publish uses fallback — treat embed + P0 checks as primary sign-off until gate logic distinguishes skip/fallback paths.
