# backend/tests/unit/test_engineering_context_extract.py
"""RCX P1 — lock/smoke extractor."""
from pathlib import Path

from app.services.engineering_context.extract import extract_engineering_context

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "engineering_context"


def test_extract_engineering_context_committed_rcx_fixture():
    md_text = (_FIXTURES / "rcx_findings_snippet.md").read_text(encoding="utf-8")
    result = extract_engineering_context(md_text, max_bytes=8192)
    assert "RCX-D8" in result.lock_ids
    assert "RCX-D12" in result.lock_ids
    assert "## Locked decisions" in result.text
    assert "Diff truncated %" in result.text


def test_extract_engineering_context_locked_decisions_dated_heading():
    md_text = "## Locked decisions (discussion 2026-07-29)\n\n| ID | Decision |\n|----|----------|\n| **JC-D3** | Lock |\n"
    result = extract_engineering_context(md_text, max_bytes=4096)
    assert result.lock_ids == ("JC-D3",)
    assert "JC-D3" in result.text


def test_extract_engineering_context_respects_byte_budget():
    md_text = (_FIXTURES / "rcx_findings_snippet.md").read_text(encoding="utf-8")
    result = extract_engineering_context(md_text, max_bytes=64)
    assert len(result.text.encode("utf-8")) <= 64
