# Review pipeline R4 — Review run

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; audit on review triggers; unit tests; hand-written Alembic; EN+LV for any user-visible review status (API errors/messages).

**Authority:** `internal-docs/product/revy/docs/architecture.md`, `backend/app/core/config.py` (LLM + timeout env), [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R4.

---

## Goal

Run the LLM review pipeline for a PR revision and persist structured findings — core product value.

**Scope:** In — `review_tasks` on `review` queue; `review_runs` + `findings` (or equivalent) schema; **Moonshot Kimi** primary (`MOONSHOT_API_KEY`, K2.7 Code for Standard, K3 for Deep/Critical per profile); staged pipeline (context retrieval from R3 → generate findings); workspace-member gated API to list/read findings per PR; `REVY_DEFAULT_REVIEW_PROFILE` + revision timeouts. Out — Anthropic judge / cross-family escalation (R5); GitHub publish (R6); plan-gated review volume (defer Q9).

**Model policy:** Primary reviewer = Moonshot Kimi (`kimi-k2.7-code` default, `kimi-k3` for deep/critical). Anthropic Claude = secondary judge only (R5) — `internal-docs/product/revy/docs/architecture.md` §13–14.

**Deliverables:** Review run record per revision; finding rows with severity/category/location; API returns findings for workspace members; Celery retry policy aligned with timeout config.

**Depends on:** R3 (retrieval context available).

**Status:** Execution ready — [waves/REVIEW_PIPELINE_R4_EXECUTION.md](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) peer-reviewed (2026-07-26); implement on `feat/review-r4-review-run`.

**Next phase:** [REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md).
