# backend/app/services/post_main_staging_probe.py
"""Post-main staging dogfood probe — autostart marker for #89 + #92 + #94 validation.

Safe import hook only; no intentional defects. Push 4 after #94 deploy:
queued GitHub check UX + overlap supersede protocol.
"""

POST_MAIN_PROBE_MARKER = "post-main-dogfood-v4-queued-check"
