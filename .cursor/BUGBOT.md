# Bugbot — review pipeline contract

**Active program:** finding-resolution-closure-scope — HEAD path-gone hygiene (Pass 1b + Pass 2 widen), FR-CS1/6/7, CS-Q6 manifest honesty.

When reviewing **backend** changes that touch resolution metrics, finding closure, compare patches, publish formatter, or pipeline trace, treat these as authoritative:

- [FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md](../docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md) — LOOP C0–C4, locked CS-Q*
- [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) — FR-CS gaps, three-track architecture, CS-Q7 HEAD truth
- [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) — phase goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
