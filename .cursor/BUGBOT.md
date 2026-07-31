# Bugbot — review pipeline contract

**Active program:** judge-transport-reliability — worker-visible judge transport logging + gateway→direct fallback.

When reviewing **backend** changes that touch judge LLM transport, profile fallback, or failure logging, treat these as authoritative:

- [JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](../docs/review-pipeline/judge/waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md) — T0–T3 LOOP index
- [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) — JT gaps, locked JT-Q1–Q6
- [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md) — T0–T3 goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
