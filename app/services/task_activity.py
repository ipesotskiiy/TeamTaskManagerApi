from datetime import date, datetime
from enum import Enum

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.constants.task_activity import (
    KEY_FOR_LOG_ACTIVITIES,
    LOG_ACTIVITIES_CREATE_COMMENT,
    LOG_ACTIVITIES_UPDATE_COMMENT, LOG_ACTIVITIES_DELETE_COMMENT,
)
from app.models import Task, TaskActivity


async def create_task_activities(
    session: Session,
    key: str,
    value: str | int | date | datetime | Enum | None,
    current_user_id: int,
    workspace_id: int,
    task: Task,
):
    task_id = task.id
    event_type = KEY_FOR_LOG_ACTIVITIES[key]

    task_data = {c.key: getattr(task, c.key) for c in inspect(task).mapper.column_attrs}
    old_value = task_data[key]
    prepared_old_value = await prepare_activity_value(old_value)
    prepared_new_value = await prepare_activity_value(value)
    if prepared_old_value != prepared_new_value:
        task_activity = TaskActivity(
            task_id=task_id,
            workspace_id=workspace_id,
            actor_id=current_user_id,
            event_type=event_type,
            field_name=key,
            old_value=prepared_old_value,
            new_value=prepared_new_value,
        )
        session.add(task_activity)

async def prepare_activity_value(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, Enum):
        return str(value.value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return str(value)


async def create_task_comment_activity(
    session: Session,
    task_comment: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
):
    task_activity = TaskActivity(
        task_id=task_id,
        workspace_id=workspace_id,
        actor_id=current_user_id,
        event_type=LOG_ACTIVITIES_CREATE_COMMENT,
        field_name="comment",
        old_value=None,
        new_value=task_comment,
    )
    session.add(task_activity)


async def create_comment_updated_activity(
    session: Session,
    old_task_comment_text: str,
    new_task_comment_text: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
):
    if old_task_comment_text != new_task_comment_text:
        task_activity = TaskActivity(
            task_id=task_id,
            workspace_id=workspace_id,
            actor_id=current_user_id,
            event_type=LOG_ACTIVITIES_UPDATE_COMMENT,
            field_name="text",
            old_value=old_task_comment_text,
            new_value=new_task_comment_text,
        )
        session.add(task_activity)


async def create_comment_deleted_activity(
    session: Session,
    old_task_comment_text: str,
    workspace_id: int,
    task_id: int,
    current_user_id: int,
):
    task_activity = TaskActivity(
        task_id=task_id,
        workspace_id=workspace_id,
        actor_id=current_user_id,
        event_type=LOG_ACTIVITIES_DELETE_COMMENT,
        field_name="comment",
        old_value=old_task_comment_text,
        new_value=None,
    )
    session.add(task_activity)