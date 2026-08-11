# backend/scripts/model_run_capture_staging_metrics.py
"""Staging metrics for model-run-capture (MRC-P0/P1/P2)."""
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
    pipeline_run_pr_join,
    scope_query_args,
    ssl_context,
    staging_database_url,
)

_EXPECTED_ALEMBIC = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot"
_ALEMBIC_SQL = "SELECT version_num FROM alembic_version LIMIT 1;"
_MODELS_SNAPSHOT_COLUMN_SQL = """
SELECT EXISTS (
  SELECT 1 FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name = 'github_pipeline_runs'
    AND column_name = 'models_snapshot'
) AS exists;
"""


def _pr_extra_join(scope: StagingScope) -> str:
    if not scope.pr_scoped:
        return ""
    return """
JOIN github_pull_request_revisions rev ON rev.id = pr.revision_id
JOIN github_pull_requests gp ON gp.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = gp.repository_id
"""


def _index_identity_sql(scope: StagingScope) -> str:
    _, where = pipeline_run_pr_join(scope)
    return f"""
WITH index_manifests AS (
  SELECT pr.id AS pipeline_run_id,
         coalesce((a.content_json->>'embed_batches')::int, 0) AS embed_batches,
         a.content_json->>'embedding_model' AS embedding_model,
         s.model_provider,
         s.model_id
  FROM github_pipeline_artifacts a
  JOIN github_pipeline_steps s ON s.id = a.step_id AND s.step_type = 'index'
  JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
  {_pr_extra_join(scope)}
  WHERE a.kind = 'manifest'
    AND {where}
)
SELECT count(*)::int AS index_runs,
       count(*) FILTER (WHERE embed_batches > 0)::int AS with_embed,
       count(*) FILTER (WHERE embed_batches = 0)::int AS reuse_only,
       count(*) FILTER (
         WHERE embed_batches > 0 AND embedding_model IS NOT NULL
       )::int AS embed_with_model_in_manifest,
       count(*) FILTER (
         WHERE embed_batches > 0
           AND model_provider = 'voyage'
           AND model_id = embedding_model
       )::int AS embed_step_model_match,
       count(*) FILTER (
         WHERE embed_batches = 0
           AND embedding_model IS NULL
           AND model_provider IS NULL
       )::int AS reuse_null_semantics,
       count(*) FILTER (
         WHERE embed_batches = 0 AND embedding_model IS NOT NULL
       )::int AS reuse_false_model
FROM index_manifests;
"""


def _index_embed_attempts_sql(scope: StagingScope) -> str:
    if scope.pr_scoped:
        return """
SELECT count(*)::int AS index_embed_attempts,
       count(*) FILTER (WHERE a.request_model IS NOT NULL)::int AS with_request_model,
       count(*) FILTER (WHERE a.provider = 'voyage')::int AS voyage_provider,
       count(DISTINCT a.request_model)::int AS distinct_request_models
FROM github_llm_call_attempts a
JOIN github_index_jobs ij ON ij.id = a.index_job_id
JOIN github_pull_request_revisions rev ON rev.id = ij.revision_id
JOIN github_pull_requests gp ON gp.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = gp.repository_id
WHERE a.step_type = 'index_embed'
  AND repo.full_name = $1 AND gp.number = $2
  AND ($3::timestamptz IS NULL OR a.started_at >= $3::timestamptz);
"""
    return """
SELECT count(*)::int AS index_embed_attempts,
       count(*) FILTER (WHERE request_model IS NOT NULL)::int AS with_request_model,
       count(*) FILTER (WHERE provider = 'voyage')::int AS voyage_provider,
       count(DISTINCT request_model)::int AS distinct_request_models
FROM github_llm_call_attempts
WHERE step_type = 'index_embed'
  AND ($1::timestamptz IS NULL OR started_at >= $1::timestamptz);
"""


