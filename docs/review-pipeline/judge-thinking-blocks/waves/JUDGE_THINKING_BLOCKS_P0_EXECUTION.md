# docs/review-pipeline/judge-thinking-blocks/waves/JUDGE_THINKING_BLOCKS_P0_EXECUTION.md

# P0 — Content-block extract (execution)

Phase **P0** of [`JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md`](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md). Baseline: [`JUDGE_THINKING_BLOCKS_FINDINGS.md`](../JUDGE_THINKING_BLOCKS_FINDINGS.md) JTB-D1–D5, JTB-D9. **P0 only.**

**Goal:** `_extract_message_text` returns concatenated non-empty `text` blocks (or `""` when a non-empty `content` list has no text); thinking-first + text-later succeeds. Anthropic review maps `""` → `ServiceUnavailableError` in this phase so the helper is never half-wired.

## Decisions locked for P0

- Walk `content` in order; concatenate non-empty **`text`** strings with **no extra separator** (D1). Skip `thinking`, `redacted_thinking`, non-dict blocks, and blocks with missing/blank `text`.
- Helper stays **taxonomy-neutral**: return `str`; **never** raise `JudgeParseError` (D2).
- ≥1 non-empty text block → return that string (D3).
- Non-empty `content` with no text (thinking-only, tool-use-only) → return `""` (D4 helper half).
- HTTP / non-JSON / missing `content` / non-list / **empty `content: []`** stay `ServiceUnavailableError("Anthropic response invalid")` in the helper (D5). Existing empty-list preview test stays.
- **Review wrap in P0:** `_post_anthropic_messages` maps helper `""` → `ServiceUnavailableError` (same message as today). Do not leave `complete_review` returning `""` into `run_review_run` (`github_review.py` ~1331 catches only `(httpx.HTTPError, ServiceUnavailableError)`). Until P1, the judge path may still feed `""` into `parse_judge_payload` (`judge_json_invalid`) — that is why P0 does not merge without P1.
- **Ship with P1** (same PR, two LOOP commits). Do not merge P0 alone.
- No retries, no second model, no Bedrock, no JSON-contract rewrite (D7).

## PR review context (required — first phase commit)

- **SSOT (Moonshot + Greptile source):** `.revy/review-context.json` — `active_program: "judge-thinking-blocks"`; **`programs[]` = one entry only**; `scope: ["backend/**"]`; three doc paths below. Mirror the same JSON to `.agent/review-context.json`.
- **Greptile (vendor output):** regenerate `.greptile/files.json` — `cd backend && python -m scripts.generate_greptile_files_from_review_context --write` — **never hand-edit**.
- **Bugbot:** `.cursor/BUGBOT.md` — active program + links to the same three docs.

**Doc paths (`paths[]` only):**

- `docs/review-pipeline/judge-thinking-blocks/waves/JUDGE_THINKING_BLOCKS_P0_EXECUTION.md`
- `docs/review-pipeline/judge-thinking-blocks/JUDGE_THINKING_BLOCKS_FINDINGS.md`
- `docs/review-pipeline/judge-thinking-blocks/JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md`

## Out of scope for P0 (later phases)

- Judge wrap `""` → `JudgeParseError` (`judge_empty_text`) → **P1**
- Transport extra `content_block_types` on empty-text → **P1**
- Distinct artifact codes vs `judge_json_invalid` / D8 INFO audit → **P2**
- Staging metrics split + validation memo → **P3**

---

## P0.0 — Program PR review context (SSOT + Greptile + Bugbot)

**What:** Switch SSOT to `judge-thinking-blocks` (one program entry); regenerate Greptile `files.json`; replace Bugbot active-program links with the three docs above.

**Files:** `.revy/review-context.json`, `.agent/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && python -m scripts.generate_greptile_files_from_review_context --write
python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
python -m json.tool ../.revy/review-context.json > /dev/null
```

---

## P0.1 — Walk content and concatenate text blocks

**What:** Rewrite `_extract_message_text` to iterate `content`: collect non-empty `text` fields in order; skip `thinking` / `redacted_thinking` / non-dict / missing text. Return the concatenated string when ≥1 text block exists. Keep SUE + `response_body_preview` for missing / non-list / empty `content: []`.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Thinking-first + later `text` returns that assistant string; legacy `content[0].text` still returns; empty `[]` still SUE.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "extract_message_text" -q
```

---

## P0.2 — No-text non-empty list returns empty string

**What:** After a successful walk of a **non-empty** `content` list with zero text blocks (thinking-only, tool-use-only), return `""`. Do **not** raise `JudgeParseError` or SUE from the helper on this path.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Fixture `{content: [{type: thinking, thinking: "", signature: "…"}]}` → `""`; helper never raises `JudgeParseError`.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "extract_message_text" -q
```

---

## P0.3 — Anthropic review maps empty text to SUE

**What:** In `_post_anthropic_messages` only: if `_extract_message_text` returns `""`, raise `ServiceUnavailableError("Anthropic response invalid")` (failed run, not unhandled `ValueError` in `run_review_run`). Do not change `_post_judge_anthropic_messages` in P0 (judge wrap is P1).

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Review-path thinking-only payload raises SUE; judge HTTP path in P0 still surfaces helper `""` to the caller (P1 wrap not yet).

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "complete_review or post_anthropic or extract_message_text" -q
```

---

## P0.4 — Live-shape fixtures

**What:** Unit fixtures matching staging RTU shape: thinking-first + text-later (45-case); thinking-only (8-case); multiple text blocks concatenated; legacy single `text` block. Keep `test_extract_message_text_empty_content_includes_preview`.

**Files:** `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** All extract fixtures pass; empty-list preview assertion unchanged.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "extract_message_text" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/anthropic_review.py
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_generate_greptile_files.py -q
```

**Deploy:** Same PR as P1 — do not merge P0 without P1. No migration.

**Next:** [`JUDGE_THINKING_BLOCKS_P1_EXECUTION.md`](./JUDGE_THINKING_BLOCKS_P1_EXECUTION.md)
