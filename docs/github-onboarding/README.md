# docs/github-onboarding/README.md

# GitHub onboarding — program index (Revy)

In-app wizard so a **new Revy user** can connect GitHub: start in Revy, GitHub App install / Setup URL (not typed IDs), then verify the target repo.

**Home:** this repo (`revy`). **Dogfood target:** enable Revy on `github.com/raimondskrauklis/saas-base` (consumer repo, not where this program lives).

This is review-pipeline **Q10** (OAuth install UI) as its own parallel program.

**Authority:** [GITHUB_ONBOARDING_FINDINGS.md](./GITHUB_ONBOARDING_FINDINGS.md) Q1–Q9, Q11–Q21 · [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md)

| Doc | Role |
|-----|------|
| [GITHUB_ONBOARDING_FINDINGS.md](./GITHUB_ONBOARDING_FINDINGS.md) | Baseline. No execution steps. |
| [GITHUB_ONBOARDING_GENERAL_PLAN.md](./GITHUB_ONBOARDING_GENERAL_PLAN.md) | P0–P4 goals. No execution steps. |
| [Architecture peer review](./reviews/architecture-peer-review/README.md) | Pass 2 delta — **BLOCK create-execution-plan: no** |
| [Execution peer review](./reviews/execution-peer-review/README.md) | Pass index. |

## LOOP order

| Phase | Focus | File | Status |
|-------|-------|------|--------|
| P0 | Env, HMAC `state`, target-config Q8+Q12 | [GITHUB_ONBOARDING_P0_EXECUTION.md](./GITHUB_ONBOARDING_P0_EXECUTION.md) | done |
| P1 | Public hops (no JWT), persist, `verified_at` + checklist + backfill | [GITHUB_ONBOARDING_P1_EXECUTION.md](./GITHUB_ONBOARDING_P1_EXECUTION.md) | done |
| P2 | Start-connect JWT API + wizard UI | [GITHUB_ONBOARDING_P2_EXECUTION.md](./GITHUB_ONBOARDING_P2_EXECUTION.md) | done |
| P3 | Live ≥1-repo verify sets `verified_at` | [GITHUB_ONBOARDING_P3_EXECUTION.md](./GITHUB_ONBOARDING_P3_EXECUTION.md) | pending |
| P4 | Dogfood saas-base, live App paste, Q10 close, doc-sync | [GITHUB_ONBOARDING_P4_EXECUTION.md](./GITHUB_ONBOARDING_P4_EXECUTION.md) | pending |

**Depends:** P1 → P0 · P2 → P1 · P3 → P1+P2 · P4 → P0–P3 + live App URLs.

**Related:** [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md) Q10 · [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md)

**Next:** `phase-execution` from P0.
