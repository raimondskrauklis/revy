# Bugbot — review-quality dogfood

When reviewing **backend** changes on `feat/review-quality`, treat these docs as the authoritative contract (not generic advice):

- [REVIEW_QUALITY_EXECUTION.md](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md) — active RQ phase, locked schema, routes, gates
- [REVIEW_QUALITY_FINDINGS.md](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md) — locked Q# and storage model

**Active phase:** RQ2 (diff-first review prompt + scoped retrieval + D10 fingerprint + parse_report).

**Check especially:**

- `_build_review_prompt` — metadata → changed files → unified diff (128KB D5) → supplemental (D6 caps)
- `compare_commits` re-called in review worker (not index job row for patches)
- D5 truncate: `diff_truncated`, `omitted_files[]` in retrieval manifest
- Scoped retrieval: changed-file chunks only in diff mode; D7 test exclusion
- `compute_fingerprint` — D10: `title` + `start_line_key`, message excluded
- `parse_finding_rows` — `parse_report` with drop reasons (persisted RQ3)
