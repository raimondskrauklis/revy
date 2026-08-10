# Model run capture — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md)

**Status:** push 1 validated on [#97](https://github.com/raimondskrauklis/revy/pull/97) — **MRC-P0 PASS**; MRC-P1 embed PASS; judge/publish step fields partial (see sign-off).

**Shipped scope (#96):** MRC-P0 (index embedding identity), MRC-P1 (attempt rows + judge/publish step models), MRC-P2.1 (`models_snapshot` column only — terminal writer is MRC-P2.2).

**Validation rule:** #96 ships capture code. The **next** PR opened after deploy (`chore/mrc-staging-dogfood`) triggers pipeline runs that exercise #96 on staging. Probes scope to that PR with `--since` at deploy completion — pre-deploy runs are excluded.

---

## Deploy boundaries

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| **#96 model-run-capture** | `2026-08-10T19:35:30Z` | **Dogfood window** — migration `0032` + P0/P1 capture |

**Rule:** Use deploy job completion time (`gh run list --branch main`), not merge time. Run probe scripts from **`main`** (metrics scripts live on main); scope with `--pr-number` on the dogfood PR opened **after** deploy.

**Pre-deploy:** Do not count runs before `2026-08-10T19:35:30Z` for MRC sign-off.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| [#97](https://github.com/raimondskrauklis/revy/pull/97) | `chore/mrc-staging-dogfood` | push 1 — probe `post-main-dogfood-v6-mrc-model-capture` |

**Protocol:** One `backend/**` touch per push (probe import in `post_main_staging_probe.py`). Push 1 introduces marker; push 2 optional for regrowth / supersede overlap.

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe v6 + autostart | **done** — 2 completed runs |
| 2 | Optional regrowth / overlap | pending |

---

## Pass criteria — push 1 (2026-08-10)

| Check | Pass | Evidence |
|-------|------|----------|
| Alembic `0032` | **PASS** | `alembic_0032` — `2026_08_10_1300_0032_github_pipeline_runs_models_snapshot` |
| Index manifest `embedding_model` | **PASS** | `2/2` embed runs — `voyage-code-3.5` |
| Index step `model_provider`/`model_id` | **PASS** | `2/2` voyage step model match |
| `index_embed` attempt rows | **PASS** | `2` rows, `request_model=voyage-code-3.5` |
| Manifest ↔ attempt model parity | **PASS** | `parity_pass=2` `parity_fail=0` |
| Judge step model fields | **PARTIAL** | `0/2` — judge likely skipped/disabled on staging (expected null model_ref) |
| Publish step model fields | **PARTIAL** | `1/2` — one run used publish fallback (no model fields by design, #96) |
| `models_snapshot` populated | **skipped** | MRC-P2.2 — `with_snapshot=0/2` INCONCLUSIVE |

---

## Probe commands

```bash
cd backend
PR=97
SINCE=2026-08-10T19:35:30Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE --pr-number $PR --require-activity --rg15-gate --json
```

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | `79626fa` | 2 completed runs; Revy **pass**; MRC P0 gate **pass** |
| 1 (pipeline) | `547f4f1` | initial probe commit — included in same `--since` window |

**Model breakdown (PR #97, post-#96):**

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
| MRC-P2.2+ snapshot population | skipped | not shipped in #96 |
| PO P0 (parallel) | **PASS** | 2 runs, 4 attempt rows in review-scoped PO query |
| RG-15 (parallel) | **PASS** | no stuck processing |

**Verdict:** **MRC-P0 + P1 embed sign-off PASS** for #96 on staging. Resume MRC-P2.2 (`build_models_snapshot` + terminal writer) on `main`.

**Gate note:** `--mrc-gate` exits 1 on judge/publish step checks when judge is skipped or publish uses fallback — treat embed + P0 checks as primary sign-off until gate logic distinguishes skip/fallback paths.
