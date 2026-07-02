from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Task, User, Workspace, WorkspaceMember
from app.schemas.task import TaskCreate, TaskPriority, TaskRead, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    workspace_id: int,
    task_data: TaskCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_stmt = select(
        Workspace
    ).join(
        WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )

    workspace = session.execute(workspace_stmt).scalars().one_or_none()

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    assignee_user_id = task_data.assignee_id
    if assignee_user_id is not None:
        assignee_stmt = select(
            WorkspaceMember,
        ).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == assignee_user_id,
        )
        assignee_membership = session.execute(assignee_stmt).scalars().one_or_none()
        if assignee_membership is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is not in this workspace",
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
async def get_tasks(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task_status: TaskStatus | None = Query(None, alias="status"),
    task_priority: TaskPriority | None = Query(None, alias="priority"),
    task_assignee_id: int | None = Query(None, ge=1, alias="assignee_id"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    workspace_stmt = select(
        Workspace,
    ).join(
        WorkspaceMember,
        Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )

    workspace = session.execute(workspace_stmt).scalars().one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
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
    tasks = session.execute(paginated_tasks).scalars().all()

    return tasks


@router.get(
    "/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
)
async def get_task(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_stmt = select(
        Workspace,
    ).join(
        WorkspaceMember,
        WorkspaceMember.workspace_id == Workspace.id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )

    workspace = session.execute(workspace_stmt).scalars().one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    task_stmt = select(
        Task,
    ).where(
        Task.workspace_id == workspace_id,
        Task.id == task_id,
    )
    task = session.execute(task_stmt).scalars().one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task
