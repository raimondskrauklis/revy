# backend/scripts/judge_json_contract_staging_metrics.py
"""Staging metrics for judge-json-contract P5 and review-context validation."""
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

_CANDIDATE_RUNS_SQL = """
WITH candidate_runs AS (
  SELECT rr.id,
         rr.created_at,
         rr.judge_status,
         rr.judge_escalation_candidate_count,
         (SELECT count(*) FROM github_finding_judge_outcomes o WHERE o.review_run_id = rr.id) AS outcomes
  FROM github_review_runs rr
  WHERE rr.status = 'completed' AND rr.judge_escalation_candidate_count > 0
)
SELECT count(*)::int AS runs,
       count(*) FILTER (WHERE outcomes > 0)::int AS with_outcomes,
       count(*) FILTER (WHERE outcomes = 0)::int AS all_failed,
       count(*) FILTER (WHERE judge_status = 'skipped_unavailable')::int AS skipped_unavailable
FROM candidate_runs;
"""

_MANIFEST_CANDIDATES_SQL = """
WITH manifests AS (
  SELECT pr.review_run_id,
         rr.created_at,
         jsonb_array_elements(a.content_json->'candidates') AS c
  FROM github_pipeline_artifacts a
  JOIN github_pipeline_steps s ON s.id = a.step_id
  JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
  JOIN github_review_runs rr ON rr.id = pr.review_run_id
  WHERE s.step_type = 'judge'
    AND a.kind = 'manifest'
    AND rr.status = 'completed'
    AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
)
SELECT count(*)::int AS total_candidates,
       count(*) FILTER (WHERE c->>'outcome' IS NOT NULL)::int AS with_outcome,
       count(*) FILTER (WHERE c->>'parse_error' IS NOT NULL)::int AS with_parse_error,
       count(*) FILTER (WHERE coalesce((c->>'retry_count')::int, 0) > 0)::int AS with_retry,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY length(coalesce(c->>'user_prompt', ''))
       )::int AS user_prompt_p50,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY coalesce((c->>'file_patch_chars')::int, 0)
       )::int AS file_patch_chars_p50
FROM manifests;
"""

_RECENT_FAILURES_SQL = """
SELECT pr.review_run_id::text,
       rr.created_at,
       c->>'parse_error' AS parse_error,
       c->>'retry_count' AS retry_count,
       left(c->>'raw_response_text', 120) AS raw_response_preview,
       length(c->>'user_prompt') AS user_prompt_chars
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = pr.review_run_id
CROSS JOIN LATERAL jsonb_array_elements(a.content_json->'candidates') AS c
WHERE s.step_type = 'judge'
  AND a.kind = 'manifest'
  AND c->>'outcome' IS NULL
  AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
ORDER BY rr.created_at DESC
LIMIT 10;
"""

_ALEMBIC_SQL = "SELECT version_num FROM alembic_version LIMIT 1;"

_RETRIEVE_MANIFESTS_SQL = """
WITH manifests AS (
  SELECT rr.id AS review_run_id,
         rr.created_at,
         a.content_json
  FROM github_pipeline_artifacts a
  JOIN github_pipeline_steps s ON s.id = a.step_id
  JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
  JOIN github_review_runs rr ON rr.id = pr.review_run_id
  WHERE s.step_type = 'retrieve'
    AND a.kind = 'manifest'
    AND rr.status = 'completed'
    AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
)
SELECT count(*)::int AS runs,
       count(*) FILTER (
         WHERE coalesce((content_json->>'diff_truncated')::boolean, false)
       )::int AS diff_truncated_runs,
       round(
         100.0 * count(*) FILTER (
           WHERE coalesce((content_json->>'diff_truncated')::boolean, false)
         ) / nullif(count(*), 0),
         1
       ) AS diff_truncated_pct,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY coalesce(jsonb_array_length(content_json->'omitted_files'), 0)
       )::int AS omitted_files_p50,
       percentile_cont(0.95) WITHIN GROUP (
         ORDER BY coalesce(jsonb_array_length(content_json->'omitted_files'), 0)
       )::int AS omitted_files_p95,
       count(*) FILTER (
         WHERE EXISTS (
           SELECT 1
           FROM jsonb_array_elements_text(
             coalesce(content_json->'omitted_files', '[]'::jsonb)
           ) AS path
           WHERE path LIKE '%.md'
         )
       )::int AS runs_with_omitted_md,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY coalesce(jsonb_array_length(content_json->'changed_files'), 0)
       )::int AS changed_files_p50,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY coalesce(jsonb_array_length(content_json->'retrieval_hits'), 0)
       )::int AS retrieval_hits_p50,
       count(*) FILTER (WHERE content_json->>'fallback_reason' IS NOT NULL)::int AS with_fallback_reason,
       count(*) FILTER (
         WHERE coalesce((content_json->>'engineering_context_injected')::boolean, false)
       )::int AS engineering_context_injected_runs
FROM manifests;
"""

