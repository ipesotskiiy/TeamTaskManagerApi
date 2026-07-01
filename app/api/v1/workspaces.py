from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.dependencies.workspaces import (
    check_workspace_role,
    get_workspace_and_membership_or_404,
    get_workspace_for_member_or_404,
    get_workspace_update_data,
)
from app.db.session import get_db
from app.models import (
    User,
    Workspace,
    WorkspaceMember,
)
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post(
    "/",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        created_by_id=current_user.id,
    )

    session.add(workspace)
    session.flush()

    workspace_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )

    session.add(workspace_member)
    session.commit()
    session.refresh(workspace)

    return workspace


@router.get(
    "/",
    response_model=list[WorkspaceRead],
    status_code=status.HTTP_200_OK,
)
async def get_workspaces(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces_stmt = select(
        Workspace
    ).join(
        WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id,
    ).where(
        WorkspaceMember.user_id == current_user.id,
    )

    return session.execute(workspaces_stmt).scalars().all()


@router.get(
    "/{workspace_id}/",
    response_model=WorkspaceRead,
)
async def get_workspace(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = get_workspace_for_member_or_404(
        session,
        workspace_id,
        current_user.id,
    )
    return workspace


@router.patch(
    "/{workspace_id}/",
    response_model=WorkspaceRead,
)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    check_workspace_role(
        membership,
        ("owner", "admin"),
        "Only owner and admin can change workspace",
    )

    update_data = get_workspace_update_data(workspace_data)

    for key, value in update_data.items():
        setattr(workspace, key, value)

    session.commit()
    session.refresh(workspace)

    return workspace


@router.delete(
    "/{workspace_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    workspace_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace, membership = get_workspace_and_membership_or_404(
        session,
        workspace_id,
        current_user.id,
    )

    check_workspace_role(
        membership,
        ("owner",),
        "Only owner can delete workspace",
    )

    session.delete(workspace)
    session.commit()
