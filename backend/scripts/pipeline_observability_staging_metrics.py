# backend/scripts/pipeline_observability_staging_metrics.py
"""Staging metrics for pipeline observability (P0 schema + P4 SLO probes)."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import asyncpg

from scripts.staging_metrics_common import (
    StagingScope,
    database_name,
    model_breakdown_sql,
    parse_since,
    review_run_pr_join,
    scope_query_args,
    ssl_context,
    staging_database_url,
)

_EXPECTED_ALEMBIC = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot"
_ALEMBIC_SQL = "SELECT version_num FROM alembic_version LIMIT 1;"
_ATTEMPTS_TABLE_SQL = """
SELECT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 'public' AND table_name = 'github_llm_call_attempts'
) AS exists;
"""


def _review_runs_sql(scope: StagingScope) -> str:
    join, where = review_run_pr_join(scope)
    return f"""
SELECT count(*)::int AS total_runs,
       count(*) FILTER (WHERE rr.status = 'completed')::int AS completed_runs,
       count(*) FILTER (WHERE rr.status = 'failed')::int AS failed_runs,
       count(*) FILTER (WHERE rr.trigger_source IS NOT NULL)::int AS with_trigger_source,
       count(*) FILTER (WHERE rr.timing_stats IS NOT NULL)::int AS with_timing_stats,
       count(*) FILTER (WHERE rr.timing_stats->>'retrieve_ms' IS NOT NULL)::int AS with_retrieve_ms,
       count(*) FILTER (WHERE rr.failure_class IS NOT NULL)::int AS with_failure_class,
       count(*) FILTER (WHERE rr.failure_stage IS NOT NULL)::int AS with_failure_stage
{join}
WHERE {where};
"""


def _attempts_sql(scope: StagingScope) -> str:
    if scope.pr_scoped:
        return """
SELECT count(*)::int AS attempt_rows,
       count(DISTINCT a.review_run_id)::int AS review_runs_with_attempts,
       count(*) FILTER (WHERE a.step_type = 'review')::int AS review_step_attempts,
       count(*) FILTER (WHERE a.step_type = 'index_embed')::int AS index_embed_attempts,
       count(*) FILTER (WHERE a.failure_class IS NOT NULL)::int AS failed_attempts,
       count(*) FILTER (WHERE a.failure_class = 'timeout')::int AS timeout_attempts,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY a.wait_ms)
         FILTER (WHERE a.step_type = 'review' AND a.wait_ms IS NOT NULL)::int AS review_wait_ms_p50,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY a.wait_ms)
         FILTER (WHERE a.step_type = 'review' AND a.wait_ms IS NOT NULL)::int AS review_wait_ms_p95,
       count(*) FILTER (WHERE a.http_status IS NOT NULL)::int AS with_http_status
FROM github_llm_call_attempts a
JOIN github_review_runs rr ON rr.id = a.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1 AND pr.number = $2
  AND ($3::timestamptz IS NULL OR a.started_at >= $3::timestamptz);
"""
    return """
SELECT count(*)::int AS attempt_rows,
       count(DISTINCT review_run_id)::int AS review_runs_with_attempts,
       count(*) FILTER (WHERE step_type = 'review')::int AS review_step_attempts,
       count(*) FILTER (WHERE step_type = 'index_embed')::int AS index_embed_attempts,
       count(*) FILTER (WHERE failure_class IS NOT NULL)::int AS failed_attempts,
       count(*) FILTER (WHERE failure_class = 'timeout')::int AS timeout_attempts,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY wait_ms)
         FILTER (WHERE step_type = 'review' AND wait_ms IS NOT NULL)::int AS review_wait_ms_p50,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY wait_ms)
         FILTER (WHERE step_type = 'review' AND wait_ms IS NOT NULL)::int AS review_wait_ms_p95,
       count(*) FILTER (WHERE http_status IS NOT NULL)::int AS with_http_status
FROM github_llm_call_attempts
WHERE ($1::timestamptz IS NULL OR started_at >= $1::timestamptz);
"""


def _taxonomy_sql(scope: StagingScope) -> str:
    if scope.pr_scoped:
        return """
SELECT coalesce(a.failure_class, '(success)') AS failure_class, count(*)::int AS n
FROM github_llm_call_attempts a
JOIN github_review_runs rr ON rr.id = a.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1 AND pr.number = $2
  AND ($3::timestamptz IS NULL OR a.started_at >= $3::timestamptz)
GROUP BY 1 ORDER BY n DESC;
"""
    return """
