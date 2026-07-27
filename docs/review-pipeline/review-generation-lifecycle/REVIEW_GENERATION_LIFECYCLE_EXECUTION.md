# Review generation lifecycle — execution index

**Program:** [README.md](./README.md) · **Baseline:** [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) · **General plan:** [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md)

**Authority:** [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md) · [github-surface-hardening](../github-surface-hardening/) (prerequisite)

**Goal:** Greptile/Bugbot-class snapshot semantics — HEAD-gated publish, supersede in-flight generations, full surface flush, optional coalesce, judge-candidate gate.

**Branch:** `feat/review-generation-lifecycle`

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5
each phase: implement → pytest gate → Bugbot → commit (push when user/LOOP ready)
```

**Gap IDs (RG-*):** findings catalog. **P0–P5:** program phases below.

## Decisions locked for execution

- **RG-Q1:** Snapshot at HEAD — supersede in-flight; publish after finish only.
- **RG-Q3:** Coalesce ≤10 s; **default `review_coalesce_seconds=0`** (off until enabled).
- **RG-Q7:** Full GitHub surface flush at publish end (check + issue + resolve + inline).
- **RG-Q8:** Superseded/stale checks → `finalize_pipeline_github_check_neutral` (“Superseded by newer commit”).
- **RG-Q9:** `GitHubReviewRunStatus.superseded` = authority; publish `skipped_not_head` / `skipped_superseded`.
- **RG-Q10:** Hold **judge-candidates** only without outcome; publish rest.
- **RG-Q11:** Non-authoritative revision — index DB OK; skip G10 start + review enqueue.
- **RG-Q12:** No Alembic for new `String(32)` status values.
- **P4 mechanism:** debounced Celery task with `countdown` + `revision_id` token; revision DB row immediate.
- **i18n:** GitHub markdown EN v1.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Foundations | Enums + authority helpers + settings | [REVIEW_GENERATION_LIFECYCLE_P0_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P0_EXECUTION.md) | **done** |
| P1 — HEAD gate | Skip publish when not HEAD / superseded | [REVIEW_GENERATION_LIFECYCLE_P1_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P1_EXECUTION.md) | pending |
| P2 — Supersede | Stage-entry guards + G10 neutral | [REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md) | pending |
| P3 — Surface flush | No spill on any channel | [REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P3_EXECUTION.md) | pending |
| P4 — Coalesce | Autostart debounce ≤10 s | [REVIEW_GENERATION_LIFECYCLE_P4_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P4_EXECUTION.md) | pending |
| P5 — Judge + dogfood | RG-6 filter, trace, doc sync | [REVIEW_GENERATION_LIFECYCLE_P5_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P5_EXECUTION.md) | pending |

**Dogfood log:** create `REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md` in **P5** (two pushes ~8 s apart; inline thread count metric).

**Peer review:** `execution-peer-review` (2026-07-28) — gaps incorporated in execution files.
