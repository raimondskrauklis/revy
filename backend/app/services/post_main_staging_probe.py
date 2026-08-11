# backend/app/services/post_main_staging_probe.py
"""Post-main staging dogfood probe — autostart marker for MRC post-#98/#99 validation.

Safe import hook only; no intentional defects. Push 1 after #99 deploy:
models_snapshot population (P2) + pipeline trace API exposure (P3).
"""

POST_MAIN_PROBE_MARKER = "post-main-dogfood-v7-mrc-snapshot-api"


def post_main_probe_value() -> str:
    return POST_MAIN_PROBE_MARKER


def post_main_probe_composed() -> str:
    return POST_MAIN_PROBE_MARKER
