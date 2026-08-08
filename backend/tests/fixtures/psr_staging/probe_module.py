# backend/tests/fixtures/psr_staging/probe_module.py
"""PSR staging probe — post-deploy rollup dogfood fixture.

Validated on PR #87 (revs 1–2). Fixture lives under tests/ (not app/services).
Rollup parity is covered by test_revy_review_dogfood_staging_validation and
staging --psr-gate per PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md.
"""

PSR_PROBE_MARKER = "psr-staging-dogfood"


def psr_probe_value() -> str:
    """Stable marker return for import smoke tests."""
    return PSR_PROBE_MARKER
