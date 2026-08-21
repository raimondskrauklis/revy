# Judge thinking-blocks — general plan

**Baseline:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md) (2026-08-21)  
**Prerequisite:** Judge JSON-contract + transport on `main` (manifest `raw_response_text` / `parse_error`, one parse retry).

**Thesis:** Live 62.4% judge persistence is an **extract bug**, not a new JSON-contract wave. Read all Messages `text` blocks; classify empty text as `JudgeParseError` so the existing retry can fire; keep RG-6.

**Locked:** JTB-D1–D8. **Open calibration:** JTB-Q5 (whether thinking-only recovers on retry) — measured in P3, does not change direction.

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` — thinking-first + text-later, thinking-only, legacy `content[0].text`, multiple text blocks; judge retry classification; Anthropic review extract shares the helper.
- **Lineage:** Distinct `parse_error` codes (D6); optional `content_block_types` on transport extra — never log thinking `signature`.
- **Coverage:** Text-later (45) vs thinking-only (8) called out in tests and validation, not averaged away.
- **i18n:** Backend-only — no new UI strings.
- **Publish:** RG-6 unchanged (D7). Bedrock extract out of scope.

---

## P0 — Content-block extract (foundations)

**Goal:** `_extract_message_text` returns concatenated non-empty `text` blocks; thinking-first + text-later succeeds.

**Scope — in:** Shared helper (D1–D3) used by judge HTTP and Anthropic `complete_review`; fixtures matching live RTU shape; keep HTTP / non-JSON as `ServiceUnavailableError` (D5).

**Scope — out:** Retry taxonomy; structured output; Moonshot; Bedrock.

**Deliverables:** Text-later payloads yield the assistant `text` string; legacy single-block tests still pass; unit coverage for skip-thinking / concat.

**Depends on:** None.

---

## P1 — Empty text is a parse miss

**Goal:** No-text after extract raises `JudgeParseError` so `call_judge_with_optional_retry` runs the existing one retry (D4).

**Scope — in:** Thinking-only and tool-use-only → `JudgeParseError` (e.g. `judge_empty_text`); distinct `parse_error` vs HTTP invalid body (D6); retry_count visible on the second miss.

**Scope — out:** Extra retries; second model; changing retry prompt beyond current schema reminder.

**Deliverables:** Thinking-only no longer dies as `ServiceUnavailableError`; one retry attempt recorded; tests for retry-on-empty-text vs no-retry-on-HTTP.

**Depends on:** P0.

---

## P2 — Trace codes

**Goal:** Operators can tell thinking-first empty-text from invalid JSON from HTTP without opening raw signatures.

**Scope — in:** Manifest / transport `parse_error` strings per D6; optional `content_block_types` on judge transport extra; existing `judge_json_contract_staging_metrics` still groups failures (no schema migration).

**Scope — out:** New tables; logging full `raw_response_text` in worker INFO.

**Deliverables:** Failure artifacts distinguishable in DB; unit tests on codes; metrics script still runs (adapt only if a code rename would break counts — keep backward-compatible grouping).

**Depends on:** P1.

---

## P3 — Staging validation & doc sync

**Goal:** Human gate — live `--since` candidate → `outcome` ≥95% after deploy, or documented residual (thinking-only / invalid JSON).

**Scope — in:** `JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md`; re-run `judge_json_contract_staging_metrics.py`; split text-later vs thinking-only in evidence; README + [LIVE_TRAFFIC](../staging-validation/LIVE_TRAFFIC_FINDINGS.md) LT-1 pointer; JTB-Q5 filled from staging.

**Scope — out:** JSON-contract prompt/schema work if extract already hits ≥95%; LT-2–LT-6.

**Deliverables:** Filled validation memo; program README status; calibration JTB-Q5 closed.

**Depends on:** P0–P2 deployed to the staging worker.

---

## Open calibration

**JTB-Q5:** thinking-only (8/53) may still fail after one retry — P3 records the rate; do not add retries or a second model without a new findings pass.

**Next step:** **`create-execution-plan`** for P0–P3 under `docs/review-pipeline/judge-thinking-blocks/waves/`.
