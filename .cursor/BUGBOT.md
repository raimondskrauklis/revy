# Bugbot — review pipeline contract

When reviewing **backend** changes that touch publish / formatter / pipeline / generation lifecycle / judge code, treat these as authoritative:

**Judge input quality (active program):**

- [JUDGE_INPUT_QUALITY_EXECUTION.md](../docs/review-pipeline/judge/waves/JUDGE_INPUT_QUALITY_EXECUTION.md) — P0–P5 scope, gates, J-8 patch reload
- [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../docs/review-pipeline/judge/JUDGE_INPUT_INVESTIGATION_FINDINGS.md) — J-* gaps, find→verify thesis
- [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../docs/review-pipeline/judge/JUDGE_INPUT_QUALITY_GENERAL_PLAN.md) — phase goals

**Review generation lifecycle (shipped on `main`):**

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

**Program:** Judge input quality on feature branch `feat/judge-input-quality` — scoped judge context, verifier prompts, Moonshot PR body fetch. Review generation lifecycle shipped on `main` via PR #54.

**Finding resolution (shipped on `main`):**

- [FINDING_RESOLUTION_EXECUTION.md](../docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_EXECUTION.md) — P0–P5 scope, closure passes, FR-Q12
- [FINDING_RESOLUTION_FINDINGS.md](../docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_FINDINGS.md) — FR-* gaps, multi-pass model
- [FINDING_RESOLUTION_GENERAL_PLAN.md](../docs/review-pipeline/finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md) — phase goals

**Judge JSON contract (active program):**

- [JUDGE_JSON_CONTRACT_EXECUTION.md](../docs/review-pipeline/judge-json-contract/waves/JUDGE_JSON_CONTRACT_EXECUTION.md) — P0–P5 scope, structured output, observability
- [JUDGE_JSON_CONTRACT_FINDINGS.md](../docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) — JC-* gaps, staging metrics
- [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_GENERAL_PLAN.md) — phase goals
