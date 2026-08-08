# docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_P2_EXECUTION.md

# P2 — Moonshot + API + dogfood + trace (execution)

Phase **P2** of [`PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`](../PR_SUMMARY_ROLLUP_GENERAL_PLAN.md). Baseline: [`PR_SUMMARY_ROLLUP_FINDINGS.md`](../PR_SUMMARY_ROLLUP_FINDINGS.md) §reuse traps (Moonshot drift), PSR-Q8. **P2 only.**

**Goal:** LLM cannot drift on PR summary; API exposes rollup; operators verify via dogfood script.

## Decisions locked for P2

- `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` — add `### PR summary` lifetime section before push delta; instruct model not to invent lifetime counts.
- `_build_issue_comment_user_prompt` — include serialized `pr_resolution_rollup` manifest subset; explicit “do not replace PR summary block”.
- Moonshot success path: `splice_deterministic_pr_summary_block` after LLM response (same pattern as findings tables).
- `_issue_comment_meets_product_bar` — require `### PR summary` when rollup `raised_count > 0` or `review_count > 1`; thin → fallback.
- PSR-Q8 ship: add `pr_resolution_rollup: dict | None` on `GitHubPublishJobResponse` (from `job.summary_json`); wire both publish-job GET routes in `installation_review.py`.
- Dogfood: `revy_review_dogfood_staging_validation.py` asserts `pr_resolution_rollup` keys + `still_open_display` parity vs comment block 2 when present.
- Pipeline trace (optional): `record_publish_pipeline_step` payload includes `rollup_pass` key with manifest subset on completed publish.

## Out of scope for P2 (later phases)

- Staging memo sign-off / human gate → **P3**
- Revy frontend UI for rollup history → deferred (findings parking lot)
- Pre-program PR backfill tooling → out of program (PSR-Q6)

---

## P2.1 — Moonshot prompt + product bar

**What:** Update `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` and `_build_issue_comment_user_prompt`; extend `_issue_comment_meets_product_bar` for `### PR summary`; unit tests on prompt substrings and bar rejection when PR summary missing.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_moonshot_review.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py tests/unit/test_github_publish_formatter.py -k "moonshot or product_bar or pr_summary" -q
```

---

## P2.2 — Moonshot splice on success path

**What:** In `build_pr_review_comment` Moonshot branch, call `splice_deterministic_pr_summary_block` after findings splice; thin-moonshot fallback preserves deterministic PR summary from P1 fallback.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "build_pr_review_comment" -q
```

---

## P2.3 — API `GitHubPublishJobResponse.pr_resolution_rollup`

**What:** Add optional field to schema; populate from `job.summary_json.get("pr_resolution_rollup")` in route handlers; route tests for GET publish job + latest publish job endpoints.

**Files:** `backend/app/schemas/github_publish.py`, `backend/app/api/v1/workspaces/installation_review.py`, `backend/tests/unit/test_github_publish_routes.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/ -k "publish_job and pr_resolution" -q
```

---

## P2.4 — Dogfood script rollup gates

**What:** Extend `revy_review_dogfood_staging_validation.py` — read `summary_json.pr_resolution_rollup`, assert schema v1 keys, `still_open_display` sanity, `review_count >= 1` on completed publish.

**Files:** `backend/scripts/revy_review_dogfood_staging_validation.py`, `backend/tests/unit/test_revy_review_dogfood_staging_validation.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/ -k "dogfood" -q
```

---

## P2.5 — Pipeline trace `rollup_pass` (optional)

**What:** When `record_publish_pipeline_step` runs for completed publish, attach `rollup_pass` object (`raised_count`, `resolved_count`, `still_open_display`, `review_count`) to step metadata. Unit test on trace reader.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_pipeline_trace.py`, `backend/tests/unit/test_github_pipeline_trace.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k "rollup" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_moonshot_review.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_pipeline_trace.py -q
pipenv run pytest tests/unit/ -k "publish_job and pr_resolution or dogfood" -q
pipenv run ruff check app/schemas/github_publish.py app/api/v1/workspaces/installation_review.py app/integrations/moonshot_review.py
```

**Deploy:** requires P0 migration + P1 formatter on staging before P3 dogfood.

**Next:** [`PR_SUMMARY_ROLLUP_P3_EXECUTION.md`](./PR_SUMMARY_ROLLUP_P3_EXECUTION.md)
