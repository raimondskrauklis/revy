# Bugbot — review pipeline contract

When reviewing **backend** changes that touch review-quality code, treat these as authoritative (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — RQ0–RQ9 scope, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model
- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT (Deferred on pass 2+)
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries

**Program:** review-quality **merged to `main`** (PR [#50](https://github.com/raimondskrauklis/revy/pull/50)); **RQ9 hardening** active on `docs/agent-work`.

**Human gate (before tag `review-quality-v1`):** staging `alembic upgrade head` through `0026`; AS2 autostart e2e — [REVIEW_QUALITY_EXECUTION.md § RQ8](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md).

**Agent workflow quick ref:** [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md)
