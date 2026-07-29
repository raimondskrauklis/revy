# Publish summary alignment — program index

**Status:** **code-complete (P0–P1)** on `feat/publish-summary-alignment` — staging human gate pending ([validation memo](./PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md)).

**Gap:** **RG-14** / **FR-Q16** — issue comment and check run diverge; confidence/merge can disagree with open inline threads.

**Thesis:** Complete **FR-Q7** on **both** GitHub summary channels — two-block model (this generation + still open on PR), PR-wide verdict fields, aligned with GH-1v2 thread collapse.

**Prerequisites on `main`:** finding-resolution P0–P5 (#57) · generation lifecycle (#54) · github-surface-hardening GH-1v2 · RCX P6+P7 (#61 merged).

| Doc | Purpose |
|-----|---------|
| [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md) | Baseline — verified behavior, gaps, PSA-Q registry |
| [PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md](./PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md) | Operator discussion log — locked PSA-D* before code |
| [PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md](./PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md) | P0–P2 phases (general — no execution steps) |
| [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](./PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) | Staging gate — run **in parallel** with RCX / judge-json-contract pass 2 |
| [waves/PUBLISH_SUMMARY_ALIGNMENT_EXECUTION.md](./waves/PUBLISH_SUMMARY_ALIGNMENT_EXECUTION.md) | LOOP index + locked decisions |

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Product contract + fallback + verdict + metrics markers | [P0](./waves/PUBLISH_SUMMARY_ALIGNMENT_P0_EXECUTION.md) | pending |
| P1 | Moonshot system/user prompt + parity tests | [P1](./waves/PUBLISH_SUMMARY_ALIGNMENT_P1_EXECUTION.md) | pending |
| P2 | Staging validation + doc sync | [P2](./waves/PUBLISH_SUMMARY_ALIGNMENT_P2_EXECUTION.md) | pending |

**Next step:** `phase-execution` on branch `feat/publish-summary-alignment` from `main`.

**Related programs**

| Program | Link |
|---------|------|
| Finding resolution (FR-Q7 partial) | [finding-resolution/README.md](../finding-resolution/README.md) |
| Generation lifecycle (RG-14 origin) | [review-generation-lifecycle/README.md](../review-generation-lifecycle/README.md) |
| GitHub surface hardening (GH-1v2) | [github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md) |
| RCX staging (parallel monitor) | [review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) |
| Staging validation workflow | [staging-validation/STAGING_VALIDATION_FINDINGS.md](../staging-validation/STAGING_VALIDATION_FINDINGS.md) |

**Related code**

| Area | Path |
|------|------|
| Formatter | `backend/app/services/github_publish_formatter.py` |
| Publish surface build | `backend/app/services/github_publish.py` (`_build_publish_surface`) |
| Moonshot issue comment | `backend/app/integrations/moonshot_review.py` |
| Formatter tests | `backend/tests/unit/test_github_publish_formatter.py` |
