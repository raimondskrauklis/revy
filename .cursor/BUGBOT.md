# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Active phase:** RQ3 (pipeline trace + read API + purge + G10 in-progress check).

**Check especially:**

- `github_pipeline_trace.py` — runs link index/review/publish; steps + artifacts per O2/O3
- Worker hooks: index, review (retrieve + review), reconcile, judge, publish
- Review artifacts: `prompt`, `raw_response` (always), `parse_report`, retrieval `manifest`
- `GET …/review-runs/{id}/pipeline` — `items_view`, `ensure_revision_access`
- G10: `create_check_run` `in_progress` at pipeline start; finalize on publish/failure
- O8: `pipeline_purge_tasks` + `PIPELINE_RETENTION_DAYS=90` + Celery beat
