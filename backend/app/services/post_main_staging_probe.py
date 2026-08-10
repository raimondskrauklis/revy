# backend/app/services/post_main_staging_probe.py
"""Post-main staging dogfood probe — autostart marker for PR #89 + #92 validation.

Safe import hook only; no intentional defects. Used by chore/post-main-staging-dogfood
to trigger full index → review → publish cycles on revy-staging after deploy.
"""

POST_MAIN_PROBE_MARKER = "post-main-dogfood-v1"


def post_main_probe_value() -> str:
    return POST_MAIN_PROBE_MARKER


def post_main_probe_composed() -> str:
    return POST_MAIN_PROBE_MARKER
