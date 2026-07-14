from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)


class TaskCommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class TaskCommentUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    workspace_id: int
    author_id: int
    text: str
    created_at: datetime
    updated_at: datetime
