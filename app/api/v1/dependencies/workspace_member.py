from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import WorkspaceMember, User


def get_workspace_member_or_404(
    session: Session,
    workspace_id: int,
    membership_id: int,
) -> tuple[WorkspaceMember, User]:
    workspace_member_user_stmt = (
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
            WorkspaceMember.id == membership_id,
        )
    )

    result = session.execute(workspace_member_user_stmt).one_or_none()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace member not found",
        )

    workspace_member, user = result
    return workspace_member, user
