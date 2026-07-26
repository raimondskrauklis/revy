# Review pipeline R8 — Automation + triggers

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) § Q11 / parking lot. **No execution steps.**

**Cross-cutting:** workspace tenancy; audit on settings change + automated triggers; EN+LV for settings UI; unit tests; hand-written Alembic; never block webhook HTTP on pipeline work.

**Authority:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](./REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md), [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) § Triggers, `internal-docs/product/revy/docs/WEBHOOKS.md`.

**Depends on:** R4–R7 on `main` and staging dogfood (`review-r7-v1`).

---

## Goal

Greptile/Bugbot parity — **autostart** the full review pipeline on PR open and every push, with workspace toggle and **`@revy review`** on-demand re-run.

**Scope:** In — workspace `review_autostart_enabled` (default on); webhook chain `pull_request.opened` / `synchronize` → index → review → reconcile → publish (reuse R4–R6 workers); `issue_comment` + `@revy review` command namespace; `index_in_progress` guard; `GET …/pull-requests/{id}` for reviewer detail; minimal settings API + UI toggle. Out — `push`-only autostart (defer); incremental chunk hash index (R9); evidence snippets on findings (R9); email digest (R9); full `workspace_review_policy` rules UI (R9+); `@revy index` / `@revy publish` commands (reserved namespace, not implemented).

**Deliverables:** PR opened or updated on connected repo triggers pipeline when autostart on; comment `@revy review` re-runs pipeline; manual-only workspaces unchanged (admin API triggers only); reviewer detail page uses single-PR API.

**Next:** [waves/REVIEW_PIPELINE_R8_EXECUTION.md](./waves/REVIEW_PIPELINE_R8_EXECUTION.md) after peer-review → `phase-execution` on `feat/review-r8-automation`.

---

## R9 (deferred — separate general plan later)

Incremental index on `synchronize`; evidence snippet on findings + judge grounding; resolution-rate metrics; review-complete email; symbol index; plan-gated volume (Q9).
