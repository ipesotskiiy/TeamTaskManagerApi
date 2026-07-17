from fastapi import (
    APIRouter,
    Depends,
    status,
    Query,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.dependencies.tasks import get_task_or_404
from app.api.v1.dependencies.workspaces import get_workspace_for_member_or_404
from app.db.session import get_db
from app.models import User, TaskActivity
from app.schemas.task_activity import TaskActivityRead

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskActivityRead],
)
async def get_task_activities(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    workspace = get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    task = get_task_or_404(
        session,
        workspace.id,
        task_id
    )

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == workspace.id,
        TaskActivity.task_id == task.id,
    )

    paginated_task_activities = task_activity_stmt.order_by(TaskActivity.id).offset(offset).limit(limit)
    task_activities = session.execute(paginated_task_activities).scalars().all()

    return task_activities
