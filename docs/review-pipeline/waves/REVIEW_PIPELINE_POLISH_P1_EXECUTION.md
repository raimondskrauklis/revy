# Polish P1 — Suggestion pipeline (execution)

Phase **P1** of [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](../REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_POLISH_FINDINGS.md](../REVIEW_PIPELINE_POLISH_FINDINGS.md) § Track A, Q# P1–P7. **Depends on P0.** **P1 only.**

**Goal:** Generate, store, and publish GitHub `` ```suggestion `` blocks on eligible inline comments (R6-Q3).

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) R6-Q3.

## Decisions locked for P1

- `SUGGESTION_MAX_LENGTH = 2000` in `app/services/github_suggestion.py` (P5 locked).
- Publish suggestion only when: non-empty stripped text; **no `\n` or `\r`** in suggestion (P6); `file_path` + `start_line` set; `end_line` is `null` or equals `start_line`; no `` ``` `` in suggestion body.
- **Single shared module** `app/services/github_suggestion.py`: `normalize_end_line`, suggestion eligibility helpers, `is_publishable_suggestion(finding) -> str | None` — imported by `_parse_finding_row` and publish (no duplicated rule lists).
- Normalize `end_line: 0` → `null` in parse (P7).
- Invalid / ineligible suggestion → message-only inline comment; publish job still `completed`.
- Extend `REVIEW_SYSTEM_PROMPT` in **both** `moonshot_review.py` and `anthropic_review.py` (Bedrock reviewer imports anthropic prompt).
- Optional JSON field `"suggestion"` — omit when no single-line fix.
- `_parse_finding_row`: store suggestion on parsed dict; strip multiline-anchor suggestions (drop field, keep finding).
- `format_inline_comment_body(..., suggestion: str | None = None)` appends fenced block after message when suggestion passed and already validated.
- Optional: add `suggestion?: string | null` on frontend `ReviewFinding` in `types.ts` (raw findings API parity; reviewer UI unchanged).

## Out of scope for P1 (later / never v1)

- Suggestion in reviewer UI table → parking lot
- Reconciled findings API → out of wave
- Check-run summary suggestion blocks → out of wave
- Multiline suggestion fences → out of wave
- Judge badge → **P2**

---

## P1.1 — Reviewer LLM prompt

**What:** Add optional `"suggestion":"single-line replacement or omit"` to `REVIEW_SYSTEM_PROMPT`; instruct model to include only for concrete single-line fixes on anchored lines.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/app/integrations/anthropic_review.py`

**Deliverable:** prompts contain `suggestion` key in documented JSON shape.

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py -q
```

---

## P1.2 — Shared suggestion helpers + parse

**What:** Add `app/services/github_suggestion.py` (`SUGGESTION_MAX_LENGTH`, `normalize_end_line`, shared eligibility). Extend `_parse_finding_row` to use shared helpers: accept optional `suggestion`; reject empty, over-max-length, contains `\n`/`\r`, or multiline-anchor (`end_line` set and ≠ `start_line`) by omitting suggestion from stored row; normalize `end_line: 0` → `null`; persist on `GitHubFindingORM` insert in `run_review_run`.

**Files:** `backend/app/services/github_suggestion.py`, `backend/app/services/github_review.py`, `backend/tests/unit/test_github_review.py` (or `test_github_suggestion.py`)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -q
```

---

## P1.3 — Inline comment formatter

**What:** Extend `format_inline_comment_body` to append `` \n\n```suggestion\n…\n``` `` when suggestion provided (`is_publishable_suggestion` lives in `github_suggestion.py` from P1.2).

**Files:** `backend/app/integrations/github_api.py`, `backend/tests/unit/test_github_api_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api_publish.py -q
```

---

## P1.4 — Publish loop wiring

**What:** In `run_publish_job` inline loop, pass `suggestion=is_publishable_suggestion(finding)` into `format_inline_comment_body`; existing 404/422 skip path unchanged.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:** tests cover suggestion in body, fence-char rejection, `\n` rejection, multiline anchor omission (use findings already persisted with normalized anchors — `end_line: 0` tests stay in P1.2).

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_moonshot_review.py \
  tests/unit/test_github_review.py \
  tests/unit/test_github_api_publish.py \
  tests/unit/test_github_publish.py -q
```

**Deploy:** no new migration; requires P0 `0025` applied.

**Next:** [REVIEW_PIPELINE_POLISH_P2_EXECUTION.md](./REVIEW_PIPELINE_POLISH_P2_EXECUTION.md)
