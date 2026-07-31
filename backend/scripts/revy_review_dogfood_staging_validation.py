# backend/scripts/revy_review_dogfood_staging_validation.py
"""RR-W1 staging validation — DB evidence for closure-loop dogfood on revy repo PRs."""
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

_ALEMBIC_SQL = "SELECT version_num FROM alembic_version LIMIT 1;"

_PR_REVISIONS_SQL = """
SELECT rev.id::text AS revision_id,
       rev.head_sha,
       rev.revision_number,
       rev.created_at,
       (SELECT count(*)::int
        FROM github_pull_request_revisions r2
        WHERE r2.pull_request_id = pr.id
          AND r2.head_sha = rev.head_sha) AS rows_per_head_sha
FROM github_pull_request_revisions rev
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1
  AND pr.number = $2
  AND ($3::timestamptz IS NULL OR rev.created_at >= $3::timestamptz)
ORDER BY rev.revision_number ASC;
"""

_REVIEW_RUNS_SQL = """
SELECT rr.id::text AS review_run_id,
       rr.status,
       rr.error_message,
       rr.judge_status,
       rr.judge_escalation_candidate_count,
       rev.head_sha,
       rev.revision_number,
       rr.created_at,
       (SELECT count(*)::int
        FROM github_finding_judge_outcomes o
        WHERE o.review_run_id = rr.id) AS judge_outcomes,
       pj.status AS publish_status,
       pj.head_sha AS publish_head_sha
FROM github_review_runs rr
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
LEFT JOIN github_publish_jobs pj ON pj.review_run_id = rr.id
WHERE repo.full_name = $1
  AND pr.number = $2
  AND ($3::timestamptz IS NULL OR rr.created_at >= $3::timestamptz)
ORDER BY rr.created_at ASC;
"""

_FINDING_GROUPS_SQL = """
SELECT g.id::text AS group_id,
       g.fingerprint,
       g.state,
       g.severity,
       g.category,
       g.resolution_status,
       g.resolution_method,
       g.closure_blocked_reason,
       g.file_path,
       g.last_seen_revision_id::text AS last_seen_revision_id,
       g.resolved_at_revision_id::text AS resolved_at_revision_id
FROM github_finding_groups g
JOIN github_pull_requests pr ON pr.id = g.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1
  AND pr.number = $2
ORDER BY g.fingerprint, g.created_at;
"""

_RESOLUTION_PASS_SQL = """
SELECT rev.head_sha,
       rev.revision_number,
       a.content_json->'resolution_pass' AS resolution_pass,
       rr.id::text AS review_run_id,
       a.created_at
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
JOIN github_pipeline_runs prun ON prun.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = prun.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1
  AND pr.number = $2
  AND s.step_type = 'reconcile'
  AND a.kind = 'manifest'
  AND ($3::timestamptz IS NULL OR a.created_at >= $3::timestamptz)
ORDER BY a.created_at ASC;
"""

