# Review quality — architecture peer review

**Date:** 2026-07-27 · **Scope:** all files in `review-quality/` cross-checked against backend + reviewer frontend.

**Verdict:** Baseline diagnosis is **accurate**; slice structure is **sound**. Dependency errors and underspecified migrations below must be locked **before** `create-execution-plan`.

**Related:** [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) · [REVIEW_QUALITY_GENERAL_PLAN.md](./REVIEW_QUALITY_GENERAL_PLAN.md)

---

## What the docs get right (verified)

| Claim | Code evidence |
|-------|---------------|
| Full-repo tarball index, no diff/compare | `run_index_job` → `iter_indexable_files` after tarball extract (`github_indexing.py`) |
| Review = global RAG, no unified diff | `_build_review_prompt` — title + chunk bodies only (`github_review.py`) |
| 3 lenses × top 10, cap 30 | `SEARCH_LENSES`, `TOP_K_PER_QUERY`, `CONTEXT_CHUNK_CAP` |
| Judge = text metadata only | `_build_judge_prompt` — no snippet (`github_finding_judge.py`) |
| Publish = table; same body check + comment | `build_summary_markdown` → `update_check_run` + `create_issue_comment` |
| Fingerprint includes message → smoke #44 dupes | `compute_fingerprint(..., message=...)` (`github_finding_reconcile.py`) |
| No `base_sha`, no `index_mode`, no pipeline tables | `GitHubPullRequestRevisionORM` — `head_sha` only; webhook drops `base.sha` |
| No `content_hash`, `evidence_snippet`, `resolution_status` | Models confirmed |
| Autostart wiring exists (R8) | `github_tasks.py` → `maybe_enqueue_pipeline_for_revision(..., autostart)`; migration `0017`; `ReviewSettingsPage` |
| `items_view` is right read permission | `installation_review.py` pattern |
| R8 prerequisite on `main` | PR #31 merged 2026-07-26 |

`REVIEW_QUALITY_FINDINGS.md` “what exists today” is a **faithful** picture of the codebase.

---

## Critical gaps — locked resolutions (pre-execution)

### 1. R5 metrics vs R7 human dismiss — **not shipped**

**Problem:** R5/M1 assumed R7 dismiss/ack UI. [R7 execution](../waves/REVIEW_PIPELINE_R7_EXECUTION.md) explicitly deferred dismiss/ack. No dismiss API; no reviewer UI. [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) “shipped (UI)” is **wrong**.

**Locked (M2):** v1 `resolution_status` uses **diff heuristic + judge-dismissed only**:

| Status | v1 source |
|--------|-----------|
| `addressed` | Diff touches `file_path` + line region on next revision |
| `still_open` | Default when group still active and region unchanged |
| `judge_dismissed` | Group `state=resolved` from judge outcome (not human) |

**Human dismiss** → defer to **R7.6** follow-up (small API + reviewer action). G9 prose uses `addressed` + `judge_dismissed` counts only in v1.

---

### 2. D10 fingerprint — **lock canonical formula**

**Problem:** Locked D10 omitted `workspace_id` / `pull_request_id`; `start_line` lives on `github_findings`, not groups; fingerprint change orphans open-PR groups.

**Locked (D10 full):**

```text
sha256(workspace_id SEP pull_request_id SEP file_path SEP category SEP title SEP start_line_key)
```

| Field | Rule |
|-------|------|
| `title` | From reconciled group title (trimmed) |
| `start_line_key` | Latest finding `start_line` for group at reconcile time, or `"0"` if null |
| `message` | **Excluded** |
| `workspace_id`, `pull_request_id` | **Retained** (uniqueness per PR) |

**Migration behavior (D10-M):** No backfill. On deploy, next reconcile on each open PR may create **new** groups for same logical issue (old + new fingerprint). Accept for v1; D10 reduces future dupes. Optional: one-time supersede pass in execution if dogfood noise is high.

---

### 3. D8 `base_sha` — webhook has it, ingestion drops it

**Verified:** `_extract_pr_fields` reads `base` dict but persists only `base_ref`, not `base.sha`.

**Locked:** Add `base_sha` on `github_pull_request_revisions`; populate from webhook `pull_request.base.sha` at revision create; compare uses stored `base_sha` + `head_sha`.

---

### 4. AS2 autostart — **staging e2e gate**, not assumed code bug

**Verified:** R8 autostart implemented with unit tests (`test_github_tasks_autostart.py`, `test_review_pipeline.py`). Smoke #44 used `@revy review`, not autostart.

**Locked (AS2):** Reword as **staging verification gate**: migrations `0017`–`0018`, worker queues, toggle on → `opened`/`synchronize` runs full pipeline without command. Fix code only if gate fails.

---

### 5. Compare fallback → `full` must be **loud**

**Locked (D13-F):** On compare failure → `index_mode=full` **and**:
- Manifest `fallback_reason`
- GitHub publish **footer + check summary** warning (not manifest-only)
- Optional: skip autostart on repos above `max_index_files` when fallback would trigger

---

### 6. O8 retention purge — **no Celery beat today**

