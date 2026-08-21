# Judge thinking-blocks — program index

**Status:** findings + general plan (2026-08-21) — execution not started.  
**Problem:** RTU `claude-sonnet-5` returns thinking-first Messages `content`; Revy reads only `content[0].text` and records `Anthropic response invalid`. 45/53 live misses already had a later `text` block.

**Not in scope:** Moonshot review JSON; RG-6 withhold; Voyage embeddings; RCX truncation; review-attempt `wait_ms` (LT-2).

| Doc | Purpose |
|-----|---------|
| [JUDGE_THINKING_BLOCKS_FINDINGS.md](./JUDGE_THINKING_BLOCKS_FINDINGS.md) | Baseline — live-window evidence, adapter gap, locked decisions |
| [JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md](./JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md) | P0–P3 phases (general — no execution steps) |

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
