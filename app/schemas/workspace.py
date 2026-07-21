from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


WorkspaceName = Annotated[
    str,
    Field(min_length=5, max_length=200),
]


class WorkspaceCreate(BaseModel):
    name: WorkspaceName
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: WorkspaceName | None = None
    description: str | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

