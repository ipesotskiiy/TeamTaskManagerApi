from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies.workspace_member import get_workspace_membership
from app.models import Task, WorkspaceMember
from app.schemas.task import TaskUpdate


def get_task_or_404(
    session: Session,
    workspace_id: int,
    task_id: int,
) -> Task:
    task_stmt = select(
        Task,
    ).where(
        Task.workspace_id == workspace_id,
        Task.id == task_id,
    )
    task = session.scalar(task_stmt)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


def validate_assignee_or_400(
    session: Session,
    workspace_id: int,
    assignee_user_id: int,
) -> None:
    assignee_membership = get_workspace_membership(
        session,
        workspace_id,
        assignee_user_id,
    )

    if assignee_membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is not in this workspace",
        )


def get_valid_task_update_data(task_data: TaskUpdate) -> dict[str, object]:
    task_data_dict = task_data.model_dump(exclude_unset=True)
    if not task_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Change request shouldn't be empty",
        )

    if "title" in task_data_dict and task_data_dict["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title should not be None",
        )

    if "status" in task_data_dict and task_data_dict["status"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status should not be None",
        )

    if "priority" in task_data_dict and task_data_dict["priority"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority should not be None",
        )

    return task_data_dict


def ensure_can_update_task(
    membership: WorkspaceMember,
    task: Task,
    current_user_id: int,
    task_data_dict: dict[str, object],
) -> None:
    if membership.role in ("admin", "owner"):
        return

    allowed_fields: set[str] = set()

    if task.created_by_id == current_user_id:
        allowed_fields.update(
            ("title", "description", "priority", "due_date"),
        )

    if task.assignee_id == current_user_id:
        allowed_fields.add("status")

    if not allowed_fields:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change this task",
        )

    requested_fields = set(task_data_dict)

    if not requested_fields.issubset(allowed_fields):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You are trying to change fields "
                "that are not allowed for you"
            ),
        )


def ensure_can_delete_task(
    membership: WorkspaceMember,
    task: Task,
    current_user_id: int,
) -> None:
    is_owner_or_admin = membership.role in ("admin", "owner")
    is_creator = task.created_by_id == current_user_id

    if not (is_owner_or_admin or is_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete this task",
        )