_REVIEW_PROMPT_SQL = """
SELECT count(*)::int AS prompt_artifacts,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY length(coalesce(a.content_text, ''))
       )::int AS prompt_chars_p50,
       percentile_cont(0.95) WITHIN GROUP (
         ORDER BY length(coalesce(a.content_text, ''))
       )::int AS prompt_chars_p95
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = pr.review_run_id
WHERE s.step_type = 'review'
  AND a.kind = 'prompt'
  AND rr.status = 'completed'
  AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz);
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge JSON contract staging metrics")
    parser.add_argument(
        "--since",
        help="ISO timestamp — only runs created at or after (e.g. 2026-07-29)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only",
    )
    return parser.parse_args()


def _staging_database_url() -> str:
    url = os.environ.get("PRODUCTION_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "PRODUCTION_DATABASE_URL not set — add revy-staging URL to backend/.env"
        )
    return url.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]


def _ssl_context() -> ssl.SSLContext | bool:
    if os.environ.get("DATABASE_SSL_INSECURE", "").strip().lower() in ("1", "true", "yes"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


async def _fetch_metrics(since: datetime | None) -> dict[str, Any]:
    conn = await asyncpg.connect(_staging_database_url(), ssl=_ssl_context())
    try:
        run_row = await conn.fetchrow(_CANDIDATE_RUNS_SQL)
        manifest_row = await conn.fetchrow(_MANIFEST_CANDIDATES_SQL, since)
        failures = await conn.fetch(_RECENT_FAILURES_SQL, since)
        retrieve_row = await conn.fetchrow(_RETRIEVE_MANIFESTS_SQL, since)
        prompt_row = await conn.fetchrow(_REVIEW_PROMPT_SQL, since)
        alembic_row = await conn.fetchrow(_ALEMBIC_SQL)
    finally:
        await conn.close()

    total_candidates = manifest_row["total_candidates"] or 0
    with_outcome = manifest_row["with_outcome"] or 0
    persistence_pct = (
        round(100.0 * with_outcome / total_candidates, 1) if total_candidates else None
    )

    return {
        "database": urlparse(_staging_database_url()).path.lstrip("/"),
        "since": since.isoformat() if since else None,
        "alembic_version": alembic_row["version_num"] if alembic_row else None,
        "candidate_runs": dict(run_row) if run_row else {},
        "manifest_candidates": dict(manifest_row) if manifest_row else {},
        "outcome_persistence_pct": persistence_pct,
        "recent_failures": [dict(row) for row in failures],
        "review_context": {
            "retrieve_manifest": dict(retrieve_row) if retrieve_row else {},
            "review_prompt": dict(prompt_row) if prompt_row else {},
        },
    }


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


async def _run() -> int:
    args = _parse_args()
    since = _parse_since(args.since)
    metrics = await _fetch_metrics(since)

    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
        return 0

    print("Judge JSON contract — staging metrics")
    print(f"  database: {metrics['database']}")
    print(f"  alembic: {metrics['alembic_version']}")
    if since:
        print(f"  since: {since.isoformat()}")
    print()
    runs = metrics["candidate_runs"]
    print("Candidate runs (completed, judge_escalation_candidate_count > 0):")
    print(f"  runs: {runs.get('runs', 0)}")
    print(f"  with_outcomes: {runs.get('with_outcomes', 0)}")
    print(f"  all_failed: {runs.get('all_failed', 0)}")
    print(f"  skipped_unavailable: {runs.get('skipped_unavailable', 0)}")
    print()
    manifest = metrics["manifest_candidates"]
    print("Manifest candidates:")
    print(f"  total: {manifest.get('total_candidates', 0)}")
    print(f"  with_outcome: {manifest.get('with_outcome', 0)}")
    print(f"  outcome_persistence: {metrics['outcome_persistence_pct']}%")
    print(f"  with_parse_error: {manifest.get('with_parse_error', 0)}")
    print(f"  with_retry: {manifest.get('with_retry', 0)}")
    print(f"  user_prompt p50: {manifest.get('user_prompt_p50')}")
    print(f"  file_patch_chars p50: {manifest.get('file_patch_chars_p50')}")
    if metrics["recent_failures"]:
        print()
        print("Recent failures (up to 10):")
        for row in metrics["recent_failures"]:
            print(
                f"  {row['review_run_id']} | {row['created_at']} | "
                f"{row['parse_error']} | retry={row['retry_count']} | "
                f"prompt={row['user_prompt_chars']} chars"
            )
    review_ctx = metrics.get("review_context", {})
    retrieve = review_ctx.get("retrieve_manifest", {})
    prompt = review_ctx.get("review_prompt", {})
    if retrieve or prompt:
        print()
        print("Review context (retrieve + Moonshot prompt):")
        if retrieve:
            print(f"  completed runs: {retrieve.get('runs', 0)}")
            print(f"  diff_truncated: {retrieve.get('diff_truncated_runs', 0)} "
                  f"({retrieve.get('diff_truncated_pct')}%)")
            print(f"  omitted_files p50/p95: {retrieve.get('omitted_files_p50')}/"
                  f"{retrieve.get('omitted_files_p95')}")
            print(f"  runs_with_omitted_md: {retrieve.get('runs_with_omitted_md', 0)}")
            print(f"  changed_files p50: {retrieve.get('changed_files_p50')}")
            print(f"  retrieval_hits p50: {retrieve.get('retrieval_hits_p50')}")
            print(f"  with_fallback_reason: {retrieve.get('with_fallback_reason', 0)}")
            print(
                f"  engineering_context_injected: "
                f"{retrieve.get('engineering_context_injected_runs', 0)}"
            )
        if prompt:
            print(f"  moonshot prompt p50/p95 chars: "
                  f"{prompt.get('prompt_chars_p50')}/{prompt.get('prompt_chars_p95')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
