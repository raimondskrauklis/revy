# Judge JSON contract — general plan

**Baseline:** [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) (staging + code, 2026-07-28)  
**Prerequisite:** [finding-resolution](../finding-resolution/README.md) merged to `main`; judge input quality + R5 on `main`.

**Thesis:** Judge failures are **contract + prompt** problems, not Moonshot or RG-6. Ship observability first, then snippet-first prompts, then API structured output on the existing RTU Messages path — keep RG-6 withhold (JC-D1).

**Gap IDs:** **JC-*** in findings; **P0–P5** = program phases below.

**Locked:** JC-D1–D6; R5-Q3 escalation gate unchanged; Moonshot review JSON unchanged (JC-D3); no `llm.rdi.services` worker proxy (JC-D2); implementation branch off `main` after finding-resolution (JC-D6).

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` per phase — parse helper, prompt tiers, manifest fields, `judge_finding` mock paths; verification judge (`github_finding_closure.py`) shares judge client contract.
- **Trace:** Judge manifest records outcome, raw body, `parse_error`, `file_patch_chars`; no `raw_response=null` on HTTP 200 after P1.
- **Tenancy / publish:** workspace scope unchanged; RG-6 withhold without outcome row — do not relax.
- **i18n:** backend-only — no new UI strings.
- **Bedrock:** same schema/parse path as Anthropic when `call_judge_llm` routes to Bedrock.

---

## P0 — API smoke & structured-output feasibility (JC-5)

**Goal:** Confirm RTU gateway (`ANTHROPIC_BASE_URL` `/v1/messages`) accepts judge `json_schema` before production wiring.

**Scope — in:** Extend `test_anthropic_judge_gateway.py` — plain prompt, `--structured` schema, optional large-prompt replay; document pass/fail matrix in findings addendum or execution gate.

**Scope — out:** Worker integration; manifest schema changes.

**Deliverables:** Runnable smoke script; locked decision: structured output on/off per path (gateway vs direct fallback).

**Depends on:** Local/staging RTU credentials in `backend/.env`.

---

## P1 — Failure observability (JC-2, G1)

**Goal:** Every judge candidate attempt leaves an auditable trace — success or failure body.

**Scope — in:** Manifest fields `raw_response_text` + `parse_error` (keep parsed `raw_response` on success); structured log on `github_finding_judge_failed`; verification-judge artifacts same shape.

**Scope — out:** Changing parse logic or prompts; RG-6 behavior.

**Deliverables:** Pipeline manifest always post-mortem-able from DB; unit tests on failure artifact path.

**Depends on:** None (ship first for metrics — JC-D5).

---

## P2 — Snippet-first prompt policy (JC-3, G3)

**Goal:** Restore find→verify context size — ~1k prompts when snippet exists; patch only as fallback.

**Scope — in:** Skip `file_patch` block when `evidence_snippet` present; tiered fallback for line-less / thin evidence; lower patch cap (~2k) when patch used; same rules for discovery + verification judge prompt builders.

**Scope — out:** Structured output API; Moonshot ingest.

**Deliverables:** Prompt p50 ≤2k when anchored + snippet; `file_patch_chars` usually null when snippet exists; unit tests per tier.

**Depends on:** P1 (measure prompt chars in manifest before/after).

---

## P3 — Structured output + parse fallback (JC-1, JC-4, G2, G4)

**Goal:** Schema-guaranteed judge JSON on Anthropic Messages API with safe fallback.

**Scope — in:** `output_config.format` / `json_schema` on `judge_finding()` (gateway + direct); shared `parse_llm_json_object` — fence strip, first-object extract; `parse_judge_outcome` unchanged enum gate; Bedrock parity if provider supports equivalent.

**Scope — out:** Moonshot changes; unbounded retries.

**Deliverables:** Judge path at Level-3 JSON where P0 confirmed; fallback parse when structured output unavailable; unit tests for helper + happy path.

**Depends on:** P0 (feasibility), P1.

---

## P4 — Targeted retry (G5)

**Goal:** Recover residual parse failures without retry storms.

**Scope — in:** Max **one** retry per candidate with validation error + schema reminder in follow-up prompt; only when P3 still fails in smoke/staging sample.

**Scope — out:** Second model; changing outcome enum.

**Deliverables:** Retry only on parse/contract failure; metrics field `retry_count` in manifest optional; skip phase if P3 staging sample is clean.

**Depends on:** P3.

---

## P5 — Staging validation & doc sync (JC-6, G8)

**Goal:** Human gate proving ≥95% judge candidate → outcome row on dogfood PRs.

**Scope — in:** `JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md` — success rate, prompt size, RG-6 warning rate, SQL repro; README + program index status; Greptile/Bugbot wiring if execution adds `.greptile` entries.

**Scope — out:** Moonshot parse_report changes; finding-resolution closure.

**Deliverables:** Filled validation memo on staging; program README marked done; incident cross-links updated.

**Depends on:** P1–P4 deployed to staging.

---

## Open calibration

**P0 smoke:** whether RTU/Azure backend honors `output_config.format` on the Revy gateway profile — if not, P3 ships parse fallback + P2 only until provider upgrades.

**Next step:** **`create-execution-plan`** → `waves/JUDGE_JSON_CONTRACT_EXECUTION.md` + P0–P5 execution files.
