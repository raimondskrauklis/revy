# Bugbot RQ1 final gate
_Exported on 27/07/2026 at 14:18:35 EEST from Cursor (3.13.10)_

---

**User**

Full Repository Path: /Users/raimonds.krauklis/projects/revy
Diff: uncommitted changes
Custom Instructions: RQ1 final gate — chunk delete after embed, stale diff paths, get_latest_completed_index_job for review.

---

**Cursor**

Reviewing RQ1 changes against the execution contract and tracing index/review code paths.


## Review allowed during active indexing

`backend/app/services/github_review.py:93-102` · Severity: high

<details open>
<summary>Description</summary>

Switching `create_review_run` to `get_latest_completed_index_job` drops the guard that blocked review when the newest index job was still `pending` or `processing`. A manual `POST …/review` can now succeed using an older completed index while a newer diff/full job is mutating `github_code_chunks` for the same revision.

</details>

