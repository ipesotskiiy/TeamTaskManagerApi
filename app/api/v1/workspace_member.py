from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.dependencies.workspace_member import get_workspace_member_or_404
from app.api.v1.dependencies.workspaces import get_workspace_for_member_or_404
from app.db.session import get_db
from app.models import User, WorkspaceMember
from app.schemas.workspace_member import WorkspaceMemberRead, WorkspaceMemberRole

router = APIRouter(prefix="/members", tags=["workspace-members"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[WorkspaceMemberRead],
)
async def get_workspace_members(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member_role: WorkspaceMemberRole | None = Query(
        default=None,
        alias="role",
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    workspace_user_stmt = (
        select(
            WorkspaceMember,
            User,
        )
        .join(
            User,
            User.id == WorkspaceMember.user_id,
        )
        .where(
            WorkspaceMember.workspace_id == workspace_id,
        )
    )

    if member_role is not None:
        workspace_user_stmt = workspace_user_stmt.where(
            WorkspaceMember.role == member_role,
        )

    workspace_user_stmt = (
        workspace_user_stmt
        .order_by(WorkspaceMember.id)
        .offset(offset)
        .limit(limit)
    )

    rows = session.execute(workspace_user_stmt).all()

    result = []

    for membership, user in rows:
        result.append(
            WorkspaceMemberRead(
                id=membership.id,
                workspace_id=membership.workspace_id,
                user_id=membership.user_id,
                username=user.username,
                email=user.email,
                role=membership.role,
                created_at=membership.created_at,
            )
        )

    return result


@router.get(
    "/{membership_id}/",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceMemberRead,
)
async def get_workspace_member(
    workspace_id: int,
    membership_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    membership, user = get_workspace_member_or_404(
        session,
        workspace_id,
        membership_id,
    )

    return WorkspaceMemberRead(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        username=user.username,
        email=user.email,
        role=membership.role,
        created_at=membership.created_at,
    )


