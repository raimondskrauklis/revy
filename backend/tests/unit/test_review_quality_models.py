# backend/tests/unit/test_review_quality_models.py
"""Review-quality RQ0 — ORM columns and enum round-trip."""
from sqlalchemy import inspect

from app.constants.enums import (
    GitHubIndexMode,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
    ResolutionStatus,
)
from app.models import (
    GitHubCodeChunkORM,
    GitHubFindingGroupORM,
    GitHubFindingORM,
    GitHubIndexJobORM,
    GitHubPipelineArtifactORM,
    GitHubPipelineRunORM,
    GitHubPipelineStepORM,
    GitHubPublishJobORM,
    GitHubPullRequestRevisionORM,
)
from app.models.base import Base


def test_review_quality_enums_values():
    assert GitHubIndexMode.diff.value == "diff"
    assert GitHubIndexMode.full.value == "full"
    assert PipelineStepType.retrieve.value == "retrieve"
    assert PipelineArtifactKind.raw_response.value == "raw_response"
    assert PipelineStepStatus.pending.value == "pending"
    assert ResolutionStatus.judge_dismissed.value == "judge_dismissed"


def test_review_quality_tables_registered():
    table_names = Base.metadata.tables.keys()
    assert "github_pipeline_runs" in table_names
    assert "github_pipeline_steps" in table_names
    assert "github_pipeline_artifacts" in table_names


def test_index_job_has_diff_first_columns():
    columns = {column.name for column in inspect(GitHubIndexJobORM).columns}
    assert {"index_mode", "fallback_reason", "warning_message", "index_incremental"} <= columns


def test_revision_has_base_sha():
    columns = {column.name for column in inspect(GitHubPullRequestRevisionORM).columns}
    assert "base_sha" in columns


def test_pipeline_run_links_workspace_with_cascade():
    workspace_fk = next(
        fk for fk in inspect(GitHubPipelineRunORM).columns["workspace_id"].foreign_keys
    )
    assert workspace_fk.target_fullname == "workspaces.id"
    assert workspace_fk.ondelete == "CASCADE"


def test_pipeline_run_optional_fks_set_null_on_delete():
    for column_name in ("index_job_id", "review_run_id", "publish_job_id"):
        fk = next(fk for fk in inspect(GitHubPipelineRunORM).columns[column_name].foreign_keys)
        assert fk.ondelete == "SET NULL"


def test_pipeline_run_revision_cascades():
    revision_fk = next(
        fk for fk in inspect(GitHubPipelineRunORM).columns["revision_id"].foreign_keys
    )
    assert revision_fk.ondelete == "CASCADE"


def test_pipeline_runs_table_has_created_at_index():
    indexes = {index.name for index in inspect(GitHubPipelineRunORM).local_table.indexes}
    assert "ix_github_pipeline_runs_created_at" in indexes
    assert "ix_github_pipeline_runs_index_job_id" in indexes
    assert "ix_github_pipeline_runs_review_run_id" in indexes


def test_finding_and_group_quality_columns():
    finding_columns = {column.name for column in inspect(GitHubFindingORM).columns}
    group_columns = {column.name for column in inspect(GitHubFindingGroupORM).columns}
    assert "evidence_snippet" in finding_columns
    assert "resolution_status" in group_columns


def test_code_chunk_and_publish_job_quality_columns():
    chunk_columns = {column.name for column in inspect(GitHubCodeChunkORM).columns}
    publish_columns = {column.name for column in inspect(GitHubPublishJobORM).columns}
    assert "content_hash" in chunk_columns
    assert "summary_json" in publish_columns


def test_pipeline_step_and_artifact_columns():
    step_columns = {column.name for column in inspect(GitHubPipelineStepORM).columns}
    artifact_columns = {column.name for column in inspect(GitHubPipelineArtifactORM).columns}
    assert {"step_type", "status", "duration_ms", "input_tokens"} <= step_columns
    assert {"kind", "content_text", "content_json", "content_hash"} <= artifact_columns