def _embed_model_parity_sql(scope: StagingScope) -> str:
    if scope.pr_scoped:
        return """
WITH manifest_models AS (
  SELECT DISTINCT ij.id AS index_job_id,
         a.content_json->>'embedding_model' AS embedding_model,
         coalesce((a.content_json->>'embed_batches')::int, 0) AS embed_batches
  FROM github_index_jobs ij
  JOIN github_pipeline_runs pr ON pr.index_job_id = ij.id
  JOIN github_pipeline_steps s ON s.pipeline_run_id = pr.id AND s.step_type = 'index'
  JOIN github_pipeline_artifacts a ON a.step_id = s.id AND a.kind = 'manifest'
  JOIN github_pull_request_revisions rev ON rev.id = ij.revision_id
  JOIN github_pull_requests gp ON gp.id = rev.pull_request_id
  JOIN github_repositories repo ON repo.id = gp.repository_id
  WHERE repo.full_name = $1 AND gp.number = $2
    AND ($3::timestamptz IS NULL OR ij.created_at >= $3::timestamptz)
),
attempt_models AS (
  SELECT a.index_job_id,
         bool_and(a.request_model = mm.embedding_model) AS models_match
  FROM github_llm_call_attempts a
  JOIN manifest_models mm ON mm.index_job_id = a.index_job_id
  WHERE a.step_type = 'index_embed'
    AND mm.embed_batches > 0
    AND mm.embedding_model IS NOT NULL
  GROUP BY a.index_job_id
)
SELECT count(*)::int AS embed_jobs_with_attempts,
       count(*) FILTER (WHERE models_match)::int AS parity_pass,
       count(*) FILTER (WHERE NOT models_match)::int AS parity_fail
FROM attempt_models;
"""
    return """
WITH manifest_models AS (
  SELECT DISTINCT ij.id AS index_job_id,
         a.content_json->>'embedding_model' AS embedding_model,
         coalesce((a.content_json->>'embed_batches')::int, 0) AS embed_batches
  FROM github_index_jobs ij
  JOIN github_pipeline_runs pr ON pr.index_job_id = ij.id
  JOIN github_pipeline_steps s ON s.pipeline_run_id = pr.id AND s.step_type = 'index'
  JOIN github_pipeline_artifacts a ON a.step_id = s.id AND a.kind = 'manifest'
  WHERE ($1::timestamptz IS NULL OR ij.created_at >= $1::timestamptz)
),
attempt_models AS (
  SELECT a.index_job_id,
         bool_and(a.request_model = mm.embedding_model) AS models_match
  FROM github_llm_call_attempts a
  JOIN manifest_models mm ON mm.index_job_id = a.index_job_id
  WHERE a.step_type = 'index_embed'
    AND mm.embed_batches > 0
    AND mm.embedding_model IS NOT NULL
  GROUP BY a.index_job_id
)
SELECT count(*)::int AS embed_jobs_with_attempts,
       count(*) FILTER (WHERE models_match)::int AS parity_pass,
       count(*) FILTER (WHERE NOT models_match)::int AS parity_fail
FROM attempt_models;
"""


def _step_models_sql(scope: StagingScope) -> str:
    _, where = pipeline_run_pr_join(scope)
    return f"""
SELECT s.step_type,
       count(*)::int AS total_steps,
       count(*) FILTER (
         WHERE s.model_provider IS NOT NULL AND s.model_id IS NOT NULL
       )::int AS with_model_fields
FROM github_pipeline_steps s
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
{_pr_extra_join(scope)}
WHERE s.status = 'completed'
  AND s.step_type IN ('review', 'judge', 'publish')
  AND {where}
GROUP BY s.step_type
ORDER BY s.step_type;
"""


def _models_snapshot_sql(scope: StagingScope) -> str:
    join, where = pipeline_run_pr_join(scope)
    return f"""
SELECT count(*)::int AS pipeline_runs,
       count(*) FILTER (WHERE pr.models_snapshot IS NOT NULL)::int AS with_snapshot
{join}
WHERE {where};
"""


