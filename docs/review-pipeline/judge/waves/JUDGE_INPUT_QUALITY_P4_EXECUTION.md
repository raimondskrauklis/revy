# Judge input quality P4 — Moonshot reviewer input (execution)

Phase **P4** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-4. **P4 only.**

**Goal:** Moonshot reviewer prompt includes PR description when present.

## Decisions locked for P4

- **`github_pull_requests.body` column** — nullable `TEXT`; migration `0027_github_pull_request_body`.
- **Webhook ingest** — `_extract_pr_fields` persists `body` from PR payload; `_upsert_pull_request` updates on every handled action including **`edited`**.
- **Review** — `prepare_review_context` passes `pull_request.body` to `_build_review_prompt`; truncate with `PR_BODY_MAX_BYTES`. **No** per-review GitHub API fetch (that was a workaround).
- `get_pull_request` in `github_api.py` remains a general API helper only — not used on the review hot path.

## Out of scope for P4

- Backfill job for PRs ingested before migration (body fills on next webhook `opened`/`synchronize`/`edited`)
- Judge changes; index/retrieval changes

---

## P4.1 — Migration + ORM

**What:** Add `body` to `GitHubPullRequestORM`; hand-written Alembic revision `0027_github_pull_request_body`.

**Files:** `backend/app/models/github_pull_request.py`, `backend/alembic/versions/2026_07_28_1000_0027_github_pull_request_body.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/models/github_pull_request.py alembic/versions/2026_07_28_1000_0027_github_pull_request_body.py
```

**LOOP pause** after this subphase until migration applied in deploy environments.

---

## P4.2 — Webhook ingest

**What:** Extract `body` in `_extract_pr_fields`; persist on create/update; add `edited` to `_PULL_REQUEST_ACTIONS`.

**Files:** `backend/app/services/github_pull_requests.py`, `backend/tests/unit/test_github_pull_requests.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pull_requests.py -k body -q
```

---

## P4.3 — Review prompt + findings closure

**What:** `prepare_review_context` uses `pull_request.body`; tests on `_build_review_prompt`. Mark J-4 **Addressed** in findings.

**Files:** `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py`, `docs/review-pipeline/judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k pr_body -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_pull_requests.py tests/unit/test_github_review.py -k "body or pr_body" -q
pipenv run ruff check app/services/github_pull_requests.py app/services/github_review.py
```

**Next:** [JUDGE_INPUT_QUALITY_P5_EXECUTION.md](./JUDGE_INPUT_QUALITY_P5_EXECUTION.md)