_PUBLISH_SUMMARY_SQL = """
SELECT pj.summary_json,
       rev.head_sha,
       rev.revision_number,
       pj.status
FROM github_publish_jobs pj
JOIN github_review_runs rr ON rr.id = pj.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
WHERE repo.full_name = $1
  AND pr.number = $2
  AND pj.status = 'completed'
  AND ($3::timestamptz IS NULL OR pj.created_at >= $3::timestamptz)
ORDER BY pj.created_at ASC;
"""


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


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _json_load(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


def _evaluate_rr_v_gates(metrics: dict[str, Any]) -> dict[str, Any]:
    revisions = metrics.get("revisions", [])
    review_runs = metrics.get("review_runs", [])
    resolution_passes = metrics.get("resolution_passes", [])
    publish_jobs = metrics.get("publish_jobs", [])
    finding_groups = metrics.get("finding_groups", [])

    completed_runs = [r for r in review_runs if r.get("status") == "completed"]
    failed_runs = [r for r in review_runs if r.get("status") == "failed"]
    duplicate_sha_rows = [r for r in revisions if (r.get("rows_per_head_sha") or 0) > 1]

    judge_runs = [
        r
        for r in completed_runs
        if (r.get("judge_escalation_candidate_count") or 0) > 0
    ]
    judge_with_outcomes = [r for r in judge_runs if (r.get("judge_outcomes") or 0) > 0]

    addressed_passes = [
        rp
        for rp in resolution_passes
        if (rp.get("resolution_pass") or {}).get("transitions_addressed", 0) > 0
        or (rp.get("resolution_pass") or {}).get("resolution_rate_pct", 0) > 0
    ]

    publish_mismatches = [
        r
        for r in completed_runs
        if r.get("publish_status") == "completed"
        and r.get("publish_head_sha")
        and r.get("publish_head_sha") != r.get("head_sha")
    ]

    resolved_groups = [g for g in finding_groups if g.get("state") == "resolved"]
    addressed_groups = [g for g in finding_groups if g.get("resolution_status") == "addressed"]

    checks: list[dict[str, Any]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if duplicate_sha_rows:
        add(
            "RR-V1_revision_idempotency",
            "FAIL",
            f"duplicate head_sha rows: {len(duplicate_sha_rows)}",
        )
    elif len(revisions) >= 2:
        add(
            "RR-V1_revision_idempotency",
            "PASS",
            f"{len(revisions)} revisions; rows_per_head_sha=1 each",
        )
    else:
        add(
            "RR-V1_revision_idempotency",
            "PENDING",
            f"need >=2 revisions; have {len(revisions)}",
        )

    if len(completed_runs) >= 5 and addressed_passes:
        add(
            "RR-V2_resolution_stamp",
            "PASS",
            f"{len(completed_runs)} completed runs; "
            f"{len(addressed_passes)} reconcile passes with addressed/rate>0",
        )
    elif len(completed_runs) >= 5:
        add(
            "RR-V2_resolution_stamp",
            "PENDING",
            f"{len(completed_runs)} runs but no addressed transition in reconcile manifest",
        )
    else:
        add(
            "RR-V2_resolution_stamp",
            "PENDING",
            f"need >=5 completed review runs; have {len(completed_runs)} "
            f"(failed={len(failed_runs)})",
        )

    completed_publishes = [
        r
        for r in completed_runs
        if r.get("publish_status") == "completed"
        and r.get("publish_head_sha")
        and r.get("publish_head_sha") == r.get("head_sha")
    ]

    if publish_mismatches:
        add(
            "RR-V3_publish_head_sha_parity",
            "FAIL",
            f"{len(publish_mismatches)} publish head_sha mismatches",
        )
    elif completed_publishes:
        add(
            "RR-V3_publish_head_sha_parity",
            "PASS",
            f"{len(completed_publishes)} completed publishes match revision head_sha",
        )
    else:
        add(
            "RR-V3_publish_head_sha_parity",
            "PENDING",
            "need >=1 completed publish with matching head_sha",
        )

    thread_issues = []
    for job in publish_jobs:
        skipped = job.get("thread_resolve_skipped") or {}
        if isinstance(skipped, dict):
            for key, count in skipped.items():
                if key != "already_resolved" and (count or 0) > 0:
                    thread_issues.append(f"{key}={count}")
    if thread_issues:
        add(
            "RR-V4_thread_resolve_taxonomy",
            "PENDING",
            f"non-zero skip counters: {', '.join(thread_issues)}",
        )
    elif publish_jobs:
        add(
            "RR-V4_thread_resolve_taxonomy",
            "PASS",
            "thread_resolve_skipped counters zero or absent on completed publishes",
        )
    else:
        add("RR-V4_thread_resolve_taxonomy", "PENDING", "no completed publish jobs yet")

    if judge_runs and judge_with_outcomes:
        add(
            "judge_transport",
            "PASS",
            f"{len(judge_with_outcomes)}/{len(judge_runs)} escalation runs persisted outcomes",
        )
    elif judge_runs:
        add(
            "judge_transport",
            "FAIL",
            f"{len(judge_runs)} escalation runs but 0 judge outcomes persisted",
        )
    else:
        add(
            "judge_transport",
            "PENDING",
            "no judge escalation candidates yet (need error/security findings)",
        )

    if resolved_groups or addressed_groups:
        add(
            "finding_groups_closure",
            "PASS",
            f"resolved={len(resolved_groups)} addressed_status={len(addressed_groups)}",
        )
    else:
        add(
            "finding_groups_closure",
            "PENDING",
            "no resolved/addressed finding groups on PR yet",
        )

    passed = all(c["status"] == "PASS" for c in checks)
    pending = any(c["status"] == "PENDING" for c in checks)
    return {
        "passed": passed and not pending,
        "ready_for_signoff": passed and not pending,
        "checks": checks,
    }


async def _fetch_metrics(
    *,
    repo_full_name: str,
    pr_number: int,
    since: datetime | None,
) -> dict[str, Any]:
    conn = await asyncpg.connect(_staging_database_url(), ssl=_ssl_context())
    try:
        alembic_row = await conn.fetchrow(_ALEMBIC_SQL)
        revision_rows = await conn.fetch(_PR_REVISIONS_SQL, repo_full_name, pr_number, since)
        review_rows = await conn.fetch(_REVIEW_RUNS_SQL, repo_full_name, pr_number, since)
        group_rows = await conn.fetch(_FINDING_GROUPS_SQL, repo_full_name, pr_number)
        resolution_rows = await conn.fetch(
            _RESOLUTION_PASS_SQL, repo_full_name, pr_number, since
        )
        publish_rows = await conn.fetch(_PUBLISH_SUMMARY_SQL, repo_full_name, pr_number, since)
    finally:
        await conn.close()

    revisions = [dict(row) for row in revision_rows]
    review_runs = [dict(row) for row in review_rows]
    finding_groups = [dict(row) for row in group_rows]
    resolution_passes = []
    for row in resolution_rows:
        payload = dict(row)
        payload["resolution_pass"] = _json_load(payload.get("resolution_pass"))
        resolution_passes.append(payload)

    publish_jobs = []
    for row in publish_rows:
        summary = _json_load(row["summary_json"])
        publish_jobs.append(
            {
                "head_sha": row["head_sha"],
                "revision_number": row["revision_number"],
                "status": row["status"],
                "thread_resolve_skipped": summary.get("thread_resolve_skipped"),
                "head_contradiction_suppressed_count": summary.get(
                    "head_contradiction_suppressed_count"
                ),
                "inline_publish_422_recovered_count": summary.get(
                    "inline_publish_422_recovered_count"
                ),
            }
        )

    metrics: dict[str, Any] = {
        "database": urlparse(_staging_database_url()).path.lstrip("/"),
        "since": since.isoformat() if since else None,
        "alembic_version": alembic_row["version_num"] if alembic_row else None,
        "repo_full_name": repo_full_name,
        "pr_number": pr_number,
        "revisions": revisions,
        "review_runs": review_runs,
        "finding_groups": finding_groups,
        "resolution_passes": resolution_passes,
        "publish_jobs": publish_jobs,
        "summary": {
            "revision_count": len(revisions),
            "completed_review_runs": sum(
                1 for r in review_runs if r.get("status") == "completed"
            ),
            "failed_review_runs": sum(1 for r in review_runs if r.get("status") == "failed"),
            "finding_group_count": len(finding_groups),
            "resolved_group_count": sum(
                1 for g in finding_groups if g.get("state") == "resolved"
            ),
        },
    }
    metrics["rr_v_gate"] = _evaluate_rr_v_gates(metrics)
    return metrics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RR-W1 revy-repo staging validation")
    parser.add_argument("--repo", default="raimondskrauklis/revy")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--since", help="ISO timestamp — only rows created at or after")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON")
    parser.add_argument(
        "--rr-v-gate",
        action="store_true",
        help="Exit 1 unless all RR-V checks PASS (no PENDING)",
    )
    return parser.parse_args()


async def _run() -> int:
    args = _parse_args()
    since = _parse_since(args.since)
    metrics = await _fetch_metrics(
        repo_full_name=args.repo,
        pr_number=args.pr_number,
        since=since,
    )
    gate = metrics["rr_v_gate"]

    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print("RR-W1 staging validation")
        print(f"  database: {metrics['database']}")
        print(f"  repo: {args.repo} PR #{args.pr_number}")
        if since:
            print(f"  since: {since.isoformat()}")
        print(f"  revisions: {metrics['summary']['revision_count']}")
        print(f"  completed runs: {metrics['summary']['completed_review_runs']}")
        print(f"  failed runs: {metrics['summary']['failed_review_runs']}")
        print(f"  finding groups: {metrics['summary']['finding_group_count']}")
        print()
        for check in gate["checks"]:
            print(f"  [{check['status']}] {check['name']}: {check['detail']}")
        print(f"  sign-off ready: {gate['ready_for_signoff']}")

    if args.rr_v_gate and not gate.get("ready_for_signoff"):
        return 1
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
