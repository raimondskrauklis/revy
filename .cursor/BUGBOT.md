# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Active phase:** RQ0 (schema migration `0026` + review-context wiring).

**Check especially:**

- Migration `0026` matches execution table (columns, FKs, `ON DELETE CASCADE` on `pipeline_runs.workspace_id`)
- New enums: `GitHubIndexMode`, `PipelineStepType`, `PipelineArtifactKind`, `ResolutionStatus`
- Hand-written Alembic only — no autogenerate
