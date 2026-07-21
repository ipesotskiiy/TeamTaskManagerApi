from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TaskActivityEvent = Literal[
    "created",
    "status_changed",
    "priority_changed",
    "assignee_changed",
    "title_changed",
    "due_date_changed",
    "comment_created",
    "comment_updated",
    "comment_deleted",
]


class TaskActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    workspace_id: int
    actor_id: int
    event_type: TaskActivityEvent
    field_name: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime
