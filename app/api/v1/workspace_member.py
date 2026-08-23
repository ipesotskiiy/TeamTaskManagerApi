from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
    HTTPException,
)
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.dependencies.workspace_member import (
    get_workspace_member_or_404,
    get_membership_with_workspace_and_user_ids,
    get_user_or_404,
    ensure_role,
    check_is_owner,
    check_correct_role,
    check_permission_for_delete,
    create_workspace_member_read,
)
from app.api.v1.dependencies.workspaces import (
    get_workspace_for_member_or_404,
    get_workspace_and_membership_or_404,
)
from app.db.session import get_db
from app.models import User, WorkspaceMember, Task
from app.schemas.workspace_member import (
    WorkspaceMemberRead,
    WorkspaceMemberRole,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
)

router = APIRouter(prefix="/members", tags=["workspace-members"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[WorkspaceMemberRead],
)
def get_workspace_members(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member_role: WorkspaceMemberRole | None = Query(
        default=None,
        alias="role",
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    workspace_user_stmt = (
        select(
            WorkspaceMember,
            User,
        )
        .join(
            User,
            User.id == WorkspaceMember.user_id,
        )
        .where(
            WorkspaceMember.workspace_id == workspace_id,
        )
    )

    if member_role is not None:
        workspace_user_stmt = workspace_user_stmt.where(
            WorkspaceMember.role == member_role,
        )

    workspace_user_stmt = (
        workspace_user_stmt
        .order_by(WorkspaceMember.id)
        .offset(offset)
        .limit(limit)
    )

    rows = session.execute(workspace_user_stmt).all()

    result = []

    for membership, user in rows:
        result.append(
            WorkspaceMemberRead(
                id=membership.id,
                workspace_id=membership.workspace_id,
                user_id=membership.user_id,
                username=user.username,
                email=user.email,
                role=membership.role,
                created_at=membership.created_at,
            )
        )

    return result


@router.get(
    "/{membership_id}/",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceMemberRead,
)
def get_workspace_member(
    workspace_id: int,
    membership_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    membership, user = get_workspace_member_or_404(
        session,
        workspace_id,
        membership_id,
    )

    return create_workspace_member_read(membership, user)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceMemberRead,
)
def create_workspace_member(
    workspace_id: int,
    workspace_member_data: WorkspaceMemberCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )
    ensure_role(
        membership.role,
        workspace_member_data.role,
    )
    user = get_user_or_404(
        session,
        workspace_member_data.user_id
    )
    existing_membership = get_membership_with_workspace_and_user_ids(
        session,
        workspace_id,
        workspace_member_data.user_id,
    )
    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member",
        )

    workspace_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=workspace_member_data.user_id,
        role=workspace_member_data.role,
    )
    session.add(workspace_member)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member"
        )
    session.refresh(workspace_member)

    return create_workspace_member_read(workspace_member, user)


@router.patch(
    "/{membership_id}/",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceMemberRead,
)
def update_workspace_member_role(
    workspace_id: int,
    membership_id: int,
    change_workspace_data: WorkspaceMemberUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )
    check_is_owner(membership.role)
    changing_membership, user = get_workspace_member_or_404(
        session,
        workspace_id=workspace.id,
        membership_id=membership_id,
    )

    check_correct_role(changing_membership.role)

    update_data = change_workspace_data.model_dump(exclude_unset=True)
    for field_name, field_value in update_data.items():
        setattr(changing_membership, field_name, field_value)

    session.commit()
    session.refresh(changing_membership)

    return create_workspace_member_read(changing_membership, user)

@router.delete(
    "/{membership_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workspace_member(
    workspace_id: int,
    membership_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    current_user_role = membership.role

    deleting_membership, user = get_workspace_member_or_404(
        session,
        workspace_id=workspace.id,
        membership_id=membership_id,
    )

    check_permission_for_delete(
        current_user_role,
        deleting_membership.role
    )

    unassign_tasks_stmt = update(
        Task
    ).where(
        Task.workspace_id == workspace_id,
        Task.assignee_id == user.id
    ).values(
        assignee_id=None
    )
    session.execute(unassign_tasks_stmt)

    session.delete(deleting_membership)
    session.commit()
