# backend/app/constants/enums.py
"""Shared enums — snake_case members and values (match PostgreSQL ENUM labels)."""
from enum import Enum


class AppRole(str, Enum):
    """Role within a workspace — stored on workspace_memberships (TENANCY.md)."""

    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class PlatformRole(str, Enum):
    """Platform staff — on users.platform_role only (not workspace-scoped)."""

    super_admin = "super_admin"


class WorkspaceStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class UserStatus(str, Enum):
    """Lifecycle — see docs/backend/USER_REGISTRATION.md."""

    pending_activation = "pending_activation"  # bootstrap super_admin only
    pending_email_verification = "pending_email_verification"
    pending_profile = "pending_profile"
    pending_approval = "pending_approval"
    active = "active"
    rejected = "rejected"
    suspended = "suspended"
    deleted = "deleted"


class ItemStatus(str, Enum):
    """Example product row status — items table (AGENT_PATTERNS.md reference)."""

    draft = "draft"
    active = "active"
    archived = "archived"


class InvitationStatus(str, Enum):
    """workspace_invitations.status — INVITATIONS.md."""

    pending = "pending"
    accepted = "accepted"
    revoked = "revoked"
    expired = "expired"


class GitHubAccountType(str, Enum):
    """github_installations.account_type — REVY_PRODUCT_SLICE.md."""

    organization = "organization"
    user = "user"


class ExportJobStatus(str, Enum):
    """data_export_jobs.status — W6 account lifecycle."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class GitHubInstallationStatus(str, Enum):
    """github_installations.status — REVY_PRODUCT_SLICE.md."""

    active = "active"
    suspended = "suspended"
    removed = "removed"


class GitHubRepositoryStatus(str, Enum):
    """github_repositories.status — R1 repository sync."""

    active = "active"
    removed = "removed"


class GitHubPullRequestState(str, Enum):
    """github_pull_requests.state — R2 PR ingestion."""

    open = "open"
    closed = "closed"


class GitHubPullRequestReviewState(str, Enum):
    """github_pull_request_reviews.state — R2 review activity."""

    approved = "approved"
    changes_requested = "changes_requested"
    commented = "commented"
    dismissed = "dismissed"
    pending = "pending"


class GitHubIndexJobStatus(str, Enum):
    """github_index_jobs.status — R3 indexing."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class GitHubIndexJobTriggerSource(str, Enum):
    """github_index_jobs.trigger_source — R8 pipeline orchestration."""

    manual = "manual"
    autostart = "autostart"
    command = "command"


class GitHubReviewRunStatus(str, Enum):
    """github_review_runs.status — R4 review run."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ReviewProfile(str, Enum):
    """Review depth tier — R4 LLM model + timeout selection."""

    standard = "standard"
    deep = "deep"
    critical = "critical"


class FindingSeverity(str, Enum):
    """github_findings.severity — R4 structured findings."""

    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class FindingCategory(str, Enum):
    """github_findings.category — R4 structured findings."""

    security = "security"
    bug = "bug"
    performance = "performance"
    style = "style"
    maintainability = "maintainability"
    other = "other"


class GitHubFindingGroupState(str, Enum):
    """github_finding_groups.state — R5 reconciliation."""

    active = "active"
    superseded = "superseded"
    resolved = "resolved"


class GitHubJudgeOutcome(str, Enum):
    """github_finding_judge_outcomes.outcome — R5 judge."""

    upheld = "upheld"
    dismissed = "dismissed"
    modified = "modified"


class GitHubReviewJudgeStatus(str, Enum):
    """github_review_runs.judge_status — polish wave judge escalation."""

    not_applicable = "not_applicable"
    completed = "completed"
    skipped_disabled = "skipped_disabled"
    skipped_unavailable = "skipped_unavailable"


class GitHubPublishJobStatus(str, Enum):
    """github_publish_jobs.status — R6 GitHub publish."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
