# backend/scripts/generation_lifecycle_staging_metrics.py
"""Staging metrics for review generation lifecycle (RG-15 restart path)."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import asyncpg

from app.constants.github_messages import SUPERSEDED_INDEX_ERROR
from scripts.staging_metrics_common import (
    StagingScope,
    database_name,
    index_job_pr_join,
    parse_since,
    review_run_pr_join,
    scope_query_args,
    ssl_context,
    staging_database_url,
)

_SUPERSEDED_INDEX_ERROR_SQL = SUPERSEDED_INDEX_ERROR.replace("'", "''")

_ALEMBIC_SQL = "SELECT version_num FROM alembic_version LIMIT 1;"


def _review_runs_sql(scope: StagingScope) -> str:
    join, where = review_run_pr_join(scope)
    return f"""
SELECT count(*)::int AS total_runs,
       count(*) FILTER (WHERE rr.status = 'completed')::int AS completed_runs,
       count(*) FILTER (WHERE rr.status = 'failed')::int AS failed_runs,
       count(*) FILTER (WHERE rr.status = 'processing')::int AS processing_runs,
       count(*) FILTER (WHERE rr.status = 'superseded')::int AS superseded_review_runs
{join}
WHERE {where};
"""


def _index_jobs_sql(scope: StagingScope) -> str:
    join, where = index_job_pr_join(scope)
    return f"""
SELECT count(*)::int AS total_jobs,
       count(*) FILTER (WHERE ij.status = 'completed')::int AS completed_jobs,
       count(*) FILTER (
         WHERE ij.status = 'failed' AND ij.error_message = '{_SUPERSEDED_INDEX_ERROR_SQL}'
       )::int AS superseded_index_jobs,
       count(*) FILTER (WHERE ij.status = 'failed')::int AS failed_jobs,
       count(*) FILTER (WHERE ij.status = 'processing')::int AS processing_jobs
{join}
WHERE {where};
"""


def _revisions_sql(scope: StagingScope) -> str:
    if not scope.pr_scoped:
        return """
SELECT count(*)::int AS revision_count,
       count(DISTINCT head_sha)::int AS distinct_head_shas
FROM github_pull_request_revisions rev
WHERE ($1::timestamptz IS NULL OR rev.created_at >= $1::timestamptz);
"""
    return """
SELECT count(*)::int AS revision_count,
       count(DISTINCT rev.head_sha)::int AS distinct_head_shas
FROM github_pull_request_revisions rev
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1 AND pr.number = $2
  AND ($3::timestamptz IS NULL OR rev.created_at >= $3::timestamptz);
"""


def _evaluate_rg15_gate(metrics: dict[str, Any], *, require_activity: bool) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    review = metrics.get("review_runs", {})
    index = metrics.get("index_jobs", {})
    revisions = metrics.get("revisions", {})
    total_runs = int(review.get("total_runs") or 0)
    total_jobs = int(index.get("total_jobs") or 0)
    revision_count = int(revisions.get("revision_count") or 0)
    missing = "FAIL" if require_activity else "INCONCLUSIVE"

    if total_runs == 0 and total_jobs == 0:
        add("pipeline_activity", missing, "no runs or index jobs in scope")
        add("supersede_path", missing, "no activity in scope")
    else:
        add("pipeline_activity", "PASS", f"runs={total_runs} index_jobs={total_jobs}")
        superseded_jobs = int(index.get("superseded_index_jobs") or 0)
        superseded_runs = int(review.get("superseded_review_runs") or 0)
        if superseded_jobs > 0 or superseded_runs > 0:
            add(
                "supersede_path",
                "PASS",
                f"superseded_index_jobs={superseded_jobs} superseded_review_runs={superseded_runs}",
            )
        elif revision_count >= 2:
            add(
                "supersede_path",
                "INCONCLUSIVE",
                f"{revision_count} revisions but no superseded rows — push-2 may have been sequential",
            )
        else:
            add("supersede_path", "INCONCLUSIVE", "need push-2 during active run for RG-15")

    processing_runs = int(review.get("processing_runs") or 0)
    processing_jobs = int(index.get("processing_jobs") or 0)
    if processing_runs == 0 and processing_jobs == 0:
        add("stuck_processing", "PASS", "no orphan processing rows")
    else:
        add(
            "stuck_processing",
            "FAIL",
            f"processing_runs={processing_runs} processing_jobs={processing_jobs}",
        )

    passed = all(c["status"] in ("PASS", "INCONCLUSIVE") for c in checks)
    failed = any(c["status"] == "FAIL" for c in checks)
    return {"passed": passed and not failed, "checks": checks}


async def _fetch_metrics(scope: StagingScope) -> dict[str, Any]:
    args = scope_query_args(scope)
    conn = await asyncpg.connect(staging_database_url(), ssl=ssl_context())
    try:
        alembic_row = await conn.fetchrow(_ALEMBIC_SQL)
        review_row = await conn.fetchrow(_review_runs_sql(scope), *args)
        index_row = await conn.fetchrow(_index_jobs_sql(scope), *args)
        revision_row = await conn.fetchrow(_revisions_sql(scope), *args)
    finally:
        await conn.close()

    return {
        "database": database_name(),
        "since": scope.since.isoformat() if scope.since else None,
        "repo_full_name": scope.repo_full_name,
        "pr_number": scope.pr_number,
        "alembic_version": alembic_row["version_num"] if alembic_row else None,
        "review_runs": dict(review_row) if review_row else {},
        "index_jobs": dict(index_row) if index_row else {},
        "revisions": dict(revision_row) if revision_row else {},
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generation lifecycle staging metrics")
    parser.add_argument("--since", help="ISO timestamp — deploy completion")
    parser.add_argument("--repo", default="raimondskrauklis/revy")
    parser.add_argument("--pr-number", type=int, help="Scope to dogfood PR (recommended)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--rg15-gate", action="store_true")
    parser.add_argument(
        "--require-activity",
        action="store_true",
        help="Dogfood mode: FAIL when no pipeline activity in scope",
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
    if args.rg15_gate:
        rg15_gate = _evaluate_rg15_gate(metrics, require_activity=args.require_activity)
        metrics["rg15_gate"] = rg15_gate
        if not rg15_gate.get("passed"):
            exit_code = 1
    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
        return exit_code
    print(json.dumps(metrics, indent=2, default=str))
    return exit_code


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
