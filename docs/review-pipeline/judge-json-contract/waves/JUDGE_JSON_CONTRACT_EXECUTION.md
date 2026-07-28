# Judge JSON contract — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [JUDGE_JSON_CONTRACT_FINDINGS.md](../JUDGE_JSON_CONTRACT_FINDINGS.md) · **General plan:** [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md)

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../../REVIEW_PIPELINE_FINDINGS.md) R5-Q3 · [judge input quality](../../judge/JUDGE_INPUT_QUALITY_GENERAL_PLAN.md) find→verify thesis · JC-D1–D6 (findings)

**Goal:** ≥95% judge candidates persist a valid `outcome` row on staging dogfood PRs; manifest always records success or failure body; prompt p50 ≤2k chars when snippet + line anchor present.

**Branch:** `feat/judge-json-contract` from `main`

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5
each phase: implement → pytest gate → Bugbot → local commit (operator pushes + validates staging)
```

**Operator LOOP:** Agent stops at **phase boundary** for local work; `phase-execution` skill pushes per phase after gate + Bugbot. Fill [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) after deploy (P5 human gate; stub may start in P4.0).

**No migrations** in this program — schema changes are manifest JSON fields only (P1).

## Decisions locked for execution

- **JC-D1:** RG-6 withhold stays — no escalation inline publish without `github_finding_judge_outcomes` row.
- **JC-D2:** RTU/direct Anthropic Messages path only — no `llm.rdi.services` worker proxy.
- **JC-D3:** Moonshot `parse_report` / review JSON unchanged.
- **JC-D4:** Snippet-first prompt — skip `file_patch` when `evidence_snippet` present; patch fallback ~2k cap.
- **JC-D5:** Ship failure observability (P1) before structured output (P3).
- **JC-D6:** Implementation branch off `main` after finding-resolution (#57).
- **Judge outcome enum:** `upheld` | `dismissed` | `modified` — `parse_judge_outcome` unchanged.
- **Discovery + verification:** same judge client contract (`call_judge_llm` → `judge_finding`); verification artifacts share P1 manifest shape.
- **P0 gate:** structured output feasibility matrix locked before P3 wires API schema.
- **P4 skip rule:** if P3 staging sample shows ≥95% parse success, P4 ships doc-only skip note in validation memo — no retry wiring.

## LOOP order

| Phase | Focus | Execution | Commit | Status |
|-------|--------|-----------|--------|--------|
| P0 — API smoke | Structured-output feasibility + smoke flags | [JUDGE_JSON_CONTRACT_P0_EXECUTION.md](./JUDGE_JSON_CONTRACT_P0_EXECUTION.md) | `b7cadcc` | done |
| P1 — Observability | `raw_response_text` + `parse_error` on manifest | [JUDGE_JSON_CONTRACT_P1_EXECUTION.md](./JUDGE_JSON_CONTRACT_P1_EXECUTION.md) | — | pending |
| P2 — Snippet-first | Prompt tiers, lower patch cap | [JUDGE_JSON_CONTRACT_P2_EXECUTION.md](./JUDGE_JSON_CONTRACT_P2_EXECUTION.md) | — | pending |
| P3 — Structured output | `json_schema` + `parse_llm_json_object` fallback | [JUDGE_JSON_CONTRACT_P3_EXECUTION.md](./JUDGE_JSON_CONTRACT_P3_EXECUTION.md) | — | pending |
| P4 — Targeted retry | Max 1 retry on parse failure | [JUDGE_JSON_CONTRACT_P4_EXECUTION.md](./JUDGE_JSON_CONTRACT_P4_EXECUTION.md) | — | pending |
| P5 — Staging + docs | Validation memo, program closeout | [JUDGE_JSON_CONTRACT_P5_EXECUTION.md](./JUDGE_JSON_CONTRACT_P5_EXECUTION.md) | — | pending |

**Peer review:** execution-peer-review complete (2026-07-28) — P1 integration-layer + P4.4 skip fixes applied.

**P0 calibration lock:** If RTU gateway rejects `output_config.format`, P3 ships `parse_llm_json_object` + P2 only until provider upgrade — document matrix in P0 gate output.