SELECT coalesce(failure_class, '(success)') AS failure_class, count(*)::int AS n
FROM github_llm_call_attempts
WHERE ($1::timestamptz IS NULL OR started_at >= $1::timestamptz)
GROUP BY 1 ORDER BY n DESC;
"""


def _evaluate_po_p0_gate(metrics: dict[str, Any], *, require_runs: bool) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    alembic = metrics.get("alembic_version")
    if alembic == _EXPECTED_ALEMBIC:
        add("alembic_0032", "PASS", alembic)
    else:
        add("alembic_0032", "FAIL", f"expected {_EXPECTED_ALEMBIC!r}, got {alembic!r}")

    if metrics.get("attempts_table_exists"):
        add("attempts_table", "PASS", "github_llm_call_attempts present")
    else:
        add("attempts_table", "FAIL", "table missing")

    review = metrics.get("review_runs", {})
    total = int(review.get("total_runs") or 0)
    missing = "FAIL" if require_runs else "INCONCLUSIVE"
    if total == 0:
        add("observability_columns", missing, "no review runs in scope")
        add("attempt_rows", missing, "no review runs in scope")
    else:
        with_ts = int(review.get("with_timing_stats") or 0)
        with_trigger = int(review.get("with_trigger_source") or 0)
        with_retrieve = int(review.get("with_retrieve_ms") or 0)
        if with_ts > 0 and with_trigger > 0 and with_retrieve > 0:
            add(
                "observability_columns",
                "PASS",
                f"timing_stats={with_ts}/{total} trigger_source={with_trigger}/{total} retrieve_ms={with_retrieve}/{total}",
            )
        else:
            add(
                "observability_columns",
                "FAIL",
                f"timing_stats={with_ts}/{total} trigger_source={with_trigger}/{total} retrieve_ms={with_retrieve}/{total}",
            )
        attempts = int(metrics.get("attempts", {}).get("attempt_rows") or 0)
        if attempts > 0:
            add("attempt_rows", "PASS", f"{attempts} rows in scope")
        else:
            add(
                "attempt_rows",
                "INCONCLUSIVE",
                "P0 success path uninstrumented until P1; timeout rows optional",
            )

    passed = all(c["status"] in ("PASS", "INCONCLUSIVE") for c in checks)
    failed = any(c["status"] == "FAIL" for c in checks)
    return {"passed": passed and not failed, "checks": checks}


def _evaluate_po_gate(metrics: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    attempts = metrics.get("attempts", {})
    review_attempts = int(attempts.get("review_step_attempts") or 0)
    if review_attempts == 0:
        add("review_wait_p95", "INCONCLUSIVE", "no review-step attempts in scope")
        add("failure_taxonomy", "INCONCLUSIVE", "no attempts in scope")
    else:
        p95 = attempts.get("review_wait_ms_p95")
        if p95 is not None:
            add("review_wait_p95", "PASS", f"p95={p95}ms n={review_attempts}")
        else:
            add("review_wait_p95", "INCONCLUSIVE", "wait_ms not populated yet")
        if metrics.get("failure_taxonomy"):
            add("failure_taxonomy", "PASS", f"{len(metrics['failure_taxonomy'])} classes")
        else:
            add("failure_taxonomy", "INCONCLUSIVE", "empty taxonomy")

    passed = all(c["status"] in ("PASS", "INCONCLUSIVE") for c in checks)
    failed = any(c["status"] == "FAIL" for c in checks)
    return {"passed": passed and not failed, "checks": checks}


async def _fetch_metrics(scope: StagingScope) -> dict[str, Any]:
    args = scope_query_args(scope)
    conn = await asyncpg.connect(staging_database_url(), ssl=ssl_context())
    try:
        alembic_row = await conn.fetchrow(_ALEMBIC_SQL)
        table_row = await conn.fetchrow(_ATTEMPTS_TABLE_SQL)
        review_row = await conn.fetchrow(_review_runs_sql(scope), *args)
        attempts_row = await conn.fetchrow(_attempts_sql(scope), *args)
        taxonomy_rows = await conn.fetch(_taxonomy_sql(scope), *args)
        breakdown_rows = await conn.fetch(model_breakdown_sql(scope), *args)
    finally:
        await conn.close()

    return {
        "database": database_name(),
        "since": scope.since.isoformat() if scope.since else None,
        "repo_full_name": scope.repo_full_name,
        "pr_number": scope.pr_number,
        "alembic_version": alembic_row["version_num"] if alembic_row else None,
        "attempts_table_exists": bool(table_row["exists"]) if table_row else False,
        "review_runs": dict(review_row) if review_row else {},
        "attempts": dict(attempts_row) if attempts_row else {},
        "failure_taxonomy": [dict(row) for row in taxonomy_rows],
        "model_breakdown": [dict(row) for row in breakdown_rows],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline observability staging metrics")
    parser.add_argument("--since", help="ISO timestamp — deploy completion (required for dogfood)")
    parser.add_argument("--repo", default="raimondskrauklis/revy")
    parser.add_argument("--pr-number", type=int, help="Scope to dogfood PR (recommended)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--po-p0-gate", action="store_true")
    parser.add_argument("--po-gate", action="store_true")
    parser.add_argument(
        "--require-runs",
        action="store_true",
        help="Dogfood mode: FAIL when no review runs in scope",
    )
    return parser.parse_args()


async def _run() -> int:
    args = _parse_args()
    scope = StagingScope(
        since=parse_since(args.since),
        repo_full_name=args.repo if args.pr_number else None,
        pr_number=args.pr_number,
    )
    metrics = await _fetch_metrics(scope)
    exit_code = 0
    if args.po_p0_gate:
        p0_gate = _evaluate_po_p0_gate(metrics, require_runs=args.require_runs)
        metrics["po_p0_gate"] = p0_gate
        if not p0_gate.get("passed"):
            exit_code = 1
    if args.po_gate:
        po_gate = _evaluate_po_gate(metrics)
        metrics["po_gate"] = po_gate
        if not po_gate.get("passed"):
            exit_code = 1
    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
        return exit_code
    print("Pipeline observability — staging metrics")
    print(f"  database: {metrics['database']}")
    if scope.pr_scoped:
        print(f"  pr: {scope.repo_full_name}#{scope.pr_number}")
    if scope.since:
        print(f"  since: {scope.since.isoformat()}")
    print(json.dumps(metrics["review_runs"], indent=2))
    return exit_code


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
