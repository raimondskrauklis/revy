# Judge thinking-blocks — findings

**Date:** 2026-08-21  
**Purpose:** Baseline for a **narrow adapter program** — extract judge (and Anthropic review) text from Messages `content` blocks when the first block is `thinking`. **No execution steps.**  
**Evidence:** [LIVE_TRAFFIC_FINDINGS.md](../staging-validation/LIVE_TRAFFIC_FINDINGS.md) LT-1; `revy-staging` 2026-08-21 (`--since 2026-08-07`); `anthropic_review.py` `_extract_message_text`; `github_finding_judge.py` `call_judge_with_optional_retry`.

**July programs remain valid but insufficient:** JSON-contract + snippet prompts moved persistence **21% → 62.4%**. The remainder is concentrated on thinking-first bodies, not missing structured output.

---

## Build principles

1. **RG-6 withhold stays** (JC-D1) — no outcome row → no escalation inline publish.
2. **Extract before retry** — do not spray extra retries on `ServiceUnavailableError`.
3. **One extract helper** — judge HTTP and Anthropic `complete_review` share `_extract_message_text`; it stays taxonomy-neutral (no `JudgeParseError`).
4. **Fail loud with a distinct code** — judge wrap uses `judge_empty_text`; do not lump thinking-only with HTTP `"Anthropic response invalid"`.
5. **Real fixtures** — unit tests use the live content-block shape (thinking + optional later `text`), not invented schemas.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Thinking-first** | `content[0].type = thinking` (often `thinking: ""` + `signature`) |
| **Text-later** | ≥1 later block with `type=text` and non-empty `text` — **45/53** live misses |
| **Thinking-only** | thinking present, no `text` block — **8/53** |
| **Extract** | Join non-empty `text` fields from `content` in order; ignore thinking / signatures |

---

## What exists vs gap

### Verified live window (from 7 Aug)

| Metric | Value |
|--------|------:|
| Judge manifest candidates | 141 |
| With `outcome` | 88 (**62.4%**, target ≥95%) |
| `parse_error=Anthropic response invalid` | 53 |
| Of those: thinking-first | **53 / 53** |
| Of those: text-later | 45 |
| Of those: thinking-only | 8 |
| `retry_count > 0` | **0** |
| Judge steps with model | 61 × `anthropic` / `claude-sonnet-5` |

Sample body (truncated): `content: [{"type": "thinking", "thinking": "", "signature": "…"}, …]`. Model in payload: `claude-sonnet-5` (RTU).

### Code today (verified)

| Layer | Behavior | Gap |
|-------|----------|-----|
| `_extract_message_text` | Requires `content[0].text` non-empty | Thinking-first → `ServiceUnavailableError("Anthropic response invalid")` |
| Callers | Judge `_post_judge_anthropic_messages` **and** review `_post_anthropic_messages` | Same extract bug; **D4 wrap is judge-only** (review must stay SUE, not `JudgeParseError`) |
| `call_judge_with_optional_retry` | Retries **only** `JudgeParseError` / `judge_outcome_invalid` | Transport extract miss never retries |
| Profile fallback | Catches `ServiceUnavailableError` if a second profile exists | Unknown whether droplet has direct key; not the 45-case fix |
| Manifest | Stores `raw_response_text` + `parse_error` (JSON-contract P1) | Enough to prove thinking-first; codes are too coarse |
| Tests | `test_extract_message_text_empty_content_includes_preview` | No thinking-first / text-later fixture |

**Bedrock** uses `parse_judge_payload` on already-extracted text — **out of this program** unless a later miss shows Bedrock thinking blocks.

---

## Locked decisions

| ID | Decision |
|----|----------|
| **JTB-D1** | Walk `content` in order; concatenate non-empty **`text` blocks**. Skip `thinking` / `redacted_thinking` / non-dict / missing text. |
| **JTB-D2** | Same **taxonomy-neutral** helper for **judge and Anthropic review**. Do not fork extract. Helper never raises `JudgeParseError` (`ValueError`) — `complete_review` / `run_review_run` only map `(httpx.HTTPError, ServiceUnavailableError)` (`github_review.py` ~1331). |
| **JTB-D3** | After a successful walk with ≥1 text block → return that string (then existing `parse_judge_payload` on the judge path). |
| **JTB-D4** | After a walk of a **non-empty** `content` list with **no** text blocks → helper returns `""`. **`_post_judge_anthropic_messages` only** maps that to **`JudgeParseError`** (`judge_empty_text`) so the existing one retry can fire. Anthropic review maps `""` → `ServiceUnavailableError` (failed run, not an unhandled exception). |
| **JTB-D5** | HTTP / non-JSON / missing `content` / non-list / **empty `content: []`** stay `ServiceUnavailableError` in the helper (real transport). Empty list was **0/53** live. |
| **JTB-D6** | Additive `parse_error` is **`judge_empty_text` only**. Live JSON-invalid code stays **`judge_json_invalid`** (`judge_llm_errors.py` `ValueError("judge_json_invalid")`; tests already assert that). Do not rename it. Do not add a second JSON-invalid token. HTTP stays the transport message. Stop using `"Anthropic response invalid"` for thinking-first empty-text. |
| **JTB-D7** | **RG-6 stays.** No extra retry storms; do not **add** a second model (existing gateway→direct `_post_judge_with_profile_fallback` stays). No JSON-contract / structured-output rewrite. Do not add retries to chase the 0.7pt extract-only gap (see D9). |
| **JTB-D8** | **Worker INFO** never dumps thinking `signature` (JT-Q4). **Manifest** keeps today’s truncated `raw_response_text` (signatures may appear there). Operators use D6 codes + optional `content_block_types` — do not add a stripping pass or migration. |
| **JTB-D9** | Extract-only ceiling on the **2026-08-07 window** is **133/141 = 94.3%** (88 existing outcomes + 45 text-later, if all 45 parse as judge JSON). P3 **passes** at ≥95% **or** when residual is classified (thinking-only / invalid JSON / other) and JSON-contract is not reopened. |

