# backend/tests/unit/test_moonshot_staging_spend_metrics.py
"""Moonshot staging spend metrics script."""
from datetime import UTC, datetime

from scripts.moonshot_staging_spend_metrics import MoonshotRow, _summarize_csv


def test_classify_review_and_publish_like():
    review = MoonshotRow(
        created_at=datetime(2026, 7, 31, 20, 11, 24, tzinfo=UTC),
        model="kimi-k2.7-code",
        api_key_name="revy-main",
        input_tokens=32_336,
        output_tokens=19_267,
        cached_tokens=0,
    )
    publish = MoonshotRow(
        created_at=datetime(2026, 7, 31, 20, 12, 6, tzinfo=UTC),
        model="kimi-k2.7-code",
        api_key_name="revy-main",
        input_tokens=923,
        output_tokens=2_011,
        cached_tokens=0,
    )
    assert review.classify() == "review_like"
    assert publish.classify() == "publish_like"


def test_summarize_csv_groups_by_day():
    rows = [
        MoonshotRow(datetime(2026, 7, 31, 20, 0, 0, tzinfo=UTC), "kimi", "revy-main", 30_000, 10_000, 0),
        MoonshotRow(datetime(2026, 7, 31, 20, 1, 0, tzinfo=UTC), "kimi", "revy-main", 900, 2_000, 0),
        MoonshotRow(datetime(2026, 8, 1, 3, 0, 0, tzinfo=UTC), "kimi", "revy-main", 60_925, 32_768, 0),
    ]
    summary = _summarize_csv(rows, since=None, days=3)
    assert summary["rows_in_window"] == 3
    assert summary["by_day"]["2026-07-31"]["review_like"] == 1
    assert summary["by_day"]["2026-07-31"]["publish_like"] == 1
    assert summary["by_day"]["2026-08-01"]["output_cap_hits"] == 1
    assert len(summary["output_cap_hits"]) == 1
