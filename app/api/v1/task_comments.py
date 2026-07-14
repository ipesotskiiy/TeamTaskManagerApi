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
    User,
    Workspace,
    WorkspaceMember,
    Task,
    TaskComment,
)
from app.schemas.task_comment import TaskCommentRead, TaskCommentCreate, TaskCommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskCommentRead,
)
async def create_task_comment(
    workspace_id: int,
    task_id: int,
    task_comment_data: TaskCommentCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace_stmt = select(
        Workspace,
        WorkspaceMember,
    ).join(
        WorkspaceMember,
        WorkspaceMember.workspace_id == Workspace.id,
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
        Task
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

    is_can_comment = (
        membership.role in ("owner", "admin")
        or task.created_by_id == current_user.id
        or task.assignee_id == current_user.id
    )

    if not is_can_comment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't comment this task",
        )

    task_comment = TaskComment(
        **task_comment_data.model_dump(exclude_unset=True),
        task_id=task_id,
        workspace_id=workspace_id,
        author_id=current_user.id
    )

    session.add(task_comment)
    session.commit()
    session.refresh(task_comment)

    return task_comment


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[TaskCommentRead],
)
async def get_list_task_comments(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    author_id: int | None = Query(None, ge=1, alias="comment_author"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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
        Task
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

    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task.id,
    )

    if author_id is not None:
        task_comment_stmt = task_comment_stmt.where(TaskComment.author_id == author_id)


    paginated_tasks_comment = task_comment_stmt.order_by(TaskComment.id).offset(offset).limit(limit)
    task_comments = session.execute(paginated_tasks_comment).scalars().all()

    return task_comments


@router.get(
    "/{comment_id}/",
    status_code=status.HTTP_200_OK,
    response_model=TaskCommentRead,
)
async def get_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        Task
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

    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task.id,
        TaskComment.id == comment_id,
    )
    task_comment = session.execute(task_comment_stmt).scalars().one_or_none()

    if task_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task comment not found"
        )

    return task_comment



@router.patch(
    "/{comment_id}/",
    status_code=status.HTTP_200_OK,
    response_model=TaskCommentRead,
)
async def update_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    update_task_comment_data: TaskCommentUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace_stmt = select(
        Workspace,
        WorkspaceMember,
    ).join(
        WorkspaceMember,
        WorkspaceMember.workspace_id == Workspace.id,
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
        Task
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

    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task.id,
        TaskComment.id == comment_id,
    )
    task_comment = session.execute(task_comment_stmt).scalars().one_or_none()

    if task_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task comment not found"
        )

    is_can_change_task_comment = (
        membership.role in ("admin", "owner")
        or task_comment.author_id == current_user.id
    )

    if not is_can_change_task_comment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't change this task comment"
        )

    update_task_comment_data_dict = update_task_comment_data.model_dump(exclude_unset=True)
    if not update_task_comment_data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Change request shouldn't be empty",
        )

    for key, value in update_task_comment_data_dict.items():
        setattr(task_comment, key, value)

    session.commit()
    session.refresh(task_comment)

    return task_comment


@router.delete(
    "/{comment_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace_stmt = select(
        Workspace,
        WorkspaceMember,
    ).join(
        WorkspaceMember,
        WorkspaceMember.workspace_id == Workspace.id,
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
        Task
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

    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task.id,
        TaskComment.id == comment_id,
    )
    task_comment = session.execute(task_comment_stmt).scalars().one_or_none()

    if task_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task comment not found"
        )

    is_can_delete_task_comment = (
        membership.role in ("admin", "owner")
        or task_comment.author_id == current_user.id
    )

    if not is_can_delete_task_comment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't delete this task comment"
        )

    session.delete(task_comment)
    session.commit()

