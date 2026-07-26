# Review pipeline R7 — Reviewer UI

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** EN+LV via `t()`; `--app-*` tokens; TanStack Query for API; Vitest component tests; workspace scope via `X-Workspace-Id`.

**Authority:** [SETTINGS_IA.md](../saas-base/SETTINGS_IA.md) (nav extension pattern), `frontend/src/platform/extensions/`, R4 findings API contracts.

---

## Goal

In-app surfaces for PR status, findings, and review history — member-facing product UI without replacing GitHub.com.

**Scope:** In — `frontend/src/features/reviewer/`; routes under authenticated shell; PR list per repo/installation; finding list + detail; links out to GitHub PR; dashboard widget slot (extension registry); i18n keys EN+LV. Out — full PR diff viewer; inline reply on GitHub; OAuth install button (separate program item Q10).

**Deliverables:** Workspace member can browse PRs and findings; empty states; error toasts via `mapApiError()`; nav entry only when R4 API exists (nav honesty — same rule as SaaS W0).

**Depends on:** R4 (read-only UI can ship before R6; publish status shown when R6 ships).

**Status:** Not started.

**Next:** `create-execution-plan` when R4 API stable — [waves/REVIEW_PIPELINE_R7_EXECUTION.md](./waves/REVIEW_PIPELINE_R7_EXECUTION.md) (to be created). May overlap R6 publish UX in a follow-up subphase.
