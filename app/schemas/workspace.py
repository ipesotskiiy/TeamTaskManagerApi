from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=5, max_length=200)
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=5, max_length=200)
    description: str | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

