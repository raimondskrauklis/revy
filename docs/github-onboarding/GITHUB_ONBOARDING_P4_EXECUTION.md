# docs/github-onboarding/GITHUB_ONBOARDING_P4_EXECUTION.md

# P4 — Dogfood + Q10 close (execution)

Phase **P4** of [`GITHUB_ONBOARDING_GENERAL_PLAN.md`](./GITHUB_ONBOARDING_GENERAL_PLAN.md). Baseline: [`GITHUB_ONBOARDING_FINDINGS.md`](./GITHUB_ONBOARDING_FINDINGS.md) experiment table, Q10, Q12, Q16. **P4 only.**

**Goal:** A new Revy user enables Revy on `raimondskrauklis/saas-base` and a PR there gets a Revy check; wizard is the documented happy path.

## Decisions locked for P4

- Q12 — paste **API** Setup/Callback URLs on the live Revy GitHub App (staging/prod). Uncheck OAuth-on-install. Redirect on update on. Slug in env matches the live App.
- Q16 — saas-base visibility is an **experiment gate**, not a product predicate.
- Q2 — no Actions secrets / deploy onboard.
- Q1 — do not change the saas-base codebase.
- Pipeline Q10 ancestor → **shipped** (this program), not left as “reopened”.
- Optional `post-finish-gap-pass` before doc-sync if gaps vs findings are small.

## Out of scope for P4

- saas-base product code, droplet deploy, Marketplace, GHES, Manifest-for-tenants, Greptile Enable UI, member bridge app

---

## P4.1 — Live App paste + env match

**What:** Operator checklist: live App Setup URL + Callback URL = Q12; slug + client id/secret + `GITHUB_OAUTH_PUBLIC_BASE` match that App. Record the paste in [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) as the happy path (manual ID form = fallback).

**Files:** `docs/utils/GITHUB_APP_SETUP.md`, `docs/utils/GITHUB_APP_TARGET_CONFIG.md` (P0 already has URLs; confirm they are what was pasted)

**Deliverable:** setup runbook no longer says leave Setup URL empty / type installation id as the happy path.

**Human gate:** LOOP stops until the live App fields are saved on GitHub. Code may already be deployed from P0–P3.

---

## P4.2 — Dogfood experiment table

**What:** Fill findings experiment gates against staging/local with a new Keycloak user and GitHub access to `raimondskrauklis/saas-base`. Include Redirect-on-update (add repo) does not 409, and a PR on saas-base gets a Revy check. Write results to `docs/github-onboarding/GITHUB_ONBOARDING_STAGING_VALIDATION.md` (new) from evidence, not placeholders.

**Files:** `docs/github-onboarding/GITHUB_ONBOARDING_STAGING_VALIDATION.md` (new)

**Deliverable:** each experiment row is pass or a named residual. saas-base is the dogfood repo in this memo only.

**Human gate:** LOOP stops for sign-off on the memo.

---

## P4.3 — Doc-sync + changelog

**What:** README LOOP statuses Done + sha. Grep siblings for stale “type installation id” / Q10 defer / SPA Setup URL. Flip [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md) **both** Q10 (**shipped**, this folder) **and** the reuse-trap row “OAuth install UI / Not shipped” so they cannot stay “reopened” + “not shipped”. User-facing changelog entry for Connect GitHub.

| Doc | Change |
|-----|--------|
| `docs/github-onboarding/README.md` | Phase statuses + shas |
| `docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md` | Q10 **shipped**; trap row “OAuth install UI” no longer “not shipped” |
| `docs/review-pipeline/README.md` | GitHub App row points at shipped wizard if still “parallel” |
| `docs/utils/GITHUB_APP_SETUP.md` | Happy path = start-connect (P4.1) |
| `frontend/src/data/changelog.json` | Connect GitHub wizard |

**Files:** docs listed above, `frontend/src/data/changelog.json`

**Deliverable:**

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

---

**Phase gate** (from repo root):

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

**Human gate:** P4.1 live App paste + P4.2 experiment memo signed. LOOP does not commit P4 until both pass or residuals are named in the memo.

**Deploy:** no saas-base deploy. Revy API/FE already on the environment used for dogfood.

**Next:** none.
