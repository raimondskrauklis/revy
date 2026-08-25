# backend/scripts/judge_json_contract_staging_metrics.py
"""Staging metrics for judge-json-contract P5 and review-context validation.

Groups judge manifest failures by any `parse_error` (including additive
`judge_empty_text` and live `judge_json_invalid`). Do not filter on a
hardcoded old transport string.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
import sys
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

_FAILURE_SPLIT_SQL = """
SELECT c->>'parse_error' AS parse_error,
       c->>'raw_response_text' AS raw_response_text,
       coalesce((c->>'retry_count')::int, 0) AS retry_count
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = pr.review_run_id
CROSS JOIN LATERAL jsonb_array_elements(a.content_json->'candidates') AS c
WHERE s.step_type = 'judge'
  AND a.kind = 'manifest'
  AND rr.status = 'completed'
  AND c->>'outcome' IS NULL
  AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
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

_CONTEXT_STATS_SQL = """
SELECT count(*)::int AS runs_with_context_stats,
       count(*) FILTER (
         WHERE coalesce((context_stats->>'engineering_context_injected')::boolean, false)
       )::int AS engineering_context_injected_runs,
       percentile_cont(0.5) WITHIN GROUP (
         ORDER BY coalesce((context_stats->>'engineering_context_bytes')::int, 0)
       ) FILTER (
         WHERE coalesce((context_stats->>'engineering_context_injected')::boolean, false)
       )::int AS engineering_context_bytes_p50,
       coalesce(
         max(
           CASE
             WHEN coalesce((context_stats->>'engineering_context_injected')::boolean, false)
             THEN coalesce((context_stats->>'engineering_context_bytes')::int, 0)
             ELSE 0
           END
         ),
         0
       )::int AS engineering_context_bytes_max_injected
FROM github_review_runs rr
WHERE rr.status = 'completed'
  AND rr.context_stats IS NOT NULL
  AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz);
"""

_PUBLISH_SUMMARY_SQL = """
WITH completed_publishes AS (
  SELECT
    pj.id,
    pj.summary_json,
    rr.id AS review_run_id
  FROM github_publish_jobs pj
  JOIN github_review_runs rr ON rr.id = pj.review_run_id
  WHERE pj.status = 'completed'
    AND ($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)
),
resolution_pass_by_run AS (
  SELECT DISTINCT ON (pr.review_run_id)
    pr.review_run_id,
    manifest.content_json->'resolution_pass' AS resolution_pass
  FROM github_pipeline_runs pr
  JOIN github_pipeline_steps s
    ON s.pipeline_run_id = pr.id AND s.step_type = 'reconcile'
  JOIN github_pipeline_artifacts manifest
    ON manifest.step_id = s.id AND manifest.kind = 'manifest'
  WHERE manifest.content_json->'resolution_pass' IS NOT NULL
  ORDER BY pr.review_run_id, pr.created_at DESC
),
joined AS (
  SELECT
    cp.id,
    cp.summary_json,
    rp.resolution_pass
  FROM completed_publishes cp
  LEFT JOIN resolution_pass_by_run rp ON rp.review_run_id = cp.review_run_id
)
SELECT
  count(*)::int AS completed_jobs,
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY coalesce((summary_json->>'generation_active_count')::int, 0)
  )::int AS generation_active_count_p50,
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY coalesce((summary_json->>'pr_active_count')::int, 0)
  )::int AS pr_active_count_p50,
  coalesce(
    sum(coalesce((summary_json->'resolution'->>'addressed')::int, 0)),
    0
  )::int AS resolution_addressed_sum,
  count(*) FILTER (
    WHERE coalesce((summary_json->'resolution'->>'addressed')::int, 0) >= 1
  )::int AS jobs_with_resolution_addressed,
  coalesce(
    sum(coalesce((resolution_pass->>'transitions_addressed')::int, 0)),
    0
  )::int AS transitions_addressed_sum,
  coalesce(
    sum(coalesce((resolution_pass->>'denominator_active_prior')::int, 0)),
    0
  )::int AS denominator_active_prior_sum,
  count(*) FILTER (
    WHERE coalesce((resolution_pass->>'denominator_active_prior')::int, 0) >= 1
  )::int AS jobs_with_denominator_active_prior
FROM joined;
"""


def _summarize_publish_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "completed_jobs": int(row.get("completed_jobs") or 0),
        "generation_active_count_p50": row.get("generation_active_count_p50"),
        "pr_active_count_p50": row.get("pr_active_count_p50"),
        "resolution_addressed_sum": int(row.get("resolution_addressed_sum") or 0),
        "jobs_with_resolution_addressed": int(row.get("jobs_with_resolution_addressed") or 0),
        "transitions_addressed_sum": int(row.get("transitions_addressed_sum") or 0),
        "denominator_active_prior_sum": int(row.get("denominator_active_prior_sum") or 0),
        "jobs_with_denominator_active_prior": int(
            row.get("jobs_with_denominator_active_prior") or 0
        ),
    }