def _evaluate_mrc_p0_gate(metrics: dict[str, Any], *, require_runs: bool) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    alembic = metrics.get("alembic_version")
    if alembic == _EXPECTED_ALEMBIC:
        add("alembic_0032", "PASS", alembic)
    else:
        add("alembic_0032", "FAIL", f"expected {_EXPECTED_ALEMBIC!r}, got {alembic!r}")

    if metrics.get("models_snapshot_column_exists"):
        add("models_snapshot_column", "PASS", "github_pipeline_runs.models_snapshot present")
    else:
        add("models_snapshot_column", "FAIL", "column missing")

    index = metrics.get("index_identity", {})
    with_embed = int(index.get("with_embed") or 0)
    missing = "FAIL" if require_runs else "INCONCLUSIVE"
    if with_embed == 0:
        add("index_embedding_manifest", missing, "no embed runs in scope")
        add("index_step_model", missing, "no embed runs in scope")
    else:
        manifest_ok = int(index.get("embed_with_model_in_manifest") or 0)
        step_ok = int(index.get("embed_step_model_match") or 0)
        false_model = int(index.get("reuse_false_model") or 0)
        if manifest_ok == with_embed and step_ok == with_embed and false_model == 0:
            add(
                "index_embedding_manifest",
                "PASS",
                f"manifest model on {manifest_ok}/{with_embed} embed runs",
            )
            add(
                "index_step_model",
                "PASS",
                f"voyage step model on {step_ok}/{with_embed} embed runs",
            )
        else:
            add(
                "index_embedding_manifest",
                "FAIL",
                f"manifest={manifest_ok}/{with_embed} step={step_ok}/{with_embed} false_reuse={false_model}",
            )
            add("index_step_model", "FAIL", "see index_embedding_manifest detail")

    passed = all(c["status"] in ("PASS", "INCONCLUSIVE") for c in checks)
    failed = any(c["status"] == "FAIL" for c in checks)
    return {"passed": passed and not failed, "checks": checks}


def _evaluate_mrc_p1_gate(metrics: dict[str, Any], *, require_runs: bool) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str = "") -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    attempts = metrics.get("index_embed_attempts", {})
    embed_attempts = int(attempts.get("index_embed_attempts") or 0)
    parity = metrics.get("embed_model_parity", {})
    parity_fail = int(parity.get("parity_fail") or 0)
    missing = "FAIL" if require_runs else "INCONCLUSIVE"

    index = metrics.get("index_identity", {})
    with_embed = int(index.get("with_embed") or 0)
    if with_embed == 0:
        add("index_embed_attempts", missing, "no embed runs in scope")
        add("embed_model_parity", missing, "no embed runs in scope")
    elif embed_attempts == 0:
        add("index_embed_attempts", "FAIL", "embed ran but no index_embed attempt rows")
        add("embed_model_parity", "INCONCLUSIVE", "no attempt rows")
    else:
        with_model = int(attempts.get("with_request_model") or 0)
        add(
            "index_embed_attempts",
            "PASS" if with_model == embed_attempts else "FAIL",
            f"{with_model}/{embed_attempts} with request_model",
        )
        parity_pass = int(parity.get("parity_pass") or 0)
        if parity_fail == 0 and parity_pass > 0:
            add("embed_model_parity", "PASS", f"{parity_pass} jobs manifest=attempt model")
        elif parity_fail > 0:
            add("embed_model_parity", "FAIL", f"parity_fail={parity_fail}")
        else:
            add("embed_model_parity", "INCONCLUSIVE", "no parity rows yet")

    step_models = {row["step_type"]: row for row in metrics.get("step_models", [])}
    for step_type in ("judge", "publish"):
        row = step_models.get(step_type)
        if row is None:
            add(f"{step_type}_step_model", "INCONCLUSIVE", f"no completed {step_type} steps")
            continue
        total = int(row.get("total_steps") or 0)
        with_model = int(row.get("with_model_fields") or 0)
        if total == 0:
            add(f"{step_type}_step_model", "INCONCLUSIVE", f"no completed {step_type} steps")
        elif with_model == total:
            add(f"{step_type}_step_model", "PASS", f"{with_model}/{total} with model fields")
        else:
            add(f"{step_type}_step_model", "FAIL", f"{with_model}/{total} with model fields")

    snapshot = metrics.get("models_snapshot", {})
    runs = int(snapshot.get("pipeline_runs") or 0)
    populated = int(snapshot.get("with_snapshot") or 0)
    if runs == 0:
        add("models_snapshot_populated", "INCONCLUSIVE", "no pipeline runs in scope")
    elif populated == 0:
        add(
            "models_snapshot_populated",
            "INCONCLUSIVE",
            "column present — terminal writer ships in MRC-P2.2",
        )
    else:
        add("models_snapshot_populated", "PASS", f"{populated}/{runs} runs")

    passed = all(c["status"] in ("PASS", "INCONCLUSIVE") for c in checks)
    failed = any(c["status"] == "FAIL" for c in checks)
    return {"passed": passed and not failed, "checks": checks}


