# backend/tests/unit/test_engineering_context_extract.py
"""RCX P1 — lock/smoke extractor."""
from pathlib import Path

from app.services.engineering_context.extract import extract_engineering_context

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "engineering_context"


def test_extract_engineering_context_judge_findings_snippet():
    md_text = (_FIXTURES / "judge_findings_snippet.md").read_text(encoding="utf-8")
    result = extract_engineering_context(md_text, max_bytes=8192)
    assert "JC-D1" in result.lock_ids
    assert "JC-D2" in result.lock_ids
    assert "Locked decisions" in result.text
    assert "P0 smoke" in result.text


def test_extract_engineering_context_rcx_findings_snippet():
    md_text = (_FIXTURES / "rcx_findings_snippet.md").read_text(encoding="utf-8")
    result = extract_engineering_context(md_text, max_bytes=8192)
    assert "RCX-D8" in result.lock_ids
    assert "RCX-D12" in result.lock_ids
    assert "Baseline captured" in result.text
    assert "Queried:" in result.text


def test_extract_engineering_context_truncates_utf8():
    md_text = "## Locked decisions\n\n" + ("x" * 1000)
    result = extract_engineering_context(md_text, max_bytes=50)
    assert len(result.text.encode("utf-8")) <= 50


def test_extract_engineering_context_skips_duplicate_nested_smoke_sections():
    md_text = (
        "## Locked decisions\n\n"
        "foo\n\n"
        "### Baseline captured\n\n"
        "**Queried:** x\n"
    )
    result = extract_engineering_context(md_text, max_bytes=8192)
    assert result.text.count("### Baseline captured") == 1
    assert result.text.count("**Queried:**") == 1
