# Bugbot RQ1 clean gate
_Exported on 27/07/2026 at 14:57:03 EEST from Cursor (3.13.10)_

---

**User**

Full Repository Path: /Users/raimonds.krauklis/projects/revy
Diff: uncommitted changes

---

**Cursor**

Reviewing RQ1 changes against the execution contract and tracing index/review code paths.


## Compare API omits files past limit

`backend/app/integrations/github_api.py:171-217` · Severity: medium

<details open>
<summary>Description</summary>

`compare_commits` issues a single compare request and treats the returned `files` array as complete. GitHub caps that list at 300 entries, so diff-mode indexing on larger PRs will only chunk/embed a subset of changed paths while still marking the job completed with no truncation signal or fallback.

</details>

## Cross-tenant p50 duration leak

`backend/app/services/github_indexing.py:242-265` · Severity: low

<details open>
<summary>Description</summary>

`_set_full_mode_warning` computes the p50 full-index duration from all completed full jobs in the database, not scoped to the current job's `workspace_id`, and writes that value into the job's `warning_message`.

</details>