async def _fetch_metrics(scope: StagingScope) -> dict[str, Any]:
    args = scope_query_args(scope)
    conn = await asyncpg.connect(staging_database_url(), ssl=ssl_context())
    try:
        alembic_row = await conn.fetchrow(_ALEMBIC_SQL)
        column_row = await conn.fetchrow(_MODELS_SNAPSHOT_COLUMN_SQL)
        index_row = await conn.fetchrow(_index_identity_sql(scope), *args)
        attempts_row = await conn.fetchrow(_index_embed_attempts_sql(scope), *args)
        parity_row = await conn.fetchrow(_embed_model_parity_sql(scope), *args)
        step_rows = await conn.fetch(_step_models_sql(scope), *args)
        snapshot_row = await conn.fetchrow(_models_snapshot_sql(scope), *args)
        breakdown_rows = await conn.fetch(model_breakdown_sql(scope), *args)
    finally:
        await conn.close()

    return {
        "database": database_name(),
        "since": scope.since.isoformat() if scope.since else None,
        "repo_full_name": scope.repo_full_name,
        "pr_number": scope.pr_number,
        "alembic_version": alembic_row["version_num"] if alembic_row else None,
        "models_snapshot_column_exists": bool(column_row["exists"]) if column_row else False,
        "index_identity": dict(index_row) if index_row else {},
        "index_embed_attempts": dict(attempts_row) if attempts_row else {},
        "embed_model_parity": dict(parity_row) if parity_row else {},
        "step_models": [dict(row) for row in step_rows],
        "models_snapshot": dict(snapshot_row) if snapshot_row else {},
        "model_breakdown": [dict(row) for row in breakdown_rows],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Model run capture staging metrics")
    parser.add_argument("--since", help="ISO timestamp — deploy completion (required for dogfood)")
    parser.add_argument("--repo", default="raimondskrauklis/revy")
    parser.add_argument("--pr-number", type=int, help="Scope to dogfood PR (recommended)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mrc-p0-gate", action="store_true")
    parser.add_argument("--mrc-p1-gate", action="store_true")
    parser.add_argument("--mrc-gate", action="store_true", help="Run P0 + P1 gates")
    parser.add_argument(
        "--require-runs",
        action="store_true",
        help="Dogfood mode: FAIL when no embed runs in scope",
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
    run_p0 = args.mrc_p0_gate or args.mrc_gate
    run_p1 = args.mrc_p1_gate or args.mrc_gate
    if run_p0:
        p0_gate = _evaluate_mrc_p0_gate(metrics, require_runs=args.require_runs)
        metrics["mrc_p0_gate"] = p0_gate
        if not p0_gate.get("passed"):
            exit_code = 1
    if run_p1:
        p1_gate = _evaluate_mrc_p1_gate(metrics, require_runs=args.require_runs)
        metrics["mrc_p1_gate"] = p1_gate
        if not p1_gate.get("passed"):
            exit_code = 1
    if args.json:
        print(json.dumps(metrics, indent=2, default=str))
        return exit_code
    print("Model run capture — staging metrics")
    print(f"  database: {metrics['database']}")
    if scope.pr_scoped:
        print(f"  pr: {scope.repo_full_name}#{scope.pr_number}")
    if scope.since:
        print(f"  since: {scope.since.isoformat()}")
    print(json.dumps(metrics["index_identity"], indent=2))
    return exit_code


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
