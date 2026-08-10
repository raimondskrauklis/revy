# backend/scripts/staging_metrics_common.py
"""Shared helpers for staging metrics scripts."""
from __future__ import annotations

import os
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class StagingScope:
    since: datetime | None = None
    repo_full_name: str | None = None
    pr_number: int | None = None

    @property
    def pr_scoped(self) -> bool:
        return self.repo_full_name is not None and self.pr_number is not None


def staging_database_url() -> str:
    url = os.environ.get("PRODUCTION_DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "PRODUCTION_DATABASE_URL not set — add revy-staging URL to backend/.env"
        )
    return url.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]


def ssl_context() -> ssl.SSLContext | bool:
    if os.environ.get("DATABASE_SSL_INSECURE", "").strip().lower() in ("1", "true", "yes"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


def parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def database_name() -> str:
    return urlparse(staging_database_url()).path.lstrip("/")


def review_run_pr_join(scope: StagingScope) -> tuple[str, str]:
    """Return (FROM/JOIN clause, extra WHERE) for review_run-scoped queries."""
    if not scope.pr_scoped:
        return "FROM github_review_runs rr", "($1::timestamptz IS NULL OR rr.created_at >= $1::timestamptz)"
    return (
        """
FROM github_review_runs rr
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
""".strip(),
        "repo.full_name = $1 AND pr.number = $2 AND ($3::timestamptz IS NULL OR rr.created_at >= $3::timestamptz)",
    )


def index_job_pr_join(scope: StagingScope) -> tuple[str, str]:
    if not scope.pr_scoped:
        return "FROM github_index_jobs ij", "($1::timestamptz IS NULL OR ij.created_at >= $1::timestamptz)"
    return (
        """
FROM github_index_jobs ij
JOIN github_pull_request_revisions rev ON rev.id = ij.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
""".strip(),
        "repo.full_name = $1 AND pr.number = $2 AND ($3::timestamptz IS NULL OR ij.created_at >= $3::timestamptz)",
    )


def pipeline_run_pr_join(scope: StagingScope) -> tuple[str, str]:
    if not scope.pr_scoped:
        return (
            "FROM github_pipeline_runs pr",
            "($1::timestamptz IS NULL OR pr.created_at >= $1::timestamptz)",
        )
    return (
        """
FROM github_pipeline_runs pr
JOIN github_pull_request_revisions rev ON rev.id = pr.revision_id
JOIN github_pull_requests gp ON gp.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = gp.repository_id
""".strip(),
        "repo.full_name = $1 AND gp.number = $2 AND ($3::timestamptz IS NULL OR pr.created_at >= $3::timestamptz)",
    )


def scope_query_args(scope: StagingScope) -> tuple:
    if scope.pr_scoped:
        return (scope.repo_full_name, scope.pr_number, scope.since)
    return (scope.since,)


def model_breakdown_sql(scope: StagingScope) -> str:
    if scope.pr_scoped:
        return """
SELECT a.step_type,
       coalesce(a.provider, '(null)') AS provider,
       coalesce(a.request_model, '(null)') AS request_model,
       count(*)::int AS n
FROM github_llm_call_attempts a
JOIN github_pipeline_runs pr ON pr.id = a.pipeline_run_id
JOIN github_pull_request_revisions rev ON rev.id = pr.revision_id
JOIN github_pull_requests gp ON gp.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = gp.repository_id
WHERE repo.full_name = $1 AND gp.number = $2
  AND ($3::timestamptz IS NULL OR a.started_at >= $3::timestamptz)
GROUP BY 1, 2, 3
ORDER BY n DESC, a.step_type, provider, request_model;
"""
    return """
SELECT step_type,
       coalesce(provider, '(null)') AS provider,
       coalesce(request_model, '(null)') AS request_model,
       count(*)::int AS n
FROM github_llm_call_attempts
WHERE ($1::timestamptz IS NULL OR started_at >= $1::timestamptz)
GROUP BY 1, 2, 3
ORDER BY n DESC, step_type, provider, request_model;
"""
