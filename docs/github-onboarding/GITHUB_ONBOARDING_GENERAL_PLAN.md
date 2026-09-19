# docs/github-onboarding/GITHUB_ONBOARDING_GENERAL_PLAN.md

# GitHub onboarding — general plan (Revy)

**Baseline:** [GITHUB_ONBOARDING_FINDINGS.md](./GITHUB_ONBOARDING_FINDINGS.md) (2026-09-19, pass-02 residuals applied). **No execution steps.**

**Thesis:** Product-first Install URL; public API Setup then Callback (HMAC bind, not JWT); user OAuth from that hop; idempotent bind; verify ≥1 granted repo. saas-base is P4 dogfood, not the product predicate. Pipeline Q10 reopens here.

**Locked:** Q1–Q9, Q11–Q21. No open calibration. Greptile layers 1–3; not their Enable UI (Q11).

---

## Cross-cutting (every phase)

- **Lineage / never mislead:** checklist `connect_integration` iff `verified_at` is set (Q5, Q19, Q21) — not row count, not a query param.
- **Coverage / exclusions:** workspace admin only (Q4); Mode B never enters; members do not start connect; saas-base **codebase** and Actions secrets stay out (Q1, Q2).
- **Visualization:** stepper + states (not started / on GitHub / linked unverified / empty allow-list → Configure / verified). EN+LV via `t()`; `--app-*`.
- **Tests:** `backend/tests/unit/` + frontend unit; spoofed `installation_id`, missing install `state`, OAuth-without-install, already-linked, empty repo list, Redirect-on-update idempotent, plan-gate 403, Setup/Callback with **no** `Authorization` still bind from HMAC, SameSite=Lax stash.
- **Secrets:** PEM, webhook secret, App client secret never in the browser. Discard GitHub user token after association check. HMAC secret server-side on start-connect.
- **No new pipeline tables.** `verified_at` is a column on `github_installations` (handwritten Alembic). Then existing R0–R8.
- **Public hops:** no `get_current_user` on Setup/Callback (Q20). JWT only on start-connect.

---

## P0 — Foundations

**Goal:** Env can name the live App; GitHub can redirect to **public API** hops; target config matches Q8 + Q12.

**Scope:** In — `GITHUB_APP_SLUG`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (server); install HMAC `state` (Q13–Q14, Q20); [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) **replaces SPA placeholders** with Q12 URLs, OAuth-on-install **unchecked**, Redirect on update **on**; `.env.example` + `deploy/env-examples/backend.env.production.example`. Out — persist; wizard UI; live GitHub App dashboard paste (P4).

**Deliverables:** Install URL is buildable from slug + install `state`; target config is pasteable and not mutually exclusive; client-secret comment is gone.

**Depends on:** None.

---

## P1 — Setup hop + Callback hop + persist + honest checklist wiring

**Goal:** After GitHub install, Revy binds a real installation without typed IDs; spoofed query params and Redirect-on-update 409s do not happen; a P1-only merge cannot complete Connect GitHub via row count.

**Scope:** In — public GET `/api/v1/github/setup` then GET `/api/v1/github/callback` (302; SameSite=Lax stash of `installation_id`; **no JWT** — Q20); user-token `GET /user/installations`; new App JWT `GET /app/installations/{id}`; idempotent same workspace+id bind (Q15); `verified_at` null on **new** insert; handwritten Alembic + list API/FE field + checklist switch + grandfather backfill (Q21); enqueue `sync_installation_repositories` (Q17); `installations.create` on persist via HMAC workspace (Q18); no-`state` / OAuth-without-install / other-workspace conflict as errors + copy, not persist. Out — live verify **setting** `verified_at` from GitHub repo list (P3); Enable UI; Marketplace; treating first orphans as a bug; `Depends(get_current_user)` on Setup/Callback.

**Deliverables:** Happy path creates/updates the workspace row from GitHub; spoofed `installation_id` does not; Redirect-on-update does not 409; first orphan webhooks remain expected; new P1 rows do not complete the checklist (`verified_at` null + checklist reads the field); existing active installs stay complete via backfill.

**Depends on:** P0.

---

## P2 — Connect wizard UI

**Goal:** A workspace admin starts connect in Revy and is sent to the right GitHub HTML with instructions.

**Scope:** In — authenticated **start-connect** API (mints install `state`, returns Install URL); stepper after `me.status === active`; Install Revy; `installations.create` **before** leaving Revy (Q18) with `plan_upgrade_required` copy; cards for org owner, SSO, **Only select repositories**, authorize ≠ install; admin-only start (Q4); members may see status; manual ID form as admin/dev fallback (Q6); stale webhook i18n gone. Out — github.com automation; saas-base app; Keycloak as IdP; GitHub as login (Q9); putting Setup on a `ProtectedRoute` SPA path; JWT on Setup/Callback.

**Deliverables:** Happy path never types an installation id; EN+LV on every step; Mode B still never reaches the wizard.

**Depends on:** P1 (hops exist). Live App Setup URL is pasted in P4; until then GitHub cannot return.

---

## P3 — Verify granted repo

**Goal:** “Connected” means live GitHub shows ≥1 granted repo and `verified_at` is **set** (checklist already reads the field from P1).

**Scope:** In — after persist, live `list_installation_repositories` (not local `github_repositories`); ≥1 repo → set `verified_at`; empty → Configure `https://github.com/settings/installations/{id}`; same rule on Q6 fallback rows; Redirect-on-update re-enters this verify. Out — hardcoded `saas-base` predicate; Greptile Enable UI (Q11); re-wiring checklist from row count (done in P1).

**Deliverables:** Typed junk and install-redirect-alone cannot complete the checklist; empty allow-list is Configure-on-GitHub, not success.

**Depends on:** P1–P2.

---

## P4 — Dogfood + Q10 close

**Goal:** A new Revy user enables Revy on `raimondskrauklis/saas-base` and a PR there gets a Revy check.

**Scope:** In — paste Q12 Setup/Callback URLs on the live App; findings experiment table (including saas-base visibility + Redirect-on-update); program README; pipeline Q10 **shipped** here. Out — saas-base product changes; Actions secrets; Marketplace; unrelated merges.

**Deliverables:** Experiment gates pass or residuals named; wizard is the documented happy path.

**Depends on:** P0–P3 in the dogfood environment; live App slug/URLs match env.

---

## Next step

No remaining open findings questions. Execution files P0–P4 are written; execution-peer-review pass 2 **BLOCK: no**. **`phase-execution`** from P0.
