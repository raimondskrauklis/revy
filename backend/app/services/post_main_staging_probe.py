# backend/app/services/post_main_staging_probe.py
"""Post-main staging dogfood probe — autostart marker for MRC post-#96 validation.

Safe import hook only; no intentional defects. Push 1 after #96 deploy:
model-run-capture embedding identity + attempt-row observability.
"""

POST_MAIN_PROBE_MARKER = "post-main-dogfood-v6-mrc-model-capture"


def post_main_probe_value() -> str:
    return POST_MAIN_PROBE_MARKER


def post_main_probe_composed() -> str:
    return POST_MAIN_PROBE_MARKER
