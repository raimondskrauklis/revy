# backend/app/api/v1/github_setup.py
"""Public GitHub App Setup + Callback hops — Q12, Q13, Q20."""
from __future__ import annotations

import secrets
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PlatformException,
    ServiceUnavailableError,
    ValidationError,
)
from app.integrations.github_api import (
    GITHUB_OAUTH_AUTHORIZE_URL,
    exchange_oauth_code,
    get_app_installation,
    require_user_installation,
)
from app.services.github_install_state import (
    SETUP_STASH_COOKIE,
    mint_oauth_state,
    mint_setup_stash,
    verify_install_state,
    verify_oauth_state,
    verify_setup_stash,
)
from app.services.github_installations import bind_github_installation, verify_granted_repositories
from app.services.github_repositories import enqueue_installation_repository_sync

router = APIRouter(prefix="/github", tags=["github-setup"])


def _spa_installations_url(*, error: str | None = None) -> str:
    base = (settings.app_public_url or "").strip().rstrip("/")
    if not base:
        raise ServiceUnavailableError(
            message="APP_PUBLIC_URL is not configured",
            error_code="app_public_url_missing",
        )
    url = f"{base}/installations"
    if error:
        return f"{url}?{urlencode({'setup_error': error})}"
    return url


def _spa_redirect(*, error: str | None = None) -> RedirectResponse:
    return RedirectResponse(url=_spa_installations_url(error=error), status_code=302)


def _clear_stash(response: RedirectResponse) -> RedirectResponse:
    response.delete_cookie(SETUP_STASH_COOKIE, path="/api/v1/github")
    return response


@router.get("/setup")
async def get_github_setup(
    state: str | None = None,
    installation_id: int | None = None,
    setup_action: str | None = None,
) -> RedirectResponse:
    try:
        if not state or installation_id is None or installation_id <= 0:
            return _spa_redirect(error="invalid_state")
        install = verify_install_state(state)
        client_id = (settings.github_client_id or "").strip()
        callback = settings.github_callback_url
        if not client_id or not callback:
            return _spa_redirect(error="not_configured")
        nonce = secrets.token_urlsafe(16)
        stash = mint_setup_stash(
            workspace_id=install.workspace_id,
            user_id=install.user_id,
            installation_id=installation_id,
            setup_action=setup_action or "",
            nonce=nonce,
        )
        oauth_state = mint_oauth_state(nonce=nonce)
        location = (
            f"{GITHUB_OAUTH_AUTHORIZE_URL}?"
            f"{urlencode({'client_id': client_id, 'redirect_uri': callback, 'state': oauth_state})}"
        )
        response = RedirectResponse(url=location, status_code=302)
        setup_url = settings.github_setup_url or ""
        response.set_cookie(
            key=SETUP_STASH_COOKIE,
            value=stash,
            httponly=True,
            samesite="lax",
            path="/api/v1/github",
            max_age=settings.github_install_state_ttl_seconds,
            secure=setup_url.startswith("https://"),
        )
        return response
    except (ValidationError, ServiceUnavailableError):
        return _spa_redirect(error="invalid_state")


@router.get("/callback")
async def get_github_callback(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return _clear_stash(_spa_redirect(error="oauth_denied"))
    stash_raw = request.cookies.get(SETUP_STASH_COOKIE)
    try:
        if not code or not state or not stash_raw:
            return _clear_stash(_spa_redirect(error="invalid_state"))
        oauth = verify_oauth_state(state)
        stash = verify_setup_stash(stash_raw)
        if oauth.nonce != stash.nonce:
            return _clear_stash(_spa_redirect(error="invalid_state"))
        callback = settings.github_callback_url
        if not callback:
            return _clear_stash(_spa_redirect(error="not_configured"))
        async with httpx.AsyncClient(timeout=30.0) as client:
            user_token = await exchange_oauth_code(client, code=code, redirect_uri=callback)
            try:
                await require_user_installation(
                    client,
                    user_access_token=user_token,
                    github_installation_id=stash.installation_id,
                )
                account = await get_app_installation(
                    client,
                    github_installation_id=stash.installation_id,
                )
            finally:
                del user_token
            row = await bind_github_installation(
                session,
                workspace_id=stash.workspace_id,
                github_installation_id=account.github_installation_id,
                account_login=account.account_login,
                account_type=account.account_type,
                account_id=account.account_id,
            )
            await session.commit()
            enqueue_installation_repository_sync(row.id)
            try:
                await verify_granted_repositories(session, installation=row, client=client)
                await session.commit()
            except (httpx.HTTPError, ServiceUnavailableError):
                pass
        return _clear_stash(_spa_redirect())
    except ForbiddenError as exc:
        code_name = exc.error_code or "forbidden"
        return _clear_stash(_spa_redirect(error=code_name))
    except ConflictError:
        return _clear_stash(_spa_redirect(error="conflict"))
    except NotFoundError:
        return _clear_stash(_spa_redirect(error="not_found"))
    except httpx.HTTPError:
        return _clear_stash(_spa_redirect(error="github_unavailable"))
    except (ValidationError, ServiceUnavailableError, PlatformException):
        return _clear_stash(_spa_redirect(error="invalid_state"))
