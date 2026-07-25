# backend/app/api/v1/me.py
"""Current user profile — docs/backend/ME_ENDPOINT.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.schemas.common import SuccessResponse
from app.schemas.lifecycle import (
    DeleteAccountRequest,
    ExportJobCreateResponse,
    ExportJobStatusResponse,
)
from app.schemas.me import MeResponse, MeUpdate, SetActiveWorkspaceRequest
from app.services.account_lifecycle import delete_account
from app.services.data_export import (
    create_export_job,
    get_export_job_for_user,
    resolve_download_path,
)
from app.services.users import build_me_response, set_active_workspace, update_me
from app.workers.export_tasks import run_data_export_job

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=SuccessResponse[MeResponse])
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    me = await build_me_response(session, current_user.user_id)
    if current_user.workspace_id is not None:
        me = me.model_copy(
            update={
                "workspace_id": current_user.workspace_id,
                "role": current_user.role,
            }
        )
    return SuccessResponse(data=me)


@router.patch("", response_model=SuccessResponse[MeResponse])
async def patch_me(
    body: MeUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await update_me(session, user_id=current_user.user_id, payload=body)
    await session.commit()

    me = await build_me_response(session, current_user.user_id)
    if current_user.workspace_id is not None:
        me = me.model_copy(
            update={
                "workspace_id": current_user.workspace_id,
                "role": current_user.role,
            }
        )
    return SuccessResponse(data=me)


@router.patch("/workspace", response_model=SuccessResponse[MeResponse])
async def patch_active_workspace(
    body: SetActiveWorkspaceRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    me = await set_active_workspace(
        session,
        user_id=current_user.user_id,
        workspace_id=body.workspace_id,
    )
    await session.commit()
    return SuccessResponse(data=me)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    body: DeleteAccountRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await delete_account(
        session,
        user_id=current_user.user_id,
        confirm_email=body.confirm_email,
    )
    await session.commit()


@router.post("/export", response_model=SuccessResponse[ExportJobCreateResponse])
async def post_export_job(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ExportJobCreateResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    job = await create_export_job(session, user_id=current_user.user_id)
    await session.commit()
    run_data_export_job.delay(str(job.id))
    return SuccessResponse(data=ExportJobCreateResponse(job_id=job.id))


@router.get("/export/{job_id}", response_model=SuccessResponse[ExportJobStatusResponse])
async def get_export_job_status(
    job_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ExportJobStatusResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    job = await get_export_job_for_user(
        session,
        job_id=job_id,
        user_id=current_user.user_id,
    )
    return SuccessResponse(data=ExportJobStatusResponse.model_validate(job))


@router.get("/export/{job_id}/download")
async def download_export_job(
    job_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    job = await get_export_job_for_user(
        session,
        job_id=job_id,
        user_id=current_user.user_id,
    )
    path = resolve_download_path(job)
    return FileResponse(
        path=path,
        media_type="application/zip",
        filename=f"revy-export-{job_id}.zip",
    )
