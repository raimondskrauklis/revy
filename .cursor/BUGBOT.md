# Bugbot — review pipeline contract

**Active program:** free-plan-credits — credit tracking on workspaces (completed_review_runs + review_run_limit columns), open GitHub installation gate, atomic credit increment, frontend counter display.

When reviewing **backend** changes for this program, treat these as authoritative:

- [FREE_PLAN_CREDITS_P0_EXECUTION.md](../docs/free-plan-credits/FREE_PLAN_CREDITS_P0_EXECUTION.md) — P0 LOOP (schema, migration, open install gate)
- [FREE_PLAN_CREDITS_FINDINGS.md](../docs/free-plan-credits/FREE_PLAN_CREDITS_FINDINGS.md) — DB snapshot, schema design, edge cases, decisions registry
- [FREE_PLAN_CREDITS_GENERAL_PLAN.md](../docs/free-plan-credits/FREE_PLAN_CREDITS_GENERAL_PLAN.md) — P0–P2 goals and deliverables

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries