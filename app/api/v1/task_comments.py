from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.dependencies.task_comments import (
    get_task_comment_or_404,
    ensure_comment_action_allowed_or_403,
    ensure_can_comment_task_or_403
)
from app.api.v1.dependencies.tasks import get_task_or_404
from app.api.v1.dependencies.workspaces import (
    get_workspace_and_membership_or_404,
    get_workspace_for_member_or_404,
)
from app.db.session import get_db
from app.models import (
    User,
    TaskComment,
)
from app.schemas.task_comment import (
    TaskCommentRead,
    TaskCommentCreate,
    TaskCommentUpdate,
)
from app.services.task_activity import (
    create_task_comment_activity,
    create_comment_updated_activity,
    create_comment_deleted_activity,
)

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskCommentRead,
)
def create_task_comment(
    workspace_id: int,
    task_id: int,
    task_comment_data: TaskCommentCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    ensure_can_comment_task_or_403(
        membership.role,
        task.created_by_id,
        task.assignee_id,
        current_user.id
    )

    create_task_comment_activity(
        session=session,
        task_comment=task_comment_data.text,
        workspace_id=workspace_id,
        task_id=task_id,
        current_user_id=current_user.id,
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
def get_list_task_comments(
    workspace_id: int,
    task_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    author_id: int | None = Query(None, ge=1, alias="comment_author"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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

    task_comment_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == task.id,
    )

    if author_id is not None:
        task_comment_stmt = task_comment_stmt.where(TaskComment.author_id == author_id)


    paginated_tasks_comment = task_comment_stmt.order_by(TaskComment.id).offset(offset).limit(limit)
    task_comments = session.scalars(paginated_tasks_comment).all()

    return task_comments


@router.get(
    "/{comment_id}/",
    status_code=status.HTTP_200_OK,
    response_model=TaskCommentRead,
)
def get_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    task_comment = get_task_comment_or_404(
        session,
        task.id,
        comment_id
    )
    return task_comment


@router.patch(
    "/{comment_id}/",
    status_code=status.HTTP_200_OK,
    response_model=TaskCommentRead,
)
def update_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    update_task_comment_data: TaskCommentUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    task_comment = get_task_comment_or_404(
        session,
        task.id,
        comment_id,
    )

    ensure_comment_action_allowed_or_403(
        membership.role,
        task_comment.author_id,
        current_user.id,
        "change",
    )

    update_task_comment_data_dict = update_task_comment_data.model_dump(exclude_unset=True)

    for key, value in update_task_comment_data_dict.items():
        if key == "text":
            create_comment_updated_activity(
                session=session,
                old_task_comment_text=task_comment.text,
                new_task_comment_text=value,
                workspace_id=workspace_id,
                task_id=task_id,
                current_user_id=current_user.id
            )
        setattr(task_comment, key, value)

    session.commit()
    session.refresh(task_comment)

    return task_comment


@router.delete(
    "/{comment_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
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
    task_comment = get_task_comment_or_404(
        session,
        task.id,
        comment_id
    )
    ensure_comment_action_allowed_or_403(
        membership.role,
        task_comment.author_id,
        current_user.id,
        "delete",
    )

    create_comment_deleted_activity(
        session=session,
        old_task_comment_text=task_comment.text,
        workspace_id=workspace_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )

    session.delete(task_comment)
    session.commit()

