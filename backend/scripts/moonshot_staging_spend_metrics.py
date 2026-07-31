# backend/scripts/moonshot_staging_spend_metrics.py
"""Reconcile Moonshot request-log CSV vs staging DB completed review runs."""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import asyncpg

_REVIEW_RUNS_SQL = """
SELECT date_trunc('day', created_at AT TIME ZONE 'UTC')::date AS d,
       count(*)::int AS completed_runs,
       count(*) FILTER (WHERE provider = 'moonshot')::int AS moonshot_runs
FROM github_review_runs
WHERE status = 'completed'
  AND ($1::timestamptz IS NULL OR created_at >= $1::timestamptz)
GROUP BY 1
ORDER BY 1;
"""

_PUBLISH_SQL = """
SELECT date_trunc('day', created_at AT TIME ZONE 'UTC')::date AS d,
       count(*)::int AS publishes
FROM github_publish_jobs
WHERE status = 'completed'
  AND ($1::timestamptz IS NULL OR created_at >= $1::timestamptz)
GROUP BY 1
ORDER BY 1;
"""

_REVIEW_LIKE_INPUT_MIN = 10_000
_PUBLISH_LIKE_INPUT_MAX = 5_000
_PUBLISH_LIKE_INPUT_MIN = 500
_OUTPUT_CAP = 32_768


@dataclass(frozen=True)
class MoonshotRow:
    created_at: datetime
    model: str
    api_key_name: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int

    def classify(self) -> str:
        if self.input_tokens >= _REVIEW_LIKE_INPUT_MIN:
            return "review_like"
        if (
            self.input_tokens < _PUBLISH_LIKE_INPUT_MAX
            and self.input_tokens >= _PUBLISH_LIKE_INPUT_MIN
        ):
            return "publish_like"
        return "other"


def _staging_database_url() -> str:
    url = (
        os.environ.get("STAGING_DATABASE_URL", "").strip()
        or os.environ.get("PRODUCTION_DATABASE_URL", "").strip()
    )
    if not url:
        raise SystemExit(
            "STAGING_DATABASE_URL or PRODUCTION_DATABASE_URL required in backend/.env"
        )
    return url.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]


