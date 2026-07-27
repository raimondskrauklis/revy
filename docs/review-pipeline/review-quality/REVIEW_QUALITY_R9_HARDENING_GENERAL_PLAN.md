# Review quality R9 — hardening (post-merge)

**Status:** next — branch `docs/agent-work` · **Tag after gate:** `review-quality-v1.1` (optional) or fold into `review-quality-v1` human gate if shipped before tag.

**Baseline:** [REVIEW_QUALITY_DOGFOOD_PR50.md](./REVIEW_QUALITY_DOGFOOD_PR50.md) § parking + execution gap pass (2026-07-27).

**Prerequisite:** RQ0–RQ8 merged to `main` (PR #50).

---

## Why R9 exists

RQ0–RQ8 shipped the review-quality program in one PR. Post-merge gap pass and dogfood found **small but real** corners cut: G10 check UX on benign skip paths, undertested TX boundaries, and agent orchestration docs not wired into Greptile scope. R9 is a **tight hardening slice** — no new schema, no product features.

---

## Goals

| # | Goal | Source |
|---|------|--------|
| H1 | G10 `neutral` finalize when review skipped (draft/closed PR) — no orphan `in_progress` | Dogfood § parking |
| H2 | Unit test proving G10 check survives index TX rollback (split `get_db_context`) | Greptile babysit RC-D16 |
| H3 | Greptile/Bugbot contract includes orchestration quick-ref + roles | Gap pass E8 |
| H4 | Execution doc fidelity (RQ0 schema, RQ1 rollback, RQ6 hook anchor) | Gap pass E1–E4 |
| H5 | Staging re-smoke checklist for post–review-quality deploy | Gap pass + RQ8 gate |

---

## Out of scope (defer)

| Item | Track |
|------|--------|
| SC3 `changed_symbols` / caller graph population | **RQ-STRUCT-1** |
| Human dismiss UI (R7.6) | Product backlog |
| Unique constraint on `pipeline_runs.index_job_id` | v1.1 if hot-path proves need |
| `publish_job_id` index | v1.1 |
| Full RQ-RC-1 scoped review context | [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) |

---

## Deliverables

1. Code — `ReviewAfterIndexOutcome.neutral_finalize_check`; `finalize_pipeline_github_check_neutral`; `index_tasks` wire-up; tests.
2. Config — `.greptile/files.json` + `.cursor/BUGBOT.md` expanded paths.
3. Docs — `REVIEW_QUALITY_EXECUTION.md` § RQ9; staging smoke § post–review-quality; recovery checklist Track I.

---

## Execution

See [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) § RQ9.
