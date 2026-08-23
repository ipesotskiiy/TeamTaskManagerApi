from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import WorkspaceMember, User
from app.schemas.workspace_member import WorkspaceMemberRead


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


def get_workspace_membership(
    session: Session,
    workspace_id: int,
    user_id: int,
) -> WorkspaceMember | None:
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    )

    membership = session.scalar(membership_stmt)

    return membership


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


def ensure_can_add_workspace_member_with_role_or_403(
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

def check_is_owner(
    membership_role: str
) -> None:
    if membership_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can change workspace member roles",
        )

def check_changing_role_is_not_owner(
    changing_membership_role: str,
) -> None:

    if changing_membership_role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace owner role cannot be changed",
        )

def ensure_can_delete_workspace_member_or_403(
    current_user_role: str,
    deleting_membership_role: str,
) -> None:
    if current_user_role == "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member cannot remove anyone from workspace"
        )

    if current_user_role == "admin" and deleting_membership_role != "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin can remove only member"
        )

    if deleting_membership_role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace owner cannot be removed",
        )


def create_workspace_member_read(
    membership: WorkspaceMember,
    user: User,
) -> WorkspaceMemberRead:
    return WorkspaceMemberRead(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        username=user.username,
        email=user.email,
        role=membership.role,
        created_at=membership.created_at,
    )
