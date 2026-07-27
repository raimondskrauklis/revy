# Bugbot RQ1 gate
_Exported on 27/07/2026 at 14:20:07 EEST from Cursor (3.13.10)_

---

**User**

Full Repository Path: /Users/raimonds.krauklis/projects/revy
Diff: uncommitted changes
Custom Instructions: RQ1 — verify create_review_run uses get_latest_completed_index_job AND index_job_in_progress guard.

---

**Cursor**

Reviewing RQ1 changes against the contract, focusing on `create_review_run` guards and related code paths.


## Missing index_job_in_progress import

`backend/app/services/github_review.py:93-101` · Severity: high

<details open>
<summary>Description</summary>

`create_review_run` calls `index_job_in_progress` but never imports it from `github_indexing`, so every review create (admin API, pipeline autostart via `prepare_review_after_index`) raises `NameError` instead of enforcing the RQ1 `index_in_progress` guard.

</details>

