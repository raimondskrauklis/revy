# docs/review-pipeline/judge-thinking-blocks/waves/JUDGE_THINKING_BLOCKS_P2_EXECUTION.md

# P2 — Trace codes (execution)

Phase **P2** of [`JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md`](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md). Baseline: [`JUDGE_THINKING_BLOCKS_FINDINGS.md`](../JUDGE_THINKING_BLOCKS_FINDINGS.md) JTB-D6, JTB-D8. **P2 only.**

**Goal:** Operators can tell additive `judge_empty_text` from live **`judge_json_invalid`** from HTTP `"Anthropic response invalid"` without opening thinking `signature` in worker INFO. Do not rename `judge_json_invalid`.

## Decisions locked for P2

- Manifest / artifact `parse_error` strings: `judge_empty_text` (P1 wrap), **`judge_json_invalid`** (existing `parse_judge_payload` / `ValueError("judge_json_invalid")`), HTTP/SUE transport message unchanged.
- Do **not** rename `judge_json_invalid`. Do **not** add a second JSON-invalid token (D6).
- `content_block_types` already recorded on the P1 wrap; P2 asserts it appears on judge failure artifacts / log extra where transport merge already copies extra (`_judge_failure_log_extra` / `_judge_failure_artifact`).
- `judge_json_contract_staging_metrics.py` keeps grouping by any `parse_error` — **no** hardcoded old-string filter, **no** schema migration (D6).
- **D8:** worker **INFO** extras never include thinking `signature`. Manifest truncated `raw_response_text` dump stays (signatures may appear there). No stripping pass.
- Stop using `"Anthropic response invalid"` for thinking-first empty-text (that path is `judge_empty_text` after P1). Empty `[]` / HTTP / non-JSON still use the transport SUE message.

## Out of scope for P2 (later phases)

- Staging `--since` split (text-later vs thinking-only) and JTB-Q5 fill → **P3**
- New tables / new DB columns → never in this program
- Extra retries / second model → never (D7)

---

## P2.1 — Artifact codes on failure

**What:** Ensure discovery/verification failure artifacts persist `parse_error=judge_empty_text` on empty-text (via existing `judge_failure_trace_fields` → `JudgeParseError.code`) and `parse_error=judge_json_invalid` on invalid JSON. HTTP/SUE remains the transport message.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/integrations/judge_llm_errors.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:** Unit tests assert the three codes are distinct on artifacts.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "parse_error or judge_empty_text or judge_json_invalid" -q
```

---

## P2.2 — `content_block_types` on merged extra

**What:** Confirm `_judge_failure_log_extra` / transport merge surfaces `content_block_types` from P1 wrap on empty-text failures. No new column; extra dict only.

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_github_finding_judge.py`

**Deliverable:** Log extra on thinking-only miss includes `content_block_types`.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_anthropic_review.py -k "content_block_types or judge_empty_text" -q
```

---

## P2.3 — Worker INFO never dumps `signature`

**What:** Audit `logger.info` in `_post_judge_anthropic_messages` / transport helpers: extras must not include thinking `signature`. Do not add a full-body INFO dump. Manifest truncated dump unchanged.

**Files:** `backend/app/integrations/anthropic_review.py`, `backend/tests/unit/test_anthropic_review.py`

**Deliverable:** Completion/failure INFO extras have no `signature` key; a thinking-first fixture does not log `signature`.

```bash
cd backend && pipenv run pytest tests/unit/test_anthropic_review.py -k "judge_llm_request or signature or transport" -q
```

---

## P2.4 — Metrics script: group by any `parse_error`

**What:** Confirm `judge_json_contract_staging_metrics.py` has no hardcoded `"Anthropic response invalid"` (or `judge_json_invalid`) filter that would hide `judge_empty_text`. Do not add a text-later vs thinking-only split here (P3). Script still runs.

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`

**Deliverable:** `rg` shows no hardcoded live-token or old-string filter on `parse_error`; existing group-by any `parse_error` remains.

```bash
cd backend && pipenv run python -m py_compile scripts/judge_json_contract_staging_metrics.py
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/anthropic_review.py app/integrations/judge_llm_errors.py app/services/github_finding_judge.py
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py -q
```

**Deploy:** Backend + worker; no migration. Can ship in the P0+P1 PR or the next commit on the same branch.

**Next:** [`JUDGE_THINKING_BLOCKS_P3_EXECUTION.md`](./JUDGE_THINKING_BLOCKS_P3_EXECUTION.md)
