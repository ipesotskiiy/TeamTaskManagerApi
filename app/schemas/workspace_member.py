from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkspaceMemberRole = Literal[
    "owner",
    "admin",
    "member",
]

WorkspaceMemberEditableRole = Literal[
    "admin",
    "member",
]


class WorkspaceMemberCreate(BaseModel):
    user_id: int = Field(ge=1)
    role: WorkspaceMemberEditableRole = "member"


class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceMemberEditableRole


class WorkspaceMemberRead(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    username: str
    email: str
    role: WorkspaceMemberRole
    created_at: datetime
