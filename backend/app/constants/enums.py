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
