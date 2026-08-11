# docs/models/model-run-capture/waves/MODEL_RUN_CAPTURE_P3_EXECUTION.md

# MRC-P3 — API exposure + staging sign-off (execution)

Phase **MRC-P3** of [`MODEL_RUN_CAPTURE_GENERAL_PLAN.md`](../MODEL_RUN_CAPTURE_GENERAL_PLAN.md). Baseline: findings §Parking lot (API). **MRC-P3 only — final phase.**

**Goal:** Pipeline trace API exposes `models_snapshot` and index manifest embedding fields; staging sign-off criteria documented.

**Status:** **shipped** — `PipelineRunResponse.models_snapshot` + index step `embedding_*` manifest fields.

## Decisions locked for MRC-P3

- `PipelineRunResponse` gains optional `models_snapshot` JSONB field.
- Index step in trace response includes flattened `embedding_model`, `embedding_dimensions`, `embedding_skipped_reason` from manifest artifact (parse `PipelineArtifactKind.manifest`).
- No workspace settings UI; operator/API consumers only.
- Staging sign-off: dogfood pipeline run shows `voyage-code-3.5` (or current env) in snapshot + manifest.

## Out of scope for MRC-P3

- User-facing PR UI / i18n
- OTel export → PO-P5
- Retrieve `query_embedding_model` → MRC-Q7 v1.1

---

## MRC-P3.1 — Response schemas

**What:** Add `models_snapshot` to `PipelineRunResponse`; add optional embedding manifest fields to index step schema or nested manifest DTO.

**Files:** `backend/app/schemas/github_pipeline.py`

**Deliverable:** Schema round-trip covered by P3.3; lint gate:

```bash
cd backend && pipenv run ruff check app/schemas/github_pipeline.py && pipenv run pytest tests/unit/test_model_run_capture_p3.py -k "schema" -q
```

---

## MRC-P3.2 — Trace API mapping

**What:** `get_pipeline_trace_for_review_run` (and related mappers) populate new fields from ORM + manifest artifact parsing.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k "pipeline_trace or models_snapshot" -q
```

---

## MRC-P3.3 — API unit coverage

**What:** End-to-end unit test: mocked pipeline run with index manifest + snapshot returns expected JSON shape for all four roles.

**Files:** `backend/tests/unit/test_model_run_capture_p3.py` (new)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_model_run_capture_p3.py -q
```

---

## MRC-P3.4 — Doc sync + staging sign-off row

**What:** Update execution README status rows; add model-run-capture sign-off criteria to [`docs/review-pipeline/staging-validation/README.md`](../../../review-pipeline/staging-validation/README.md) (pass criteria: manifest + snapshot show embedding model after dogfood index).

| Doc | Change |
|-----|--------|
| `docs/models/model-run-capture/waves/README.md` | MRC-P0–P3 status Done + sha |
| `docs/models/model-run-capture/README.md` | Link waves index; program status |
| `docs/review-pipeline/staging-validation/README.md` | Row: model-run-capture — embedding model in manifest/snapshot |

**Deliverable:** Grep confirms sign-off row exists; no changelog (operator-only, not user-facing).

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/schemas/github_pipeline.py app/services/github_pipeline_trace.py
pipenv run pytest tests/unit/test_github_pipeline_trace.py tests/unit/test_model_run_capture_p3.py -q
```

**Human gate (non-blocking for commit):** Run dogfood index on staging; confirm `models_snapshot.embedding.model_id` matches `REVY_EMBEDDING_MODEL` via API or SQL.

**Next:** none — program complete after doc sync.
