from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TaskComment

ActionType = Literal["change", "delete"]


def get_task_comment_or_404(
    session: Session,
    task_id: int,
    comment_id: int,
) -> TaskComment:
    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task_id,
        TaskComment.id == comment_id,
    )
    task_comment = session.scalar(task_comment_stmt)

    if task_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task comment not found"
        )

    return task_comment


def ensure_comment_action_allowed_or_403(
    membership_role: str,
    task_comment_author_id: int,
    current_user_id: int,
    action: ActionType,
) -> None:
    is_change_or_delete_comment_allowed = (
            membership_role in ("admin", "owner")
            or task_comment_author_id == current_user_id
    )

    if not is_change_or_delete_comment_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You can't {action} this task comment"
        )


def ensure_can_comment_task_or_403(
    membership_role: str,
    task_created_by_id: int,
    task_assignee_id: int | None,
    current_user_id: int,
) -> None:
    is_comment_allowed = (
            membership_role in ("owner", "admin")
            or task_created_by_id == current_user_id
            or task_assignee_id == current_user_id
    )

    if not is_comment_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't comment this task",
        )