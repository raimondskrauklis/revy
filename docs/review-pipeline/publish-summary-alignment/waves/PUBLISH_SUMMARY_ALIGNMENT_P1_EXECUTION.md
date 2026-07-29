# Publish summary alignment P1 — Moonshot + parity (execution)

Phase **P1** of [PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md](../PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md). **P1 only.**

**Goal:** Moonshot issue comment path meets same product bar as P0 fallback.

**Peer review:** System prompt update **required** (not optional); product bar simplified.

## Decisions locked for P1

- `_build_issue_comment_user_prompt`: PR-wide confidence/merge/rationale from `verdict_groups(ctx)`; capped JSON for **generation** active + **PR** active; explicit instruction to render `### This generation` + `### Still open on PR` (no `### Findings`).
- **`ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` (required):** Replace step (7) `### Findings table` with two-block sections matching `format_summary_comment` headings; renumber if needed. Assert in `test_moonshot_review.py` if constant is tested.
- **`_issue_comment_meets_product_bar`:** When `_active_groups(verdict_groups(ctx))` non-empty → require `### This generation` **and** `### Still open on PR` (both always emitted by `format_summary_comment`). Reject `### Findings` as sole table. When PR clean (no active anywhere) → allow empty generation block text only.
- Moonshot success: missing either heading when PR has active → thin → fallback. `_insert_resolution_metrics_block` already P0-fixed.
- Babysit-grade parity: extracted two-block substring **identical** between `build_check_run_summary` and `build_pr_review_comment_fallback` (not full issue body).

## Out of scope for P1

- Moonshot **review** JSON path
- Publish worker / `compute_check_conclusion`

---

## P1.1 — Moonshot user prompt parity

**What:** Update `_build_issue_comment_user_prompt` per locked decisions; unit test asserts prompt contains both block headings instruction + PR-wide confidence value.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "user_prompt" -q
```

---

## P1.2 — System prompt rewrite (required)

**What:** Rewrite `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` in `moonshot_review.py` — two-block findings sections instead of `### Findings`; keep Greptile section order otherwise. Update product bar to reject legacy `### Findings`-only shape when active findings exist.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_moonshot_review.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py tests/unit/test_github_publish_formatter.py -k "product_bar or thin_moonshot or moonshot" -q
```

---

## P1.3 — Check ≡ issue two-block parity test

**What:** `test_check_and_issue_share_identical_summary_blocks` — same `PublishFormatContext` with `pr_active_groups` extras; compare normalized substring from `### This generation` through end of `### Still open on PR` section in check summary vs issue fallback.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k parity -q
```

---

## P1.4 — Moonshot mock path regression

**What:** Update async `build_pr_review_comment` mocks to emit two-block markdown (not `### Findings`); thin mock missing `### Still open on PR` → fallback; success path includes resolution metrics insert before `### This generation`.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "build_pr_review_comment" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_moonshot_review.py -q
pipenv run ruff check app/services/github_publish_formatter.py app/integrations/moonshot_review.py
```

**Next:** [PUBLISH_SUMMARY_ALIGNMENT_P2_EXECUTION.md](./PUBLISH_SUMMARY_ALIGNMENT_P2_EXECUTION.md)
