# backend/app/core/auth.py
"""Keycloak JWT validation + CurrentUser — AUTH.md, AUTHZ_MODEL.md, TENANCY.md."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWKSetError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, ServiceUnavailableError, UnauthorizedError
from app.core.jwks import JwkSigningKeyNotFoundError, jwks_client, signing_key_from_jwt
from app.core.logging import get_logger
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.impersonation import get_active_session
from app.services.keycloak_provisioning import provision_user_from_keycloak

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)

ACTIVE_WORKSPACE_HEADER = "X-Workspace-Id"


@dataclass
class CurrentUser:
    sub: str
    actor_user_id: UUID | None = None
    impersonated_user_id: UUID | None = None
    email: str | None = None
    platform_role: PlatformRole | None = None
    workspace_id: UUID | None = None
    role: AppRole | None = None
    status: UserStatus | None = None
    roles: frozenset[str] = frozenset()

    @property
    def user_id(self) -> UUID | None:
        return self.effective_user_id

    @property
    def effective_user_id(self) -> UUID | None:
        return self.impersonated_user_id or self.actor_user_id

    @property
    def impersonator_user_id(self) -> UUID | None:
        if self.impersonated_user_id is None:
            return None
        return self.actor_user_id

    @property
    def is_impersonating(self) -> bool:
        return self.impersonated_user_id is not None

    @property
    def is_super_admin(self) -> bool:
        return self.platform_role == PlatformRole.super_admin


def token_client_allowlist() -> frozenset[str]:
    """OIDC clients allowed in JWT ``aud`` / ``azp`` — API + SPA (keycloak.md)."""
    clients = {settings.keycloak_client_id}
    frontend = settings.keycloak_frontend_client_id.strip()
    if frontend:
        clients.add(frontend)
    return frozenset(clients)


def _decode_token_payload(token: str, jwks: dict) -> dict:
    """Verify JWT signature, issuer, expiry; then validate audience allowlist."""
    signing_key = signing_key_from_jwt(jwks, token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=jwks_client.issuer,
        options={"verify_aud": False},
    )
    _validate_audience(payload)
    return payload


def _validate_audience(payload: dict) -> None:
    allowed = token_client_allowlist()
    azp = payload.get("azp")
    if azp is not None and str(azp) not in allowed:
        raise UnauthorizedError("Invalid authorized party")

    aud = payload.get("aud")
    if aud is None:
        return

    if isinstance(aud, str):
        if aud not in allowed:
            raise UnauthorizedError("Invalid token audience")
        return
    if isinstance(aud, list) and not allowed.intersection({str(a) for a in aud}):
        raise UnauthorizedError("Invalid token audience")


async def decode_access_token(token: str) -> dict:
    """Validate JWT signature, issuer, expiry, and audience."""
    jwks = await jwks_client.get_jwks()
    try:
        return _decode_token_payload(token, jwks)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except JwkSigningKeyNotFoundError:
        jwks = await jwks_client.get_jwks(force_refresh=True)
        try:
            return _decode_token_payload(token, jwks)
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("Token expired") from exc
        except PyJWKSetError as exc:
            raise ServiceUnavailableError(
                message="Authentication service unavailable",
                details={"reason": str(exc)},
            ) from exc
        except (JwkSigningKeyNotFoundError, jwt.InvalidTokenError) as retry_exc:
            raise UnauthorizedError("Invalid token") from retry_exc
    except PyJWKSetError as exc:
        raise ServiceUnavailableError(
            message="Authentication service unavailable",
            details={"reason": str(exc)},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc


async def _resolve_active_workspace(
    session: AsyncSession,
    user: UserORM,
    *,
    header_workspace_id: str | None,
) -> tuple[UUID | None, AppRole | None]:
    if user.is_super_admin:
        return None, None

    memberships = (
        await session.scalars(
            select(WorkspaceMembershipORM).where(WorkspaceMembershipORM.user_id == user.id)
        )
    ).all()
    if not memberships:
        return None, None

    if header_workspace_id:
        try:
            requested = UUID(header_workspace_id)
        except ValueError as exc:
            raise ForbiddenError(
                message="Invalid workspace id",
                error_code="validation_error",
            ) from exc
        match = next((m for m in memberships if m.workspace_id == requested), None)
        if match is None:
            raise ForbiddenError(message="Workspace access denied")
        workspace = await session.get(WorkspaceORM, match.workspace_id)
        if workspace is not None and workspace.status == WorkspaceStatus.suspended:
            raise ForbiddenError(
                message="Workspace suspended",
                error_code="workspace_suspended",
            )
        return match.workspace_id, match.role

    if len(memberships) == 1:
        only = memberships[0]
        return only.workspace_id, only.role

    return None, None


def _assert_effective_user_active(status: UserStatus) -> None:
    if status == UserStatus.suspended:
        raise ForbiddenError(message="Account suspended")
    if status == UserStatus.rejected:
        raise ForbiddenError(message="Account rejected")
    if status == UserStatus.deleted:
        raise ForbiddenError(message="Account deleted", error_code="account_deleted")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
    x_workspace_id: Annotated[str | None, Header(alias=ACTIVE_WORKSPACE_HEADER)] = None,
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")

    payload = await decode_access_token(credentials.credentials)
    sub = str(payload.get("sub") or "")
    email = payload.get("email")
    if not sub:
        raise UnauthorizedError("Invalid token: missing sub")

    given_name = payload.get("given_name")
    family_name = payload.get("family_name")
    display_name = " ".join(part for part in (given_name, family_name) if part) or None
    actor = await provision_user_from_keycloak(
        session,
        sub=sub,
        email=str(email) if email else None,
        email_verified=bool(payload.get("email_verified")),
        display_name=str(display_name) if display_name else None,
    )
    await session.commit()
    await session.refresh(actor)

    if actor.status == UserStatus.suspended:
        raise ForbiddenError(message="Account suspended", error_code="account_suspended")
    if actor.status == UserStatus.rejected:
        raise ForbiddenError(message="Account rejected")
    if actor.status == UserStatus.deleted:
        raise ForbiddenError(message="Account deleted", error_code="account_deleted")

    impersonated_user_id: UUID | None = None
    active_session = await get_active_session(session, actor_user_id=actor.id)
    if active_session is not None:
        impersonated_user_id = active_session.target_user_id

    effective = actor
    if impersonated_user_id is not None:
        target = await session.get(UserORM, impersonated_user_id)
        if target is None:
            raise ForbiddenError(
                message="Impersonation target not found",
                error_code="impersonation_invalid",
            )
        effective = target
        _assert_effective_user_active(effective.status)

    workspace_id, role = await _resolve_active_workspace(
        session,
        effective,
        header_workspace_id=x_workspace_id,
    )

    return CurrentUser(
        sub=sub,
        actor_user_id=actor.id,
        impersonated_user_id=impersonated_user_id,
        email=effective.email,
        platform_role=actor.platform_role,
        workspace_id=workspace_id,
        role=role,
        status=effective.status,
    )


def require_super_admin():
    async def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.is_super_admin:
            raise ForbiddenError("Platform administrator required")
        return user

    return _guard


def require_impersonation_allowed():
    async def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.is_impersonating:
            raise ForbiddenError(
                message="Action not allowed while impersonating",
                error_code="impersonation_restricted",
            )
        return user

    return _guard
