# Bugbot — review pipeline contract

**Active program:** revy-review-dogfood — cross-repo operator trust: revision ingest idempotency, thread resolve taxonomy, resolution stamp, HEAD suppression.

When reviewing **backend** changes for RR-W1, treat these as authoritative:

- [REVY_REVIEW_DOGFOOD_EXECUTION.md](../docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_EXECUTION.md) — R0–R5 LOOP index
- [REVY_REVIEW_DOGFOOD_FINDINGS.md](../docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_FINDINGS.md) — RR-DG* gaps; RR-Q5 app dedupe; RR-DG4 `stale_closure_blocked`
- [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md) — R0–R5 goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