def _evaluate_rcx_gate(metrics: dict[str, Any]) -> dict[str, Any]:
    retrieve = metrics.get("review_context", {}).get("retrieve_manifest", {})
    context_stats = metrics.get("review_context", {}).get("context_stats", {})

    completed_runs = int(retrieve.get("runs") or 0)
    runs_with_context_stats = int(context_stats.get("runs_with_context_stats") or 0)
    engineering_injected_ctx = int(context_stats.get("engineering_context_injected_runs") or 0)
    engineering_bytes_p50 = int(context_stats.get("engineering_context_bytes_p50") or 0)
    engineering_bytes_max = int(context_stats.get("engineering_context_bytes_max_injected") or 0)
    runs_with_omitted_md = int(retrieve.get("runs_with_omitted_md") or 0)
    diff_truncated_pct = retrieve.get("diff_truncated_pct")
    retrieve_injected = int(retrieve.get("engineering_context_injected_runs") or 0)

    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if completed_runs == 0:
        add("context_stats_rows", "INCONCLUSIVE", "no completed runs in window")
        add("engineering_context_injected", "INCONCLUSIVE", "no completed runs in window")
        add("engineering_context_bytes_p50", "INCONCLUSIVE", "no completed runs in window")
        add("runs_with_omitted_md", "INCONCLUSIVE", "no completed runs in window")
        add("diff_truncated_pct", "INCONCLUSIVE", "no completed runs in window")
        add("retrieve_manifest_inject_cross_check", "INCONCLUSIVE", "no completed runs in window")
    else:
        add(
            "context_stats_rows",
            "PASS" if runs_with_context_stats >= 1 else "FAIL",
            f"{runs_with_context_stats} rows",
        )
        add(
            "engineering_context_injected",
            "PASS" if engineering_injected_ctx >= 1 else "FAIL",
            f"{engineering_injected_ctx} runs",
        )
        if engineering_injected_ctx > 0:
            bytes_ok = engineering_bytes_p50 > 0 or engineering_bytes_max > 0
            add(
                "engineering_context_bytes_p50",
                "PASS" if bytes_ok else "FAIL",
                f"p50={engineering_bytes_p50}, max_injected={engineering_bytes_max}",
            )
        else:
            add("engineering_context_bytes_p50", "INCONCLUSIVE", "no inject runs")
        add(
            "runs_with_omitted_md",
            "PASS" if runs_with_omitted_md == 0 else "FAIL",
            f"{runs_with_omitted_md} runs",
        )
        if completed_runs >= 3:
            pct = float(diff_truncated_pct) if diff_truncated_pct is not None else 100.0
            add(
                "diff_truncated_pct",
                "PASS" if pct < 5.0 else "FAIL",
                f"{pct}%",
            )
        else:
            add(
                "diff_truncated_pct",
                "INCONCLUSIVE",
                f"{completed_runs} run(s) in window",
            )
        if engineering_injected_ctx > 0 and retrieve_injected == 0:
            add(
                "retrieve_manifest_inject_cross_check",
                "FAIL",
                "context_stats injected but retrieve count 0",
            )
        elif retrieve_injected > 0 and engineering_injected_ctx == 0:
            add(
                "retrieve_manifest_inject_cross_check",
                "FAIL",
                "retrieve injected but context_stats count 0",
            )
        elif engineering_injected_ctx > 0 or retrieve_injected > 0:
            add(
                "retrieve_manifest_inject_cross_check",
                "PASS",
                f"retrieve={retrieve_injected}, context_stats={engineering_injected_ctx}",
            )
        else:
            add("retrieve_manifest_inject_cross_check", "INCONCLUSIVE", "no inject runs")

    passed = not any(check["status"] == "FAIL" for check in checks)
    return {"passed": passed, "checks": checks}


def _print_rcx_gate(rcx_gate: dict[str, Any], *, since: datetime | None) -> None:
    print()
    window = since.isoformat() if since else "full history (baseline mode)"
    print(f"RCX gate ({window}):")
    for check in rcx_gate.get("checks", []):
        print(f"  [{check['status']}] {check['name']}: {check.get('detail', '')}")
    print(f"  overall: {'PASS' if rcx_gate.get('passed') else 'FAIL'}")


def _content_shape(raw: str | None) -> str:
    if not raw:
        return "unknown"
    has_thinking = '"type": "thinking"' in raw or '"type":"thinking"' in raw
    has_text = '"type": "text"' in raw or '"type":"text"' in raw
    if has_thinking and has_text:
        return "text_later"
    if has_thinking and not has_text:
        return "thinking_only"
    return "other"


