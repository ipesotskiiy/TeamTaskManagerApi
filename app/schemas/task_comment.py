from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


TaskCommentText = Annotated[
    str,
    Field(min_length=1, max_length=1000),
]


class TaskCommentCreate(BaseModel):
    text: TaskCommentText


class TaskCommentUpdate(BaseModel):
    text: TaskCommentText


class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    workspace_id: int
    author_id: int
    text: str
    created_at: datetime
    updated_at: datetime
