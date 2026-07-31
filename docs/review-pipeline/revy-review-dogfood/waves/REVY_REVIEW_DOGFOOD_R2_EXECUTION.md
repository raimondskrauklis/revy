# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R2_EXECUTION.md

# R2 — Publish hygiene: thread resolve taxonomy (execution)

Phase **R2** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § RR-DG1, RR-DG7, RR-DG9, RC-2. **R2 only.**

**Goal:** Every skipped thread resolve is classified in manifest + logs; no silent `continue` on `thread_id is None`.

## Decisions locked for R2

- Extend `publish_job.summary_json` with `thread_resolve_skipped: { reason: count }`.
- Reasons: `thread_id_not_found`, `thread_not_revy_owned`, `resolve_mutation_failed`, `already_resolved`.
- Replace silent skip at `github_publish.py` ~712 with WARN log + counter increment (`fingerprint`, `comment_id` in `extra`).
- Optional **single retry** on `resolve_mutation_failed` only (not on `thread_id_not_found`).
- `thread_not_revy_owned`: count when R0.5 `thread_owner=mixed`; skip resolve attempt when comment author is not installation bot; if `thread_owner=unknown`, count only — no ownership filter.
- Do not change GH-1v2 pairing model.

## Out of scope for R2

- Resolution stamp / compare → **R3**
- HEAD suppression → **R4**

---

## R2.1 — Skip reason enum + manifest schema

**What:** Add typed skip reasons on publish summary builder; persist `thread_resolve_skipped` on every publish job completion path (including skip/superseded jobs that ran resolve step).

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py`

**Deliverable:** `summary_json.thread_resolve_skipped` dict present on completed publish jobs that executed `_resolve_stale_inline_threads`.

---

## R2.2 — thread_id_not_found visibility + mutation retry

**What:** When `thread_id is None` after lookup, log `github_publish_resolve_inline_thread_skipped` with `reason=thread_id_not_found`, `fingerprint`, `comment_id`; increment manifest counter. On `resolve_mutation_failed`, log truncated GraphQL error body; **one** immediate retry before final count.

**Files:** `backend/app/services/github_publish.py` (`_resolve_stale_inline_threads`, ~692–730)

**Deliverable:** Unit tests assert log + counter for missing `thread_id`; retry succeeds on second GraphQL call in mutation-failure fixture.

---

## R2.3 — Formatter / operator summary line

**What:** Human-readable publish footer line: `Thread resolve skipped: N (thread_id_not_found: X, resolve_mutation_failed: Y, …)` for issue comment / check summary.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_publish.py` (`_flush_publish_surface`)

**Contract (locked):** `thread_resolve_skipped` does **not** flow through `format_summary_comment` / `PublishFormatContext`. `_flush_publish_surface` appends the footer via `append_thread_resolve_skipped_block(issue_comment_body, thread_resolve_skipped)` and the same for `check_summary_body` after `_resolve_stale_inline_threads` returns counters. Unit tests call `format_thread_resolve_skipped_block` / `append_thread_resolve_skipped_block` directly.

**Deliverable:** Formatter test includes skip breakdown when counters non-zero.

---

## R2.4 — Regression tests (RR-DG1 / RR-V4 prep)

**What:** Test matrix:

| Case | Expected reason |
|------|-----------------|
| Already resolved in thread index | `already_resolved` |
| GraphQL mutation errors | `resolve_mutation_failed` |
| Missing thread id | `thread_id_not_found` |
| Non-bot comment when `thread_owner=mixed` | `thread_not_revy_owned` |

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -q -k "resolve or thread"
```

---

**Phase gate:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_publish_formatter.py -q -k "resolve or thread"
pipenv run ruff check app/services/github_publish.py app/services/github_publish_formatter.py
```

**Next:** [REVY_REVIEW_DOGFOOD_R3_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R3_EXECUTION.md)
