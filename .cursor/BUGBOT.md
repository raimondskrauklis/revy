# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model
- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — distilled Custom Instructions + **Pass 1/2 output format** (Deferred table on pass 2+)

**Active phase:** RQ6 next (resolution metrics). RQ5 shipped — evidence snippets + grounding judge.

**RQ6 check especially:**

- `resolution_status` on synchronize: `judge_dismissed` | `addressed` | `still_open`
- Hook after `_append_revision` flush, before `maybe_enqueue_pipeline_for_revision`
- `addressed` = compare touches file_path + line region from latest finding
