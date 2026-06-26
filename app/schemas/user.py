from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