def _ssl_context() -> ssl.SSLContext | bool:
    if os.environ.get("DATABASE_SSL_INSECURE", "").strip().lower() in ("1", "true", "yes"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _load_csv(path: Path) -> list[MoonshotRow]:
    rows: list[MoonshotRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            rows.append(
                MoonshotRow(
                    created_at=datetime.strptime(
                        record["Created At"], "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=UTC),
                    model=record.get("Model", ""),
                    api_key_name=record.get("API Key Name", ""),
                    input_tokens=int(record["Input Tokens"]),
                    output_tokens=int(record["Output Tokens"]),
                    cached_tokens=int(record.get("Cached Tokens") or 0),
                )
            )
    return rows


def _summarize_csv(rows: list[MoonshotRow], *, since: datetime | None, days: int) -> dict[str, Any]:
    if not rows:
        return {"rows": 0, "by_day": {}}
    max_dt = max(row.created_at for row in rows)
    cutoff_date = (since.date() if since else max_dt.date() - timedelta(days=days - 1))
    window = [
        row
        for row in rows
        if row.created_at.date() >= cutoff_date
        and (since is None or row.created_at >= since)
    ]
    by_day: dict[str, dict[str, Any]] = {}
    for row in window:
        day = row.created_at.date().isoformat()
        bucket = by_day.setdefault(
            day,
            {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "review_like": 0,
                "publish_like": 0,
                "other": 0,
                "output_cap_hits": 0,
            },
        )
        bucket["calls"] += 1
        bucket["input_tokens"] += row.input_tokens
        bucket["output_tokens"] += row.output_tokens
        bucket["cached_tokens"] += row.cached_tokens
        bucket[row.classify()] += 1
        if row.output_tokens == _OUTPUT_CAP:
            bucket["output_cap_hits"] += 1

    return {
        "window_start": cutoff_date.isoformat(),
        "window_end": max_dt.date().isoformat(),
        "rows_in_window": len(window),
        "total_input_tokens": sum(row.input_tokens for row in window),
        "total_output_tokens": sum(row.output_tokens for row in window),
        "by_day": dict(sorted(by_day.items())),
        "output_cap_hits": [
            {
                "created_at": row.created_at.isoformat(sep=" "),
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
            }
            for row in window
            if row.output_tokens == _OUTPUT_CAP
        ],
    }


async def _fetch_db(since: datetime | None) -> dict[str, Any]:
    conn = await asyncpg.connect(_staging_database_url(), ssl=_ssl_context())
    try:
        review_rows = await conn.fetch(_REVIEW_RUNS_SQL, since)
        publish_rows = await conn.fetch(_PUBLISH_SQL, since)
    finally:
        await conn.close()
    return {
        "database": urlparse(_staging_database_url()).path.lstrip("/"),
        "review_runs_by_day": [
            {"day": row["d"].isoformat(), **{k: row[k] for k in row if k != "d"}}
            for row in review_rows
        ],
        "publishes_by_day": [
            {"day": row["d"].isoformat(), "publishes": row["publishes"]} for row in publish_rows
        ],
    }


def _print_human(metrics: dict[str, Any]) -> None:
    csv_part = metrics["moonshot_csv"]
    db_part = metrics.get("database")
    print("Moonshot staging spend — CSV vs DB")
    print(f"  csv: {metrics['csv_path']}")
    print(f"  window: {csv_part['window_start']} .. {csv_part['window_end']}")
    print(f"  rows in window: {csv_part['rows_in_window']}")
    print(
        f"  tokens: {csv_part['total_input_tokens']:,} in / "
        f"{csv_part['total_output_tokens']:,} out"
    )
    print("\nMoonshot by day:")
    for day, bucket in csv_part["by_day"].items():
        print(
            f"  {day}: calls={bucket['calls']} "
            f"in={bucket['input_tokens']:,} out={bucket['output_tokens']:,} "
            f"review_like={bucket['review_like']} publish_like={bucket['publish_like']} "
            f"other={bucket['other']}"
        )
    if csv_part["output_cap_hits"]:
        print(f"\nOutput at {_OUTPUT_CAP} cap: {len(csv_part['output_cap_hits'])}")
        for hit in csv_part["output_cap_hits"]:
            print(f"  {hit['created_at']} in={hit['input_tokens']:,}")

    if db_part:
        print(f"\nDB ({db_part['database']}) completed review runs by day:")
        for row in db_part["review_runs_by_day"]:
            print(f"  {row['day']}: completed={row['completed_runs']} moonshot={row['moonshot_runs']}")
        print("DB completed publishes by day:")
        for row in db_part["publishes_by_day"]:
            print(f"  {row['day']}: publishes={row['publishes']}")

    print(
        "\nNote: each review run is typically 2 Moonshot calls "
        "(large review + small publish summary)."
    )


async def _run() -> int:
    parser = argparse.ArgumentParser(description="Moonshot staging spend metrics")
    parser.add_argument(
        "--csv",
        default="../misc/request_log_part_0001.csv",
        help="Moonshot request log CSV export",
    )
    parser.add_argument("--since", help="ISO timestamp lower bound (UTC)")
    parser.add_argument("--days", type=int, default=3, help="Rolling day window when --since omitted")
    parser.add_argument("--no-db", action="store_true", help="Skip staging DB comparison")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        raise SystemExit(f"CSV not found: {csv_path}")

    since = _parse_since(args.since)
    rows = _load_csv(csv_path)
    metrics: dict[str, Any] = {
        "csv_path": str(csv_path.resolve()),
        "since": since.isoformat() if since else None,
        "days": args.days,
        "moonshot_csv": _summarize_csv(rows, since=since, days=args.days),
    }
    if not args.no_db:
        metrics["database"] = await _fetch_db(since)

    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        _print_human(metrics)
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
