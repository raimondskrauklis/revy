# backend/tests/unit/test_engineering_context_stats.py
"""RCX P2 — context_stats builder."""
from app.services.engineering_context.pack import EngineeringContextPack
from app.services.engineering_context.stats import build_context_stats


def test_build_context_stats_populates_engineering_fields():
    pack = EngineeringContextPack(
        active_program="review-engineering-context",
        lock_ids=["RCX-D8"],
        inject_text="## Locked decisions\n",
        deduped_paths=["docs/a.md"],
    )
    stats = build_context_stats(
        engineering_pack=pack,
        prompt_chars=1200,
        unified_diff_bytes=4096,
        diff_truncated=True,
        omitted_files=["docs/a.md", "large.py"],
        diff_max_bytes=524288,
    )
    assert stats["active_program"] == "review-engineering-context"
    assert stats["engineering_context_injected"] is True
    assert stats["engineering_context_bytes"] == len(pack.inject_text.encode("utf-8"))
    assert stats["lock_ids_extracted"] == ["RCX-D8"]
    assert stats["engineering_context_deduped_paths"] == ["docs/a.md"]
    assert stats["omitted_md_count"] == 1
    assert stats["prompt_chars"] == 1200
