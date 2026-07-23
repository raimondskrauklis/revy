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


class UserStatus(str, Enum):
    """Lifecycle — see docs/backend/USER_REGISTRATION.md."""

    pending_activation = "pending_activation"  # bootstrap super_admin only
    pending_email_verification = "pending_email_verification"
    pending_profile = "pending_profile"
    pending_approval = "pending_approval"
    active = "active"
    rejected = "rejected"
    suspended = "suspended"


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
