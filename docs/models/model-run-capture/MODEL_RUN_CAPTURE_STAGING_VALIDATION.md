# Model run capture — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md)

**Status:** *in progress* — #96 deployed on staging; validation runs on the **post-deploy dogfood PR**, not on #96 itself.

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
| TBD | `chore/mrc-staging-dogfood` | not opened — probe marker `post-main-dogfood-v6-mrc-model-capture` |

**Protocol:** One `backend/**` touch per push (probe import in `post_main_staging_probe.py`). Push 1 introduces marker; push 2 exercises full index → review → publish with new chunks (embed HTTP required).

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe v6 + autostart | pending |
| 2 | Full pipeline with embed — MRC gate | pending |

---

## Pass criteria — push 2

| Check | Pass | Evidence |
|-------|------|----------|
| Alembic `0032` | pending | `mrc_p0_gate.alembic_0032` |
| Index manifest `embedding_model` | pending | `index_identity.embed_with_model_in_manifest` |
| Index step `model_provider`/`model_id` | pending | `index_identity.embed_step_model_match` |
| `index_embed` attempt rows | pending | `index_embed_attempts.index_embed_attempts` |
| Manifest ↔ attempt model parity | pending | `embed_model_parity.parity_pass` |
| Judge/publish step model fields | pending | `step_models` (INCONCLUSIVE if judge skipped) |
| `models_snapshot` populated | skipped | MRC-P2.2 — expect INCONCLUSIVE until shipped |

---

## Probe commands

```bash
cd backend
PR=<dogfood-pr-number>
SINCE=2026-08-10T19:35:30Z

# MRC P0 + P1 gates (primary sign-off)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json

# PO baseline (still useful — alembic + attempt rows)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json

# RG-15 supersede (unchanged)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE --pr-number $PR --require-activity --rg15-gate --json
```

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | — | pending |
| 2 | — | pending |

---

## Sign-off

| Track | Status | Evidence |
|-------|--------|----------|
| MRC-P0 index identity | pending | — |
| MRC-P1 attempt + step models | pending | — |
| MRC-P2.1 schema (`models_snapshot` column) | pending | `alembic_0032` + column exists |
| MRC-P2.2+ snapshot population | skipped | not shipped in #96 |

**Next:** merge validation tooling to `main` → open dogfood PR (probe v6) → wait for full pipeline on that PR → run probes with `--since 2026-08-10T19:35:30Z`.
