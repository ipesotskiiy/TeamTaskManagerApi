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
    task_comment = session.execute(task_comment_stmt).scalars().one_or_none()

    if task_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task comment not found"
        )

    return task_comment


def is_can_change_or_delete_or_403(
    membership_role: str,
    task_comment_author_id: int,
    current_user_id: int,
    action: ActionType,
):
    is_can_change_or_delete_task_comment = (
            membership_role in ("admin", "owner")
            or task_comment_author_id == current_user_id
    )

    if not is_can_change_or_delete_task_comment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You can't {action} this task comment"
        )


def is_can_comment_or_403(
    membership_role: str,
    task_created_by_id: int,
    task_assignee_id: int | None,
    current_user_id: int,
):
    is_can_comment = (
            membership_role in ("owner", "admin")
            or task_created_by_id == current_user_id
            or task_assignee_id == current_user_id
    )

    if not is_can_comment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't comment this task",
        )