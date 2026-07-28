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


def get_membership_with_workspace_and_user_ids(
    session: Session,
    workspace_id: int,
    user_id: int,
) -> WorkspaceMember | None:
    check_add_user_membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    )

    check_add_user_membership = session.scalar(check_add_user_membership_stmt)

    return check_add_user_membership


def get_user_or_404(
    session: Session,
    user_id: int,
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def ensure_role(
    membership_role: str,
    workspace_member_data_role: str,
) -> None:
    if membership_role == "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot add workspace members",
        )
    if workspace_member_data_role == "admin" and membership_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can add workspace admin"
        )
