# Bugbot — review pipeline contract

When reviewing **backend** changes that touch publish / formatter / pipeline code, treat these as authoritative:

**GitHub surface hardening (active program):**

- [GITHUB_SURFACE_HARDENING_EXECUTION.md](../docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_EXECUTION.md) — P0–P4 scope, gates, dogfood rubric
- [GITHUB_SURFACE_HARDENING_FINDINGS.md](../docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md) — GH-* gaps, Option A resolve
- [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](../docs/review-pipeline/github-surface-hardening/GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md) — phase goals

**Review-quality engine (shipped on `main`):**

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — RQ0–RQ9 routes, schema
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries

**Program:** GitHub surface hardening on feature branch `feat/github-surface-hardening` — thread auto-resolve (GH-1), GraphQL scale, publish test harness.
