# Judge thinking-blocks — program index

**Status:** **Closed.** P0–P3 on [#103](https://github.com/raimondskrauklis/revy/pull/103). S0–S3 [#106](https://github.com/raimondskrauklis/revy/pull/106). S4 Deep Fable [#108](https://github.com/raimondskrauklis/revy/pull/108) after [#107](https://github.com/raimondskrauklis/revy/pull/107) — **close #108 without merge**. D6: live `judge_json_invalid` stays; additive `judge_empty_text` only.  
**Problem:** RTU `claude-sonnet-5` returns thinking-first Messages `content`; Revy reads only `content[0].text` and records `Anthropic response invalid`. 45/53 live misses already had a later `text` block.

**Not in scope:** Moonshot review JSON; RG-6 withhold; Voyage embeddings; RCX truncation; review-attempt `wait_ms` (LT-2).

| Doc | Purpose |
|-----|---------|
| [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md) | Baseline — live-window evidence, adapter gap, locked decisions |
| [JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md](./JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md) | P0–P3 phases (general — no execution steps) |
| [waves/JUDGE_THINKING_BLOCKS_EXECUTION.md](./waves/JUDGE_THINKING_BLOCKS_EXECUTION.md) | LOOP index |
| [JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md](./JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md) | Operator staging gate (P3 human sign-off) |
| [Architecture peer review](./reviews/architecture-peer-review/README.md) | Pass index — findings + general plan vs codebase |
| [Execution peer review](./reviews/execution-peer-review/README.md) | Pass index — P0–P3 waves vs codebase |

**Parent evidence:** [LIVE_TRAFFIC_FINDINGS.md](../staging-validation/LIVE_TRAFFIC_FINDINGS.md) LT-1.

**Related programs**

| Program | Link |
|---------|------|
| Judge JSON contract (shipped, persistence still FAIL) | [judge-json-contract](../judge-json-contract/README.md) |
| Judge transport reliability (closed partial) | [judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) |
| Judge input quality (shipped) | [judge/README.md](../judge/README.md) |

**Related code**

| Area | Path |
|------|------|
| Content extract | `backend/app/integrations/anthropic_review.py` (`_extract_message_text`) |
| Judge retry | `backend/app/services/github_finding_judge.py` (`call_judge_with_optional_retry`) |
| Parse JSON | `backend/app/integrations/judge_llm_errors.py` (`JudgeParseError`, `parse_judge_payload`) |
| Metrics | `backend/scripts/judge_json_contract_staging_metrics.py` |

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Content-block extract + review `""`→SUE | [P0](./waves/JUDGE_THINKING_BLOCKS_P0_EXECUTION.md) | done (`0fc5b45`) |
| P1 | Judge wrap `judge_empty_text` + transport extra | [P1](./waves/JUDGE_THINKING_BLOCKS_P1_EXECUTION.md) | done (`bf480d7`) |
| P2 | Distinct codes; D8 INFO; metrics grouping | [P2](./waves/JUDGE_THINKING_BLOCKS_P2_EXECUTION.md) | done (`d9fd997`) |
| P3 | Staging validation + split evidence + doc sync | [P3](./waves/JUDGE_THINKING_BLOCKS_P3_EXECUTION.md) | done — S0–S4 signed in [validation memo](./JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md) |

P0 and P1 already shipped together on [#103](https://github.com/raimondskrauklis/revy/pull/103).

**Next:** none — program closed. Do not merge [#108](https://github.com/raimondskrauklis/revy/pull/108).
