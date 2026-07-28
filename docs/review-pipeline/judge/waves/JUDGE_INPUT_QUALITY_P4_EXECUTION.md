# Judge input quality P4 — Moonshot reviewer input (execution)

Phase **P4** of [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md). Baseline: [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) J-4. **P4 only.**

**Goal:** Moonshot reviewer prompt includes PR description when present.

## Decisions locked for P4

- **`GitHubPullRequestORM` has no `body` column** — webhook ingest (`_extract_pr_fields`) does not persist body today.
- **No migration** — fetch body at review time via GitHub REST `GET /repos/{owner}/{repo}/pulls/{number}` (same installation auth as compare).
- New `get_pull_request` in `github_api.py`; helper `_fetch_pr_body_for_review(session, pull_request)` in `github_review.py` returns `str | None` on success; `None` on API/parse failure — review still runs.
- `prepare_review_context` passes fetched body to `_build_review_prompt` as `pr_body`.
- Truncation via existing `PR_BODY_MAX_BYTES` in `_build_review_prompt`.
- No judge or reconcile changes.

## Out of scope for P4

- `body` column + webhook ingest + Alembic (defer — higher scope than this program)
- Index / retrieval changes
- Judge context → **P3**

---

## P4.1 — GitHub API: get pull request

**What:** Add `get_pull_request(client, installation_id, owner, repo, pull_number) -> dict` returning REST payload; extract `body` field (may be empty string → treat as `None` for prompt).

**Files:** `backend/app/integrations/github_api.py`, `backend/tests/unit/test_github_api.py` (or respx test module)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api.py -k get_pull_request -q
```

---

## P4.2 — Fetch body in `prepare_review_context`

**What:** Add `_fetch_pr_body_for_review(session, pull_request) -> str | None`; call from `prepare_review_context`; replace `pr_body=None` with fetched value in `_build_review_prompt`.

**Files:** `backend/app/services/github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k pr_body -q
```

---

## P4.3 — Unit tests + findings gap closure

**What:** `_build_review_prompt` includes `PR body:` when body non-empty; omitted when `None`. Mock `_fetch_pr_body_for_review` in `prepare_review_context` test — body forwarded into prompt. Mark J-4 **Addressed** in findings gap table.

**Files:** `backend/tests/unit/test_github_review.py`, `docs/review-pipeline/judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "pr_body or build_review_prompt" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_review.py tests/unit/test_github_api.py -k "pr_body or get_pull_request or build_review_prompt" -q
pipenv run ruff check app/services/github_review.py app/integrations/github_api.py
```

**Next:** [JUDGE_INPUT_QUALITY_P5_EXECUTION.md](./JUDGE_INPUT_QUALITY_P5_EXECUTION.md)
