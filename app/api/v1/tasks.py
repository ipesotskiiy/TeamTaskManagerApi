from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.task_activity import TASK_UPDATE_EVENT_BY_FIELD
from app.api.deps import get_current_user

from app.api.v1.dependencies.tasks import (
    ensure_can_update_task,
    ensure_can_delete_task,
    get_task_or_404,
    get_valid_task_update_data,
    validate_assignee_or_400,
)
from app.api.v1.dependencies.workspaces import (
    get_workspace_and_membership_or_404,
    get_workspace_for_member_or_404,
)
from app.db.session import get_db
from app.models import (
    Task,
    User,
)
from app.schemas.task import (
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)
from app.services.task_activity import create_task_update_activity

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    workspace_id: int,
    task_data: TaskCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    assignee_user_id = task_data.assignee_id
    if assignee_user_id is not None:
        validate_assignee_or_400(
            session,
            workspace_id,
            assignee_user_id,
        )

    task = Task(
        **task_data.model_dump(exclude_unset=True),
        workspace_id=workspace_id,
        created_by_id=current_user.id,
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return task


@router.get(
    "/",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK,
)
def get_tasks(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task_status: TaskStatus | None = Query(None, alias="status"),
    task_priority: TaskPriority | None = Query(None, alias="priority"),
    task_assignee_id: int | None = Query(None, ge=1, alias="assignee_id"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    tasks_stmt = select(
        Task,
    ).where(
        Task.workspace_id == workspace_id,
    )

    if task_status is not None:
        tasks_stmt = tasks_stmt.where(Task.status == task_status)

    if task_priority is not None:
        tasks_stmt = tasks_stmt.where(Task.priority == task_priority)

    if task_assignee_id is not None:
        tasks_stmt = tasks_stmt.where(Task.assignee_id == task_assignee_id)

    paginated_tasks = tasks_stmt.order_by(Task.id).offset(offset).limit(limit)
    tasks = session.scalars(paginated_tasks).all()

    return tasks


@router.get(
    "/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
)
def get_task(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    task = get_task_or_404(
        session,
        workspace_id,
        task_id,
    )

    return task


@router.patch(
    "/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
)
def update_task(
    workspace_id: int,
    task_id: int,
    task_data: TaskUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    task = get_task_or_404(
        session,
        workspace_id,
        task_id,
    )

    task_data_dict = get_valid_task_update_data(task_data)

    ensure_can_update_task(
        membership,
        task,
        current_user.id,
        task_data_dict,
    )

    new_assignee_id = task_data_dict.get("assignee_id")

    if "assignee_id" in task_data_dict and new_assignee_id is not None:
        validate_assignee_or_400(
            session,
            workspace_id,
            new_assignee_id,
        )

    for field_name, field_value in task_data_dict.items():
        if field_name in TASK_UPDATE_EVENT_BY_FIELD:
            create_task_update_activity(
                session,
                field_name,
                field_value,
                current_user.id,
                workspace_id,
                task,
            )
        setattr(task, field_name, field_value)

    session.commit()
    session.refresh(task)

    return task


@router.delete(
    "/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    task = get_task_or_404(
        session,
        workspace_id,
        task_id,
    )

    ensure_can_delete_task(membership, task, current_user.id)

    session.delete(task)
    session.commit()
