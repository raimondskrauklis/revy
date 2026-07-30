# Bugbot — review pipeline contract

**Active program:** finding-resolution-dogfood — FR-DG1/FR-DG2 **closed PASS** (wave C [#69](https://github.com/raimondskrauklis/revy/pull/69) Track C); MR-DG1 open.

When reviewing **backend** changes that touch publish / formatter / pipeline / generation lifecycle / judge code, treat these as authoritative:

- [FINDING_RESOLUTION_DOGFOOD_EXECUTION.md](../docs/review-pipeline/finding-resolution-dogfood/waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md) — LOOP P0–P3, deploy cadence, FR-DG* locks
- [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) — FR-DG1/2 closed PASS; MR-DG1 gaps from PSA #63
- [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md) — phase goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
