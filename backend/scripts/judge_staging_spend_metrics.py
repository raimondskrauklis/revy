# backend/scripts/judge_staging_spend_metrics.py
"""Staging judge spend reconciliation — DB manifest tokens vs outcome counts."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import asyncpg

_SPEND_SQL = """
WITH judge_calls AS (
  SELECT 'discovery' AS kind,
         coalesce((c->>'input_tokens')::int,
                  (c->'raw_response'->'usage'->>'input_tokens')::int) AS input_tokens,
         coalesce((c->>'output_tokens')::int,
                  (c->'raw_response'->'usage'->>'output_tokens')::int) AS output_tokens,
         c->>'outcome' IS NOT NULL AS succeeded,
         c->>'parse_error' IS NOT NULL AS failed
  FROM github_pipeline_artifacts a
  JOIN github_pipeline_steps s ON s.id = a.step_id
  JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
  JOIN github_review_runs rr ON rr.id = pr.review_run_id
  CROSS JOIN LATERAL jsonb_array_elements(a.content_json->'candidates') c
  WHERE s.step_type = 'judge'
    AND a.kind = 'manifest'
    AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
  UNION ALL
  SELECT 'verification',
         coalesce((c->>'input_tokens')::int,
                  (c->'raw_response'->'usage'->>'input_tokens')::int),
         coalesce((c->>'output_tokens')::int,
                  (c->'raw_response'->'usage'->>'output_tokens')::int),
         c->>'outcome' IS NOT NULL,
         c->>'parse_error' IS NOT NULL
  FROM github_pipeline_artifacts a
  JOIN github_pipeline_steps s ON s.id = a.step_id
  JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
  JOIN github_review_runs rr ON rr.id = pr.review_run_id
  CROSS JOIN LATERAL jsonb_array_elements(a.content_json->'verification_candidates') c
  WHERE s.step_type = 'judge'
    AND a.kind = 'manifest'
    AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
)
SELECT count(*)::int AS manifest_slots,
       count(*) FILTER (WHERE succeeded)::int AS with_outcome,
       count(*) FILTER (WHERE failed)::int AS parse_failures,
       coalesce(sum(input_tokens), 0)::bigint AS sum_input_tokens,
       coalesce(sum(output_tokens), 0)::bigint AS sum_output_tokens,
       count(*) FILTER (WHERE input_tokens IS NOT NULL)::int AS slots_with_token_capture
FROM judge_calls;
"""

_RUNS_SQL = """
SELECT count(*)::int AS review_runs,
       count(*) FILTER (WHERE status = 'completed')::int AS completed_runs,
       count(*) FILTER (WHERE judge_escalation_candidate_count > 0)::int AS escalation_runs,
       count(*) FILTER (WHERE judge_status = 'completed')::int AS judge_completed,
       count(*) FILTER (WHERE judge_status = 'skipped_unavailable')::int AS judge_skipped_unavailable,
       count(*) FILTER (WHERE judge_status = 'not_applicable')::int AS judge_not_applicable
FROM github_review_runs rr
WHERE ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz);
"""

_OUTCOMES_SQL = """
SELECT count(*)::int AS outcomes,
       count(*) FILTER (WHERE judge_purpose = 'discovery')::int AS discovery,
       count(*) FILTER (WHERE judge_purpose = 'verification')::int AS verification
FROM github_finding_judge_outcomes
WHERE ($1::timestamptz IS NULL OR created_at >= $1::timestamptz);
"""

_STEP_TOKENS_SQL = """
SELECT coalesce(sum(s.input_tokens), 0)::bigint AS step_input_tokens,
       coalesce(sum(s.output_tokens), 0)::bigint AS step_output_tokens,
       count(*) FILTER (WHERE s.input_tokens IS NOT NULL)::int AS steps_with_tokens
FROM github_pipeline_steps s
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = pr.review_run_id
WHERE s.step_type = 'judge'
  AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz);
"""


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


async def _fetch_metrics(since: datetime | None) -> dict[str, Any]:
    conn = await asyncpg.connect(_staging_database_url(), ssl=_ssl_context())
    try:
        spend = await conn.fetchrow(_SPEND_SQL, since)
        runs = await conn.fetchrow(_RUNS_SQL, since)
        outcomes = await conn.fetchrow(_OUTCOMES_SQL, since)
        step_tokens = await conn.fetchrow(_STEP_TOKENS_SQL, since)
    finally:
        await conn.close()
    return {
        "database": urlparse(_staging_database_url()).path.lstrip("/"),
        "since": since.isoformat() if since else None,
        "review_runs": dict(runs) if runs else {},
        "judge_outcomes": dict(outcomes) if outcomes else {},
        "manifest_spend": dict(spend) if spend else {},
        "pipeline_step_tokens": dict(step_tokens) if step_tokens else {},
    }


def _print_human(metrics: dict[str, Any]) -> None:
    print("Judge staging spend — reconciliation")
    print(f"  database: {metrics['database']}")
    print(f"  since:    {metrics.get('since') or 'all time'}")
    runs = metrics.get("review_runs", {})
    print("\nReview runs:")
    print(f"  total: {runs.get('review_runs', 0)}")
    print(f"  escalation candidates: {runs.get('escalation_runs', 0)}")
    print(f"  judge completed: {runs.get('judge_completed', 0)}")
    print(f"  judge skipped_unavailable: {runs.get('judge_skipped_unavailable', 0)}")
    print(f"  judge not_applicable: {runs.get('judge_not_applicable', 0)}")
    outcomes = metrics.get("judge_outcomes", {})
    print("\nOutcomes persisted:")
    print(f"  total: {outcomes.get('outcomes', 0)}")
    print(f"  discovery: {outcomes.get('discovery', 0)}")
    print(f"  verification: {outcomes.get('verification', 0)}")
    spend = metrics.get("manifest_spend", {})
    print("\nManifest judge slots:")
    print(f"  slots: {spend.get('manifest_slots', 0)}")
    print(f"  with outcome: {spend.get('with_outcome', 0)}")
    print(f"  parse failures: {spend.get('parse_failures', 0)}")
    print(f"  sum input tokens: {spend.get('sum_input_tokens', 0)}")
    print(f"  sum output tokens: {spend.get('sum_output_tokens', 0)}")
    print(f"  slots with token capture: {spend.get('slots_with_token_capture', 0)}")
    steps = metrics.get("pipeline_step_tokens", {})
    print("\nPipeline judge steps:")
    print(f"  step input tokens: {steps.get('step_input_tokens', 0)}")
    print(f"  step output tokens: {steps.get('step_output_tokens', 0)}")
    print(f"  steps with tokens: {steps.get('steps_with_tokens', 0)}")
    print(
        "\nNote: Anthropic CSV rows are daily aggregates (input + output), not per-request counts."
    )


async def _run() -> int:
    parser = argparse.ArgumentParser(description="Judge staging spend metrics")
    parser.add_argument("--since", help="ISO timestamp lower bound (UTC)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    since = _parse_since(args.since)
    metrics = await _fetch_metrics(since)
    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        _print_human(metrics)
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
