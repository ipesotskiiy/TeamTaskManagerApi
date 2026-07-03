from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import (
    Task,
    User,
    Workspace,
    WorkspaceMember,
)
from app.schemas.task import (
    TaskCreate,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)

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


@router.patch(
    "/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    workspace_id: int,
    task_id: int,
    task_data: TaskUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_stmt = select(
        Workspace,
        WorkspaceMember,
    ).join(
        WorkspaceMember,
        Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )

    result = session.execute(workspace_stmt).one_or_none()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    workspace, membership = result

    task_stmt = select(
        Task,
    ).where(
        Task.workspace_id == workspace.id,
        Task.id == task_id,
    )
    task = session.execute(task_stmt).scalars().one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task_data_dict = task_data.model_dump(exclude_unset=True)
    if not task_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Change request shouldn't be empty",
        )

    if "title" in task_data_dict and task_data_dict["title"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title should not be None",
        )

    if "status" in task_data_dict and task_data_dict["status"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status should not be None",
        )

    if "priority" in task_data_dict and task_data_dict["priority"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority should not be None",
        )

    is_owner_or_admin = membership.role in ("admin", "owner")

    if not is_owner_or_admin:
        allowed_fields = set()
        if task.created_by_id == current_user.id:
            allowed_fields.update(
                ("title", "description", "priority", "due_date"),
            )
        if task.assignee_id == current_user.id:
            allowed_fields.add("status")

        if not allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change this task",
            )

        requested_fields = set(task_data_dict)
        if not requested_fields.issubset(allowed_fields):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are trying to change fields that are not allowed for you",
            )

    new_assignee_id = task_data_dict.get("assignee_id")

    if "assignee_id" in task_data_dict and new_assignee_id is not None:
        assignee_stmt = select(
            WorkspaceMember,
        ).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == new_assignee_id,
        )

        assignee_membership = session.execute(
            assignee_stmt,
        ).scalars().one_or_none()

        if assignee_membership is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is not in this workspace",
            )

    for key, value in task_data_dict.items():
        setattr(task, key, value)

    session.commit()
    session.refresh(task)

    return task


@router.delete(
    "/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_stmt = select(
        Workspace,
        WorkspaceMember,
    ).join(
        WorkspaceMember,
        Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        Workspace.id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )

    result = session.execute(workspace_stmt).one_or_none()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    workspace, membership = result

    task_stmt = select(
        Task,
    ).where(
        Task.workspace_id == workspace.id,
        Task.id == task_id,
    )

    task = session.execute(task_stmt).scalars().one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    is_owner_or_admin = membership.role in ("admin", "owner")
    is_creator = task.created_by_id == current_user.id

    if not (is_owner_or_admin or is_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete this task",
        )

    session.delete(task)
    session.commit()
