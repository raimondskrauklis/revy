# Judge thinking-blocks — general plan

**Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md) (2026-08-21)  
**Prerequisite:** Judge JSON-contract + transport on `main` (manifest `raw_response_text` / `parse_error`, one parse retry).

**Thesis:** Live 62.4% judge persistence is an **extract bug**, not a new JSON-contract wave. Shared helper reads all Messages `text` blocks; **judge wrap only** maps empty text to `JudgeParseError` so the existing retry can fire; keep RG-6.

**Locked:** JTB-D1–D9. **Open calibration:** JTB-Q5 (whether thinking-only recovers on retry) — measured in P3, does not change direction.

Pass-01 architecture review blockers (D2/D4 raise-site, P3 94.3% ceiling) are locked here — do not re-open.

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` — thinking-first + text-later, thinking-only, legacy `content[0].text`, multiple text blocks; judge retry classification; Anthropic review extract shares the helper.
- **Lineage:** Distinct `parse_error` codes (D6); optional `content_block_types` on transport extra. Worker INFO never dumps thinking `signature` (D8); manifest truncated dump stays.
- **Coverage:** Text-later (45) vs thinking-only (8) called out in tests and validation, not averaged away.
- **i18n:** Backend-only — no new UI strings.
- **Publish:** RG-6 unchanged (D7). Bedrock extract out of scope.

---

## P0 — Content-block extract (foundations)

**Goal:** `_extract_message_text` returns concatenated non-empty `text` blocks (or `""` when a non-empty `content` list has no text); thinking-first + text-later succeeds.

**Scope — in:** Shared helper (D1–D3, D2) used by judge HTTP and Anthropic `complete_review`; fixtures matching live RTU shape; HTTP / non-JSON / missing / empty `content: []` stay `ServiceUnavailableError` (D5). Helper does **not** raise `JudgeParseError`.

**Scope — out:** Retry taxonomy; judge-only wrap; structured output; Moonshot; Bedrock.

**Deliverables:** Text-later payloads yield the assistant `text` string; thinking-only / tool-use-only yield `""`; legacy single-block tests still pass; unit coverage for skip-thinking / concat / empty-list SUE.

**Depends on:** None. **Ship with P1** (same PR, or include review `""`→SUE in P0): if the helper starts returning `""` while review still treats it as model JSON, `run_review_run` can `ValueError` instead of SUE. Live review is Moonshot; still do not leave the Anthropic review path half-wired.

---

## P1 — Empty text is a parse miss (judge wrap)

**Goal:** `_post_judge_anthropic_messages` maps helper `""` → `JudgeParseError` (`judge_empty_text`) so `call_judge_with_optional_retry` runs the existing one retry (D4). Anthropic review maps `""` → `ServiceUnavailableError`.

**Scope — in:** Judge-only wrap; record transport extra on empty-text (including optional `content_block_types` home) so P2 is not skipped by the current `(HTTPError, SUE)` except (`anthropic_review.py` ~331); distinct `parse_error` vs HTTP (D6); retry_count visible on the second miss. Keep existing gateway→direct `_post_judge_with_profile_fallback` (D7 — do not “fix” fallback away).

**Scope — out:** Extra retries; adding a second model; changing retry prompt beyond current schema reminder; raising `JudgeParseError` from `_extract_message_text`.

**Deliverables:** Thinking-only no longer dies as unwrapped SUE on the judge path; one retry attempt recorded; tests for retry-on-empty-text vs no-retry-on-HTTP vs review-path SUE on `""`.

**Depends on:** P0.

---

## P2 — Trace codes

**Goal:** Operators can tell additive `judge_empty_text` from live **`judge_json_invalid`** (`judge_llm_errors.py`) from HTTP without opening thinking signatures in worker logs. Do not rename `judge_json_invalid`.

**Scope — in:** Manifest / transport `parse_error` strings per D6; optional `content_block_types` on judge transport extra (P1 wrap records it); existing `judge_json_contract_staging_metrics` still groups by any `parse_error` (no schema migration). D8: INFO never dumps `signature`; manifest truncated dump unchanged.

**Scope — out:** New tables; stripping signatures from `raw_response_text`; logging full bodies in worker INFO.

**Deliverables:** Failure artifacts distinguishable in DB by D6 code; unit tests on codes; metrics script still runs without a hardcoded old-string filter.

**Depends on:** P1.

---

## P3 — Staging validation & doc sync

**Goal:** Human gate — live `--since` candidate → `outcome` ≥95% **or** residual classified (thinking-only / invalid JSON / other). Extract-only ceiling on the 2026-08-07 window is **94.3%** (D9); do not reopen JSON-contract or add retries to chase 0.7 points (D7).

**Scope — in:** `JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md`; re-run `judge_json_contract_staging_metrics.py` **plus** evidence SQL/script split (text-later vs thinking-only — today’s printer does not split); README + [LIVE_TRAFFIC](../staging-validation/LIVE_TRAFFIC_FINDINGS.md) LT-1 pointer; JTB-Q5 filled from staging.

**Scope — out:** JSON-contract prompt/schema work; LT-2–LT-6; treating 94.3% as hard fail.

**Deliverables:** Filled validation memo with split evidence and D9 ceiling noted; program README status; calibration JTB-Q5 closed.

**Depends on:** P0–P2 deployed to the staging worker.

---

## Open calibration

**JTB-Q5:** thinking-only (8/53) may still fail after one retry — P3 records the rate; do not add retries or a second model without a new findings pass.

**Next step:** **`execution-peer-review`** on `docs/review-pipeline/judge-thinking-blocks/waves/` (P0–P3), then **`phase-execution`** from P0. Live token `judge_json_invalid`; additive code `judge_empty_text` only.
