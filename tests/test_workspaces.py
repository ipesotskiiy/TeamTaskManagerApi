from fastapi import status
from sqlalchemy import select

from app.models import Workspace, WorkspaceMember


def test_create_workspace_success(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
):
    workspace_data = {
        "name": "test_workspace",
        "description": "test_description",
    }
    create_workspace_response = test_db_client.post(
        "/api/v1/workspaces/",
        json=workspace_data,
        headers=authorize_first_user,
    )

    assert create_workspace_response.status_code == status.HTTP_201_CREATED

    workspace_response_data = create_workspace_response.json()
    workspace = test_session.get(Workspace, workspace_response_data["id"])

    assert workspace is not None
    assert isinstance(workspace, Workspace)
    assert workspace.created_by_id == first_user.id

    workspace_member_stmt = select(WorkspaceMember).where(
        WorkspaceMember.user_id == first_user.id,
        WorkspaceMember.workspace_id == workspace.id,
    )

    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is not None
    assert isinstance(workspace_member, WorkspaceMember)
    assert workspace_member.role == "owner"


def test_get_workspaces_returns_only_user_workspaces(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace,
):
    list_workspace_response = test_db_client.get(
        "/api/v1/workspaces/",
        headers=authorize_first_user,
    )
    list_workspace_response_data = list_workspace_response.json()

    ids_workspace_response = {
        workspace["id"]
        for workspace in list_workspace_response_data
    }

    assert list_workspace_response.status_code == status.HTTP_200_OK
    assert len(list_workspace_response_data) == 1
    assert first_user_workspace.id in ids_workspace_response
    assert second_user_workspace.id not in ids_workspace_response


def test_get_workspace_success_for_member(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    response = get_workspace_owner_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )
    response_data = response.json()

    assert get_workspace_owner_response.status_code == status.HTTP_200_OK
    assert response_data["id"] == first_user_workspace.id
    assert response_data["name"] == first_user_workspace.name


def test_get_workspace_not_found_for_non_member(
    test_db_client,
    first_user_workspace,
    authorize_second_user,
):
    get_workspace_no_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_second_user,
    )

    assert get_workspace_no_member_response.status_code == status.HTTP_404_NOT_FOUND


def test_owner_can_update_workspace(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    data_for_update = {"name": "new name"}
    update_workspace_owner_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        json=data_for_update,
        headers=authorize_first_user,
    )

    assert update_workspace_owner_response.status_code == status.HTTP_200_OK

    update_workspace_owner_response_data = update_workspace_owner_response.json()
    workspace = test_session.get(
        Workspace,
        update_workspace_owner_response_data["id"],
    )

    assert workspace.name == data_for_update["name"]


def test_admin_can_update_workspace(
    test_db_client,
    test_session,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    workspace_member_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.user_id == first_user.id,
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is not None

    workspace_member.role = "admin"

    test_session.commit()
    test_session.refresh(workspace_member)

    data_for_update = {"name": "admin new name"}
    update_workspace_admin_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        json=data_for_update,
        headers=authorize_first_user,
    )

    assert update_workspace_admin_response.status_code == status.HTTP_200_OK

    update_workspace_owner_response_data = update_workspace_admin_response.json()
    workspace = test_session.get(Workspace, update_workspace_owner_response_data["id"])

    assert workspace.name == data_for_update["name"]


def test_member_cannot_update_workspace(
    test_db_client,
    test_session,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    workspace_member_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.user_id == first_user.id,
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is not None

    workspace_member.role = "member"

    test_session.commit()
    test_session.refresh(workspace_member)

    data_for_update = {"name": "member new name"}
    update_workspace_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        json=data_for_update,
        headers=authorize_first_user,
    )

    assert update_workspace_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert first_user_workspace.name != data_for_update["name"]


def test_non_member_cannot_update_workspace(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
):
    data_for_update = {"name": "no member new name"}
    update_workspace_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        json=data_for_update,
        headers=authorize_second_user,
    )

    assert update_workspace_member_response.status_code == status.HTTP_404_NOT_FOUND


def test_update_workspace_name_none_returns_400(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    data_for_update = {"name": None}
    update_workspace_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        json=data_for_update,
        headers=authorize_first_user,
    )

    assert update_workspace_member_response.status_code == status.HTTP_400_BAD_REQUEST


def test_owner_can_delete_workspace(
    test_db_client,
    test_session,
    authorize_first_user,
    first_user_workspace,
):
    delete_workspace_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )

    workspace = test_session.get(Workspace, first_user_workspace.id)

    assert delete_workspace_response.status_code == status.HTTP_204_NO_CONTENT
    assert workspace is None


def test_delete_workspace_removes_memberships_by_cascade(
    test_db_client,
    test_session,
    authorize_first_user,
    first_user_workspace,
):
    delete_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )

    workspace_member_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is None
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


def test_admin_cannot_delete_workspace(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    workspace_member_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.user_id == first_user.id,
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is not None

    workspace_member.role = "admin"

    test_session.commit()
    test_session.refresh(workspace_member)

    delete_admin_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )

    assert delete_admin_response.status_code == status.HTTP_403_FORBIDDEN


def test_member_cannot_delete_workspace(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    workspace_member_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.user_id == first_user.id,
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    workspace_member = test_session.execute(
        workspace_member_stmt,
    ).scalars().one_or_none()

    assert workspace_member is not None

    workspace_member.role = "member"

    test_session.commit()
    test_session.refresh(workspace_member)

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_403_FORBIDDEN


def test_non_member_cannot_delete_workspace(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
):
    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_404_NOT_FOUND

