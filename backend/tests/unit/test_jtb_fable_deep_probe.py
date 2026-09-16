# backend/tests/unit/test_jtb_fable_deep_probe.py
"""Staging probe for post-#107 Fable Deep dogfood."""
from app.services.jtb_fable_deep_probe import (
    JTB_FABLE_DEEP_PROBE_MARKER,
    jtb_fable_deep_probe_marker,
    run_untrusted_command,
)


def test_probe_marker() -> None:
    assert jtb_fable_deep_probe_marker() == JTB_FABLE_DEEP_PROBE_MARKER


def test_run_untrusted_command_uses_shell(monkeypatch) -> None:
    calls: list[tuple[str, bool]] = []

    def fake_call(cmd: str, shell: bool = False) -> int:
        calls.append((cmd, shell))
        return 0

    monkeypatch.setattr("subprocess.call", fake_call)
    assert run_untrusted_command("echo hi") == 0
    assert calls == [("echo hi", True)]
