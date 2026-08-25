from datetime import date, datetime
from enum import Enum

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.constants.task_activity import (
    TASK_UPDATE_EVENT_BY_FIELD,
    COMMENT_CREATED_EVENT,
    COMMENT_UPDATED_EVENT,
    COMMENT_DELETED_EVENT,
)
from app.models import Task, TaskActivity


def create_task_update_activity(
    session: Session,
    key: str,
    value: str | int | date | datetime | Enum | None,
    current_user_id: int,
    workspace_id: int,
    task: Task,
) -> None:
    event_type = TASK_UPDATE_EVENT_BY_FIELD[key]
    old_value = inspect(task).attrs[key].value

    prepared_old_value = prepare_activity_value(old_value)
    prepared_new_value = prepare_activity_value(value)

    if prepared_old_value == prepared_new_value:
        return

    task_activity = TaskActivity(
        task_id=task.id,
        workspace_id=workspace_id,
        actor_id=current_user_id,
        event_type=event_type,
        field_name=key,
        old_value=prepared_old_value,
        new_value=prepared_new_value,
    )
    session.add(task_activity)


def prepare_activity_value(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, Enum):
        return str(value.value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return str(value)


def create_task_comment_activity(
    session: Session,
    task_comment: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
) -> None:
    task_activity = TaskActivity(
        task_id=task_id,
        workspace_id=workspace_id,
        actor_id=current_user_id,
        event_type=COMMENT_CREATED_EVENT,
        field_name="comment",
        old_value=None,
        new_value=task_comment,
    )
    session.add(task_activity)


def create_comment_updated_activity(
    session: Session,
    old_task_comment_text: str,
    new_task_comment_text: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
) -> None:
    if old_task_comment_text != new_task_comment_text:
        task_activity = TaskActivity(
            task_id=task_id,
            workspace_id=workspace_id,
            actor_id=current_user_id,
            event_type=COMMENT_UPDATED_EVENT,
            field_name="text",
            old_value=old_task_comment_text,
            new_value=new_task_comment_text,
        )
        session.add(task_activity)


def create_comment_deleted_activity(
    session: Session,
    old_task_comment_text: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
) -> None:
    task_activity = TaskActivity(
        task_id=task_id,
        workspace_id=workspace_id,
        actor_id=current_user_id,
        event_type=COMMENT_DELETED_EVENT,
        field_name="comment",
        old_value=old_task_comment_text,
        new_value=None,
    )
    session.add(task_activity)