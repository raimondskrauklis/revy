# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Active phase:** RQ1 (compare API + `base_sha` + diff-first index + AS1 job-create guards).

**Check especially:**

- `compare_commits` in `github_api.py` — 404/rate-limit errors; `base...head` URL
- `base_sha` on revision create from webhook `pull_request.base.sha` (D8)
- `index_mode` at job create only — manual `full`, pipeline `diff`; `run_index_job` reads `job.index_mode`
- Compare fallback → `index_mode=full` + `fallback_reason` on job row
- Deep/critical admin review → full index required (`full_index_required` / `index_mode_mismatch`)
