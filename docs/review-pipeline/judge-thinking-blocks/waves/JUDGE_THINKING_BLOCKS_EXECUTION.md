# Judge thinking-blocks — execution index

**Authority:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](../JUDGE_THINKING_BLOCKS_FINDINGS.md) · [JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md)

**Prerequisite:** Judge JSON-contract + transport on `main` (manifest `raw_response_text` / `parse_error`, one parse retry) — **satisfied**.

**LOOP:** `P0 → P1 → P2 → P3`. P0 and P1 are **two commits, one PR**. Do not merge P0 without P1.

## LOOP order

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Content-block extract + review `""`→SUE | [P0](./JUDGE_THINKING_BLOCKS_P0_EXECUTION.md) | done (`0fc5b45`) |
| P1 | Judge wrap `judge_empty_text` + transport extra | [P1](./JUDGE_THINKING_BLOCKS_P1_EXECUTION.md) | done (`bf480d7`) |
| P2 | Distinct codes; D8 INFO; metrics grouping | [P2](./JUDGE_THINKING_BLOCKS_P2_EXECUTION.md) | done (`d9fd997`) |
| P3 | Staging validation + split evidence + doc sync | [P3](./JUDGE_THINKING_BLOCKS_P3_EXECUTION.md) | code-complete — human gate pending |

**Locked tokens:** additive `judge_empty_text` only; live JSON-invalid stays **`judge_json_invalid`**. Do not rename.

**Next:** human gate — fill [JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md](../JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md) after P0–P2 is on the staging worker.
