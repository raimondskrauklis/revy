# Bugbot — review pipeline contract

When reviewing **backend** changes that touch publish / formatter / pipeline code, treat these as authoritative:

**GitHub surface (active program):**

- [GITHUB_SURFACE_EXECUTION.md](../docs/review-pipeline/post-review-quality/GITHUB_SURFACE_EXECUTION.md) — P0–P4 scope, gates, dogfood rubric
- [POST_REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/post-review-quality/POST_REVIEW_QUALITY_FINDINGS.md) — platform baseline, track A/B
- [POST_REVIEW_QUALITY_GENERAL_PLAN.md](../docs/review-pipeline/post-review-quality/POST_REVIEW_QUALITY_GENERAL_PLAN.md) — phase goals

**Review-quality engine (shipped on `main`):**

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — RQ0–RQ9 routes, schema
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries

**Program:** GitHub surface on feature branch `feat/revy-github` — Greptile-comparable L1–L3 on PR branch pushes (pre-merge autostart). **Status:** P0–P4 code + doc sync shipped; dogfood rows pending on real PR push.
