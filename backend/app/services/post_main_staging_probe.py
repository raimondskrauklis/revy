# backend/app/services/post_main_staging_probe.py
"""Post-main staging dogfood probe — autostart marker for post-#103 RTU provider.

Safe import hook only; no intentional defects. Push 1 after #103 deploy:
reviewer/judge/publish ``models_snapshot`` must show provider ``rtu``.
"""

POST_MAIN_PROBE_MARKER = "post-main-dogfood-v8-rtu-provider"


def post_main_probe_value() -> str:
    return POST_MAIN_PROBE_MARKER


def post_main_probe_composed() -> str:
    return POST_MAIN_PROBE_MARKER
