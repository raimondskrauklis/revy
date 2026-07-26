# Review pipeline R7 — Reviewer UI

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** EN+LV via `t()`; `--app-*` tokens; TanStack Query for API; Vitest component tests; workspace scope via `X-Workspace-Id`.

**Authority:** [SETTINGS_IA.md](../saas-base/SETTINGS_IA.md) (nav extension pattern), `frontend/src/platform/extensions/`, R4 findings API contracts.

---

## Goal

In-app surfaces for PR status, findings, and review history — member-facing product UI without replacing GitHub.com.

**Scope:** In — `frontend/src/features/reviewer/`; flat routes under authenticated shell (`/reviewer/…`, workspace via `X-Workspace-Id`); PR list per repo/installation; finding list + detail; **merge readiness badge** derived from latest check run conclusion (R6-Q2); links out to GitHub PR; dashboard widget slot (extension registry in `registerRevy.ts`); i18n keys EN+LV. Out — full PR diff viewer; inline reply on GitHub; OAuth install button (separate program item Q10).

**Deliverables:** Workspace member can browse PRs and findings; empty states; error toasts via `mapApiError()`; nav entry only when R4 API exists (nav honesty — same rule as SaaS W0).

**Depends on:** R4 (read-only UI can ship before R6; publish status shown when R6 ships).

**Status:** Not started.

**Next:** `execution-peer-review` when R4 API stable — [waves/REVIEW_PIPELINE_R7_EXECUTION.md](./waves/REVIEW_PIPELINE_R7_EXECUTION.md). R7.4 publish badge may follow R6.
