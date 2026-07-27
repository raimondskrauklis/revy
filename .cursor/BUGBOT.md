# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model
- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — distilled Custom Instructions + **Pass 1/2 output format** (Deferred table on pass 2+)

**Active phase:** RQ5 next (evidence + grounding judge). RQ4 shipped including pass-2 deferred fixes.

**RQ5 check especially:**

- `evidence_snippet` at parse from diff hunk or top retrieval chunk
- `_build_judge_prompt` grounding instruction (E2)
- Judge dismissed → `resolved` group state
- Pipeline judge artifacts per candidate (RQ3 hooks)
