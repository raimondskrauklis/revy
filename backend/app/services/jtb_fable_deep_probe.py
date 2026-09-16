# backend/app/services/jtb_fable_deep_probe.py
"""Intentional staging probe — post-#107 Fable Deep + judge.

Live ``subprocess.call(..., shell=True)`` so autostart (Kimi) and Deep (Fable)
both see a security finding. Do not call from production request paths.
"""
from __future__ import annotations

import subprocess

JTB_FABLE_DEEP_PROBE_MARKER = "jtb-fable-deep-dogfood"


def run_untrusted_command(user_input: str) -> int:
    return subprocess.call(user_input, shell=True)


def jtb_fable_deep_probe_marker() -> str:
    return JTB_FABLE_DEEP_PROBE_MARKER