def _classify_failure_row(parse_error: str | None, raw: str | None) -> str:
    if parse_error == "judge_json_invalid":
        return "invalid_json"
    shape = _content_shape(raw)
    if shape == "text_later":
        return "text_later"
    if shape == "thinking_only":
        return "thinking_only"
    if parse_error == "judge_empty_text":
        return "thinking_only"
    if parse_error == "Anthropic response invalid":
        return "transport"
    return "other"


def _summarize_thinking_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "text_later": 0,
        "thinking_only": 0,
        "invalid_json": 0,
        "transport": 0,
        "other": 0,
    }
    with_retry = 0
    for row in rows:
        bucket = _classify_failure_row(row.get("parse_error"), row.get("raw_response_text"))
        buckets[bucket] = buckets.get(bucket, 0) + 1
        if int(row.get("retry_count") or 0) > 0:
            with_retry += 1
    return {
        "failure_rows": len(rows),
        "with_retry": with_retry,
        **buckets,
    }


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
    parser.add_argument(
        "--rcx-gate",
        action="store_true",
        help="Evaluate RCX pass/fail gate (requires --since for sign-off)",
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
        split_rows = await conn.fetch(_FAILURE_SPLIT_SQL, since)
        retrieve_row = await conn.fetchrow(_RETRIEVE_MANIFESTS_SQL, since)
        prompt_row = await conn.fetchrow(_REVIEW_PROMPT_SQL, since)
        context_stats_row = await conn.fetchrow(_CONTEXT_STATS_SQL, since)
        publish_summary_row = await conn.fetchrow(_PUBLISH_SUMMARY_SQL, since)
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
        "thinking_split": _summarize_thinking_split([dict(row) for row in split_rows]),
        "review_context": {
            "retrieve_manifest": dict(retrieve_row) if retrieve_row else {},
            "review_prompt": dict(prompt_row) if prompt_row else {},
            "context_stats": dict(context_stats_row) if context_stats_row else {},
        },
        "publish_summary": _summarize_publish_summary(
            dict(publish_summary_row) if publish_summary_row else None
        ),
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

    rcx_gate: dict[str, Any] | None = None
    if args.rcx_gate:
        if since is None:
            print(
                "WARNING: --rcx-gate without --since uses full history (baseline mode only)",
                file=sys.stderr,
            )
        rcx_gate = _evaluate_rcx_gate(metrics)
        metrics["rcx_gate"] = rcx_gate

    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
        if args.rcx_gate and rcx_gate is not None and not rcx_gate.get("passed"):
            return 1
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
    split = metrics.get("thinking_split") or {}
    if split:
        print()
        print("Thinking-block split (manifest failures, no outcome):")
        print(f"  failure_rows: {split.get('failure_rows', 0)}")
        print(f"  text_later: {split.get('text_later', 0)}")
        print(f"  thinking_only: {split.get('thinking_only', 0)}")
        print(f"  invalid_json (judge_json_invalid): {split.get('invalid_json', 0)}")
        print(f"  transport: {split.get('transport', 0)}")
        print(f"  other: {split.get('other', 0)}")
        print(f"  with_retry: {split.get('with_retry', 0)}")
    review_ctx = metrics.get("review_context", {})
    retrieve = review_ctx.get("retrieve_manifest", {})
    prompt = review_ctx.get("review_prompt", {})
    context_stats = review_ctx.get("context_stats", {})
    if retrieve or prompt or context_stats:
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
        if context_stats:
            print(f"  runs_with_context_stats: "
                  f"{context_stats.get('runs_with_context_stats', 0)}")
            print(f"  context_stats engineering_injected: "
                  f"{context_stats.get('engineering_context_injected_runs', 0)}")
            print(f"  context_stats engineering_bytes p50: "
                  f"{context_stats.get('engineering_context_bytes_p50')}")
    if rcx_gate is not None:
        _print_rcx_gate(rcx_gate, since=since)
    publish_summary = metrics.get("publish_summary", {})
    if publish_summary:
        print()
        print("Publish summary (completed jobs):")
        print(f"  completed_jobs: {publish_summary.get('completed_jobs', 0)}")
        print(
            f"  generation_active_count p50: "
            f"{publish_summary.get('generation_active_count_p50')}"
        )
        print(f"  pr_active_count p50: {publish_summary.get('pr_active_count_p50')}")
        print(
            f"  resolution.addressed sum: "
            f"{publish_summary.get('resolution_addressed_sum', 0)}"
        )
        print(
            f"  transitions_addressed sum: "
            f"{publish_summary.get('transitions_addressed_sum', 0)}"
        )
        print(
            f"  denominator_active_prior sum: "
            f"{publish_summary.get('denominator_active_prior_sum', 0)}"
        )
    if args.rcx_gate and rcx_gate is not None and not rcx_gate.get("passed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