**Contradiction closed:** July JSON-contract findings blamed prompt/schema. Live 45/53 already contain parseable assistant text the adapter never reads. JSON-contract work still applies to thinking-only (8) and residual invalid JSON — this program does not reopen P3 structured output.

---

## Catalog

| Track | Method |
|-------|--------|
| Text-later (45) | Extract — should become ordinary `parse_judge_payload` successes |
| Thinking-only (8) | Helper `""` → judge wrap `JudgeParseError` → one schema-reminder retry; may still fail if the model returns thinking-only again |
| Residual JSON | Unchanged JSON-contract path after extract |

---

## Data scope & exclusions

**In:** Anthropic Messages `content` extract; judge retry classification; unit tests; staging metrics re-measure.  
**Out:** Moonshot; Voyage; RCX; LT-2 attempt complete; LT-3 stuck processing; Bedrock extract; droplet credential ops (JT-Q6); new DB columns.

---

## Edge cases

| Case | Handling |
|------|----------|
| `content[0]` is text (legacy tests / direct API) | Unchanged success |
| Multiple text blocks | Concatenate in order (D1) |
| Thinking-only after retry | Persist `JudgeParseError`; RG-6 withhold |
| Tool-use-only (0 in live sample) | Same as no-text → D4 (judge wrap) |
| Empty `content: []` | D5 — SUE in helper (not `judge_empty_text`) |
| Review path via Anthropic, no text | D2 + D4 — helper `""` → review raises SUE, not `JudgeParseError` |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| JTB-Q1 | Adapter vs JSON-contract as primary miss? | **locked** | Adapter (D1–D3); JSON-contract not reopened |
| JTB-Q2 | Retry thinking-first as transport error? | **locked** | No — extract first; empty-text → `JudgeParseError` at **judge wrap only** (D4) |
| JTB-Q3 | Fork extract for judge only? | **locked** | No — shared helper (D2); wrap is judge-only, extract is not |
| JTB-Q4 | Relax RG-6 while persistence is 62%? | **locked** | No (D7) |
| JTB-Q5 | Will retry recover thinking-only (8)? | **open (calibration)** | Measure after P1 on staging |
| JTB-Q6 | Raise `JudgeParseError` from `_extract_message_text`? | **locked** | No — D2/D4 raise-site ([pass-01](./reviews/architecture-peer-review/pass-01-2026-08-22.md)) |
| JTB-Q7 | Empty `content: []` → `judge_empty_text` or SUE? | **locked** | SUE (D5); 0 live |
| JTB-Q8 | Strip `signature` from manifest `raw_response_text`? | **locked** | No — D8: INFO never dumps it; manifest truncated dump stays |

---

## Parking lot

- Direct Anthropic on droplet (fallback) — transport program, not this one.
- Worker-log `parse_error` wording once D6 ships.
- `revy` #102 `01a020aa-…` as post-deploy re-check sample.

---

## Devil's advocate

- If RTU stops sending a later `text` block, P0 does nothing for those rows — P1 retry is the only residual lever, and it may not be enough.
- Concatenating text blocks could join reasoning leaked as `text`; live samples used empty thinking + later JSON text — keep tests on that shape.
- 62% → 95% is **not** guaranteed by extract alone: ceiling on the baseline window is **94.3%** even if all 45 text-later parse as JSON (D9). Measure in P3; do not expand this program into prompt/schema work to chase 0.7 points.

---

## Experiment / verification

| Check | Pass | Fail |
|-------|------|------|
| Text-later fixture | Extract returns the `text` JSON string | Still `Anthropic response invalid` |
| Thinking-only | `JudgeParseError` + `retry_count` 0 then 1 on the existing retry | Still `ServiceUnavailableError` |
| Live `--since` after deploy | ≥95% **or** residual classified (thinking-only / invalid JSON); extract-only ceiling on the 7 Aug window is **94.3%** | Persistence stuck ~62% with thinking-first `parse_error`; or P3 treats 94.3% as hard fail and reopens JSON-contract |
| Legacy `content[0].text` only | Tests still pass | Regressed direct/simple payloads |

---

## References

- Live fleet: [LIVE_TRAFFIC_FINDINGS.md](../staging-validation/LIVE_TRAFFIC_FINDINGS.md) § LT-1  
- July contract: [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md)  
- Transport: [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)  
- Code: `backend/app/integrations/anthropic_review.py` ~208–230, ~317, ~368; `backend/app/services/github_finding_judge.py` ~90–136  
- Tests: `backend/tests/unit/test_anthropic_review.py` (`test_extract_message_text_empty_content_includes_preview`)