**Locked (O8):** Execution subphase picks infra: Celery beat schedule **or** existing maintenance worker pattern. Purge `github_pipeline_*` older than retention; log counts.

---

### 7. O4 workspace retention override — **defer to v1.1**

**Verified:** No retention column on `workspaces`; no admin PATCH.

**Locked (O4-v1):** **90d global default only** in v1. Workspace override → v1.1 (schema + admin PATCH). Update O4 registry accordingly.

---

## Inconsistencies — execution notes

| Topic | Note |
|-------|------|
| **Naming** | Review-pipeline **R5** = reconcile/judge service; review-quality **R5** = metrics. Use distinct code prefixes (`github_finding_reconcile` vs `resolution_status`). |
| **R6-Q2 vs G2** | Check `conclusion` stays severity-derived; confidence 0–5 is **comment-only** (G3 split). |
| **G3** | `build_pr_review_comment()` net-new; today one `build_summary_markdown` for both surfaces. |
| **G8** | `summary_json` on `github_publish_jobs` — needs migration (R3 slice). |
| **`POST …/index?mode=full`** | Not in `installation_indexing.py` today — add in R1 or use profile-only (`deep`/`critical` → `full`). |
| **R1 scope** | Large — execution needs **migration subphase 0** + 5–6 subphases. |
| **R3 ↔ R5 order** | Same PR: `summary_json` column → resolution job on `synchronize` → G9 formatter hook. |
| **Parent recovery checklist** | Stale “merge R8” — R8 merged; update [RECOVERY_CHECKLIST](../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md). |
| **Track M prose** | “After dismiss flows” contradicted locked M1 — fixed via M2. |

---

## Migration subphase 0 (single chain — locked)

Hand-written Alembic, one PR. Suggested columns/tables:

| Object | Slice |
|--------|-------|
| `github_pull_request_revisions.base_sha` | R1 / D8 |
| `github_index_jobs.index_mode` | R1 / D13 |
| `github_pipeline_runs`, `_steps`, `_artifacts` | R1 / O |
| `github_code_chunks.content_hash` | R2 / C1 |
| `github_findings.evidence_snippet` | R4 / E1 |
| `github_finding_groups.resolution_status` | R5 / M |
| `github_publish_jobs.summary_json` | R3 / G8 |

Order in execution file: schema first → services → API → purge job.

---

## Per-slice notes (retained)

- **R1:** Highest risk — D13 hybrid fits `download_repository_tarball` + `chunk_file_content`; SC3 instrumentation correct.
- **R2:** First push = no parent (copy-forward no-op). Delete removed paths vs **parent revision** file set.
- **R3:** Formatter LLM = largest product unknown; R6 table fallback locked.
- **R4:** Grounding dismiss → existing `resolved` group state; clarify in execution.
- **R5:** Blocked on human dismiss — **scoped down** per M2.
- **STRUCTURAL_CONTEXT:** Best doc; SC3 only v1 touchpoint.

---

## Phase gate S4 (add autostart)

Extend smoke checklist beyond #44 command replay:

- [ ] Toggle on → `opened` / `synchronize` autostart e2e (AS2)
- [ ] Diff mode manifest on 1-line PR
- [ ] No paraphrase duplicate rows (D10)
- [ ] Greptile-shaped comment (G)

---

## Questions — locked answers

| # | Question | Answer |
|---|----------|--------|
| **Q1** | AS2: code bug or staging verification? | **Staging e2e gate** unless gate identifies a specific bug |
| **Q2** | Human dismiss in review-quality-v1? | **No** — M2: judge-dismissed + diff heuristic only; human dismiss → R7.6 |
| **Q3** | D10: backfill open PR groups? | **No backfill** — accept one-time regroup on next reconcile (D10-M); supersede pass optional if noisy |

---

## Execution-planning checklist

- [x] M2 — scope R5 without human dismiss
- [x] D10 full formula + D10-M migration behavior
- [x] D8 `base_sha` from webhook
- [x] AS2 staging gate wording
- [x] O4-v1 default-only; O8 infra choice in subphase
- [x] D13-F loud fallback in publish
- [x] Migration subphase 0 list
- [x] PRODUCT_PATTERNS dismiss row corrected
- [x] RECOVERY_CHECKLIST R8 merged
- [x] `execution-peer-review` on [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) (two passes, 2026-07-27)

**Next:** `phase-execution` on `feat/review-quality` starting at RQ0.

---

## Execution peer review (2026-07-27)

**Verdict:** Proceed — two passes; all critical/high/medium items incorporated in [execution](../waves/REVIEW_QUALITY_EXECUTION.md) § Execution peer review.

| Pass | Focus |
|------|--------|
| **1** | `index_mode` at job create; pipeline route; O2 artifacts-only; RQ0 schema; worker hooks; O8 purge |
| **2** | `warning_message` column; AS1 admin deep/critical path; compare re-call in RQ2; RQ8 doc table; Celery beat gate; `retrieve` step_type |

**Blocking questions — locked in execution:** pipeline route (revision-scoped); O8 = `pipeline_purge_tasks.py` + `beat_schedule`.
