# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model
- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — distilled Custom Instructions + **Pass 1/2 output format** (Deferred table on pass 2+)

**Active phase:** RQ8 complete — program shipped on branch; human gate AS2 + migration `0026` before tag `review-quality-v1`.

**RQ6–RQ8 shipped on PR #50:**

- RQ6: `resolution_status` on synchronize (`github_resolution_metrics.py`)
- RQ7: G3 split bodies + G9 prose + `summary_json` (`github_publish_formatter.py`)
- RQ8: doc sync; full unit gate green
