# Bugbot — review pipeline contract

**Active program:** pr-summary-rollup — persisted PR lifetime rollup + this-push manifest on every publish.

When reviewing **backend** changes for PSR, treat these as authoritative:

- [PR_SUMMARY_ROLLUP_EXECUTION.md](../docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_EXECUTION.md) — P0–P3 LOOP index
- [PR_SUMMARY_ROLLUP_FINDINGS.md](../docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_FINDINGS.md) — manifest v1, PSR-Q1–Q10, post-collapse compute locks
- [PR_SUMMARY_ROLLUP_GENERAL_PLAN.md](../docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_GENERAL_PLAN.md) — P0–P3 goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
