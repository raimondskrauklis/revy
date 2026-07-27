# Review pipeline R8 — Automation + triggers

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) § Q11. **No execution steps.**

**Cross-cutting:** workspace tenancy; audit on settings change + automated triggers; EN+LV for settings UI; unit tests; hand-written Alembic; never block webhook HTTP on pipeline work.

**Authority:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md), [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) § Triggers, `internal-docs/product/revy/docs/WEBHOOKS.md`.

**Depends on:** R4–R7 on `main` and staging dogfood (`review-r7-v1`).

---

## Goal

Greptile/Bugbot parity — **autostart** the full review pipeline on PR open and every push, with workspace toggle and **`@revy review`** on-demand re-run.

**Scope (in):**

| Item | Detail |
|------|--------|
| Workspace toggle | `review_autostart_enabled` (default on); admin PATCH only — **R8-Q1** |
| Webhook autostart | `pull_request` `opened` + `synchronize` (new revision only) → index → review → reconcile → publish — **R8-Q2** |
| On-demand command | `issue_comment` + `@revy review` on open PRs — **R8-Q3** |
| Chain guards | Skip with log when API/LLM keys missing; `index_in_progress` guard — **R8-Q4**, **R8-Q5** |
| Manual index isolation | Admin `POST …/index` stays index-only; no auto-chain to review — **R8-Q7** |
| Single-PR API | `GET …/pull-requests/{id}` for reviewer detail — **R8-Q6** |
| Settings UI | Minimal autostart toggle (EN+LV) |

**Scope (out):** `push`-only autostart; incremental chunk hash index (**R9**); evidence snippets on findings (**R9**); email digest (**R9**); full `workspace_review_policy` rules UI (**R9+**); `@revy index` / `@revy publish` (reserved namespace, not implemented).

**Deliverables:** PR opened or updated on a connected repo triggers the pipeline when autostart is on; `@revy review` re-runs the full pipeline; manual-only workspaces unchanged (admin API triggers only); reviewer detail uses single-PR API.

**Locked decisions:** [findings § R8-Q1–R8-Q7](./REVIEW_PIPELINE_FINDINGS.md#decisions-registry)

**Next:** [waves/REVIEW_PIPELINE_R8_EXECUTION.md](./waves/REVIEW_PIPELINE_R8_EXECUTION.md) — shipped on `main` (#31). Follow-on: [review-quality execution](./waves/REVIEW_QUALITY_EXECUTION.md).

---

## R9 (deferred — separate general plan later)

Incremental index on `synchronize`; evidence snippet on findings + judge grounding; resolution-rate metrics; review-complete email; symbol index; plan-gated volume (Q9).
