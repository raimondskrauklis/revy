# Bugbot — review pipeline contract

When reviewing **backend** changes that touch publish / formatter / pipeline / generation lifecycle code, treat these as authoritative:

**Review generation lifecycle (active program):**

- [REVIEW_GENERATION_LIFECYCLE_EXECUTION.md](../docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_EXECUTION.md) — P0–P5 scope, gates, dogfood rubric
- [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](../docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) — RG-* gaps, snapshot semantics
- [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](../docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md) — phase goals

**GitHub surface hardening (shipped on `main`):**

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

**Program:** Review generation lifecycle on feature branch `feat/review-generation-lifecycle` — HEAD-gated publish, supersede in-flight generations, full surface flush, optional coalesce. GitHub surface hardening (thread auto-resolve, GraphQL scale) shipped on `main` via PR #53.
