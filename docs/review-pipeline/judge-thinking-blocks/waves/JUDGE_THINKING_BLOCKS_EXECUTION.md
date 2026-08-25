# Judge thinking-blocks — execution index

**Authority:** [JUDGE_THINKING_BLOCKS_FINDINGS.md](../JUDGE_THINKING_BLOCKS_FINDINGS.md) · [JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md)

**Prerequisite:** Judge JSON-contract + transport on `main` (manifest `raw_response_text` / `parse_error`, one parse retry) — **satisfied**.

**LOOP:** `P0 → P1 → P2 → P3`. P0 and P1 are **two commits, one PR**. Do not merge P0 without P1.

## LOOP order

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Content-block extract + review `""`→SUE | [P0](./JUDGE_THINKING_BLOCKS_P0_EXECUTION.md) | done |
| P1 | Judge wrap `judge_empty_text` + transport extra | [P1](./JUDGE_THINKING_BLOCKS_P1_EXECUTION.md) | pending |
| P2 | Distinct codes; D8 INFO; metrics grouping | [P2](./JUDGE_THINKING_BLOCKS_P2_EXECUTION.md) | pending |
| P3 | Staging validation + split evidence + doc sync | [P3](./JUDGE_THINKING_BLOCKS_P3_EXECUTION.md) | pending |

**Locked tokens:** additive `judge_empty_text` only; live JSON-invalid stays **`judge_json_invalid`**. Do not rename.

**Next:** `phase-execution` from [P0](./JUDGE_THINKING_BLOCKS_P0_EXECUTION.md). Execution-peer-review pass 1: **BLOCK no.**
