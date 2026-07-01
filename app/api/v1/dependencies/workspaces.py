from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Workspace, WorkspaceMember
from app.schemas.workspace import WorkspaceUpdate


def get_workspace_for_member_or_404(
    session: Session,
    workspace_id: int,
    user_id: int,
) -> Workspace:
    workspace_stmt = select(
        Workspace
    ).join(
        WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )

    workspace = session.execute(workspace_stmt).scalars().one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


def get_workspace_and_membership_or_404(
    session: Session,
    workspace_id: int,
    user_id: int,
) -> tuple[Workspace, WorkspaceMember]:
    workspace_stmt = select(
        Workspace, WorkspaceMember
    ).join(
        WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    result = session.execute(workspace_stmt).one_or_none()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    workspace, membership = result

    return workspace, membership


def check_workspace_role(
    membership: WorkspaceMember,
    allowed_roles: tuple[str, ...],
    detail: str,
) -> None:
    if membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def get_workspace_update_data(workspace_data: WorkspaceUpdate) -> dict[str, object]:
    update_data = workspace_data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name should not be None",
        )

    return update_data
