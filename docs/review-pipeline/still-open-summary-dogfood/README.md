# Still-open summary vs inline collapse — dogfood

**Status:** **P1 implemented** (SOS-5) — deploy + #491 rev 3 dogfood re-check pending. P0 shipped ([#83](https://github.com/raimondskrauklis/revy/pull/83)).

**Thesis:** On new publishes, GH-1v2 collapse and `### Still open on PR` stay aligned. Fix **current implementation** when dogfood finds drift.

**Related programs:** [publish-summary-alignment](../publish-summary-alignment/README.md), [finding-resolution](../finding-resolution/README.md), [github-surface-hardening](../github-surface-hardening/README.md).

| Doc | Purpose |
|-----|---------|
| [STILL_OPEN_SUMMARY_DOGFOOD_FINDINGS.md](./STILL_OPEN_SUMMARY_DOGFOOD_FINDINGS.md) | Evidence + gap registry (SOS-*) |
| [STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md](./STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md) | P0–P2 plan |
| [waves/STILL_OPEN_SUMMARY_DOGFOOD_EXECUTION.md](./waves/STILL_OPEN_SUMMARY_DOGFOOD_EXECUTION.md) | LOOP index |

**Evidence PRs:** [#485](https://github.com/raimondskrauklis/kp-platform/pull/485) (first report), [#489](https://github.com/raimondskrauklis/kp-platform/pull/489) (pre-deploy repro — **out of scope**), [#491](https://github.com/raimondskrauklis/kp-platform/pull/491) (post-deploy PASS).

**DB script:** `backend/scripts/revy_review_dogfood_staging_validation.py --repo raimondskrauklis/kp-platform --pr 491 --json`

**Next:** Monitor post-#83 PRs; log P1 gaps in findings and ship targeted fixes when proven.
