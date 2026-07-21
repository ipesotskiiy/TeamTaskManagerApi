from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    CheckConstraint,
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


class TaskComment(Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(
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
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="comments",
    )
    author: Mapped["User"] = relationship(
        "User",
        back_populates="task_comments",
    )
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="task_comments",
    )

    __table_args__ = (
        CheckConstraint("length(text) >= 1", name="ck_task_comments_text_min_length"),
    )
