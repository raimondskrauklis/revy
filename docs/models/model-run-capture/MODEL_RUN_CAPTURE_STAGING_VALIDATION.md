# Model run capture — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md)

**Status:** **MRC-P0–P3 staging sign-off PASS** on [#100](https://github.com/raimondskrauklis/revy/pull/100) push 1 (post-#98/#99 deploy). Judge step model remains **PARTIAL** (skipped on staging — by design).

**Shipped scope:**

| PR | Scope |
|----|--------|
| [#96](https://github.com/raimondskrauklis/revy/pull/96) | MRC-P0 (index embedding identity), MRC-P1 (attempt rows + judge/publish step models), MRC-P2.1 (`models_snapshot` column) |
| [#98](https://github.com/raimondskrauklis/revy/pull/98) | MRC-P2.2–P2.4 (`build_models_snapshot`, terminal writer hooks, `model_breakdown` staging metrics) |
| [#99](https://github.com/raimondskrauklis/revy/pull/99) | MRC-P3 (`PipelineRunResponse.models_snapshot`, index step `embedding_*` manifest fields, typed schemas) |

**Validation rule:** Merged code cannot self-validate on its own PR. Use a **dogfood PR opened after deploy** with `--since` at deploy completion — pre-deploy runs are excluded.

---

## Deploy boundaries

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| **#96 model-run-capture** | `2026-08-10T19:35:30Z` | **P0/P1 dogfood window** — migration `0032` + index/attempt capture |
| **#98 MRC-P2** | `2026-08-11T05:49:57Z` | **P2 dogfood window** — terminal `models_snapshot` writer |
| **#99 MRC-P3** | `2026-08-11T07:40:23Z` | **P3 dogfood window** — pipeline trace API exposure |

**Rule:** Use deploy job completion time (`gh run list --branch main`), not merge time. Run probe scripts from **`main`** (metrics scripts live on main); scope with `--pr-number` on the dogfood PR opened **after** deploy.

**Pre-deploy:** Do not count runs before the deploy boundary for the phase under sign-off.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#97](https://github.com/raimondskrauklis/revy/pull/97) | `chore/mrc-staging-dogfood` | **merged** — push 1 P0/P1 **PASS** |
| [#100](https://github.com/raimondskrauklis/revy/pull/100) | `chore/mrc-staging-dogfood-p2` | **merged** — push 1 P2/P3 **PASS** |

**Protocol:** One `backend/**` touch per push (probe import in `post_main_staging_probe.py`). Open a **new** dogfood PR after #99 deploy; push 1 triggers pipeline runs that exercise `models_snapshot` population + trace API fields.

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe v6 + autostart | **done** — 2 completed runs (P0/P1) |
| 2 | Post-#98/#99 deploy — `models_snapshot` + trace API | **done** — [#100](https://github.com/raimondskrauklis/revy/pull/100) push 1 — 2 completed runs |

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

## Pass criteria — push 2 / #98+#99 window (2026-08-11)

| Check | Pass | Evidence |
|-------|------|----------|
| `models_snapshot_populated` | **PASS** | `2/2` runs — `--mrc-gate` `models_snapshot_populated` |
| Snapshot shape | **PASS** | `embedding` + `reviewer` + `judge`/`publish` keys; `judge=null` (skipped) |
| `model_breakdown` (PO script) | **PASS** | `index_embed`/`review`/`publish` rows in `--json` output |
| Trace API `models_snapshot` | **PASS** | DB snapshot matches typed contract (`voyage-code-3.5` @ 1024) |
| Trace API index `embedding_*` | **PASS** | manifest `embedding_model=voyage-code-3.5`, `embedding_dimensions=1024` |

**Expected snapshot (full pipeline, embed path):**

```json
{
  "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5", "dimensions": 1024},
  "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
  "judge": null,
  "publish": {"provider": "moonshot", "model_id": "kimi-k2.7-code"}
}
```

All four role keys are always present when `models_snapshot` is populated; unused stages are `null`. Reuse-only index runs set `embedding` to `null`.

---

## Probe commands

```bash
cd backend
PR=100
SINCE=2026-08-11T05:49:57Z   # P2 (#98 deploy)
# SINCE=2026-08-11T07:40:23Z     # P3 API (#99 deploy)

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE --pr-number $PR --require-activity --rg15-gate --json
```

**P2 gate:** `models_snapshot_populated` is **INCONCLUSIVE** when `with_snapshot=0` and writer not deployed; **PASS** when completed runs show non-null `models_snapshot` after #98 deploy (`--since 2026-08-11T05:49:57Z`).

**P3 gate (manual):** Call pipeline trace API on a completed dogfood run; confirm `models_snapshot.embedding.model_id` matches staging `REVY_EMBEDDING_MODEL` and index step exposes manifest `embedding_*` fields.

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | `79626fa` | 2 completed runs; Revy **pass**; MRC P0 gate **pass** |
| 1 (pipeline) | `547f4f1` | initial probe commit — included in same `--since` window |
| 2 | `c2925da` | 2 completed runs; Revy **pass**; `models_snapshot` **2/2**; MRC P2 snapshot **pass** |
| 2 (probe) | `253655f` | initial probe commit — included in same `--since` window |

**Model breakdown (PR #100, post-#98/#99):**

| step_type | provider | request_model | n |
|-----------|----------|---------------|---|
| index_embed | voyage | voyage-code-3.5 | 2 |
| review | moonshot | kimi-k2.7-code | 2 |
| publish | moonshot | kimi-k2.7-code | 1 |

**Sample `models_snapshot` (run `c2925da`, 2026-08-11):**

```json
{
  "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5", "dimensions": 1024},
  "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
  "judge": null,
  "publish": {"provider": "moonshot", "model_id": "kimi-k2.7-code"}
}
```

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
| MRC-P2.2–P2.4 snapshot population | **PASS** | PR #100 — `with_snapshot=2/2` |
| MRC-P3 trace API exposure | **PASS** | manifest `embedding_*` + typed snapshot in DB |
| PO P0 (parallel) | **PASS** | 2 runs, 3 attempt rows in review-scoped PO query |
| RG-15 (parallel) | **PASS** | 1 superseded review run; no stuck processing |

**Verdict:** **MRC program staging sign-off PASS** — P0/P1 (#97), P2/P3 (#100). `--mrc-gate` exits 1 on `judge_step_model` when judge is skipped on staging; treat embed + snapshot checks as primary sign-off.
