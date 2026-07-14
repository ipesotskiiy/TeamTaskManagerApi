from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    ForeignKey,
    Enum,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User
    from app.models.workspace import Workspace


class TaskActivity(Base):
    __tablename__ = "task_activities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tasks.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    actor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
        ),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        Enum(
            "created",
            "status_changed",
            "priority_changed",
            "assignee_changed",
            "title_changed",
            "due_date_changed",
            "comment_created",
            "comment_updated",
            "comment_deleted",
            name="task_event",
        ),
        nullable=False,
    )
    field_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    old_value: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    new_value: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="activities",
    )
    actor: Mapped["User"] = relationship(
        "User",
        back_populates="task_activities",
    )
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="task_activities",
    )

