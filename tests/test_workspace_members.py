from fastapi import status
from sqlalchemy import select

from app.models import WorkspaceMember


def test_owner_can_get_workspace_members(
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_first_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 2

    members_by_user_id = {
        member["user_id"]: member
        for member in workspace_members_response_data
    }

    assert first_user.id in members_by_user_id
    assert second_user.id in members_by_user_id

    first_user_response_data = members_by_user_id[first_user.id]
    second_user_response_data = members_by_user_id[second_user.id]

    assert first_user.id == first_user_response_data["user_id"]
    assert first_user.username == first_user_response_data["username"]
    assert first_user.email == first_user_response_data["email"]
    assert first_user_response_data["role"] == "owner"

    assert second_user.id == second_user_response_data["user_id"]
    assert second_user.username == second_user_response_data["username"]
    assert second_user.email == second_user_response_data["email"]


def test_admin_can_get_workspace_members(
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 2

    members_by_user_id = {
        member["user_id"]: member
        for member in workspace_members_response_data
    }

    assert first_user.id in members_by_user_id
    assert second_user.id in members_by_user_id

    first_user_response_data = members_by_user_id[first_user.id]
    second_user_response_data = members_by_user_id[second_user.id]

    assert first_user.id == first_user_response_data["user_id"]
    assert first_user.username == first_user_response_data["username"]
    assert first_user.email == first_user_response_data["email"]

    assert second_user.id == second_user_response_data["user_id"]
    assert second_user.username == second_user_response_data["username"]
    assert second_user.email == second_user_response_data["email"]
    assert second_user_response_data["role"] == "admin"


def test_member_can_get_workspace_members(
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 2

    members_by_user_id = {
        member["user_id"]: member
        for member in workspace_members_response_data
    }

    assert first_user.id in members_by_user_id
    assert second_user.id in members_by_user_id

    first_user_response_data = members_by_user_id[first_user.id]
    second_user_response_data = members_by_user_id[second_user.id]

    assert first_user.id == first_user_response_data["user_id"]
    assert first_user.username == first_user_response_data["username"]
    assert first_user.email == first_user_response_data["email"]

    assert second_user.id == second_user_response_data["user_id"]
    assert second_user.username == second_user_response_data["username"]
    assert second_user.email == second_user_response_data["email"]
    assert second_user_response_data["role"] == "member"


def test_get_workspace_members_returns_only_current_workspace_members(
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace,
):

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_first_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    member_user_ids = {
        member["user_id"]
        for member in workspace_members_response_data
    }

    assert first_user.id in member_user_ids
    assert second_user.id not in member_user_ids

    first_user_response_data = workspace_members_response_data[0]

    assert first_user.id == first_user_response_data["user_id"]
    assert first_user.username == first_user_response_data["username"]
    assert first_user.email == first_user_response_data["email"]


def test_non_member_get_workspace_members_gets_404(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
):

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_404_NOT_FOUND
    assert workspace_members_response.json()["detail"] == "Workspace not found"


def test_filter_workspace_members_by_owner_role(
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?role=owner",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    member_user_ids = {
        member["user_id"]
        for member in workspace_members_response_data
    }

    assert first_user.id in member_user_ids
    assert second_user.id not in member_user_ids

    first_user_response_data = workspace_members_response_data[0]

    assert first_user.id == first_user_response_data["user_id"]
    assert first_user.username == first_user_response_data["username"]
    assert first_user.email == first_user_response_data["email"]
    assert first_user_response_data["role"] == "owner"


def test_filter_workspace_members_by_admin_role(
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?role=admin",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    member_user_ids = {
        member["user_id"]
        for member in workspace_members_response_data
    }

    assert first_user.id not in member_user_ids
    assert second_user.id in member_user_ids

    second_user_response_data = workspace_members_response_data[0]

    assert second_user.id == second_user_response_data["user_id"]
    assert second_user.username == second_user_response_data["username"]
    assert second_user.email == second_user_response_data["email"]
    assert second_user_response_data["role"] == "admin"


def test_filter_workspace_members_by_member_role(
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?role=member",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    member_user_ids = {
        member["user_id"]
        for member in workspace_members_response_data
    }

    assert first_user.id not in member_user_ids
    assert second_user.id in member_user_ids

    second_user_response_data = workspace_members_response_data[0]

    assert second_user.id == second_user_response_data["user_id"]
    assert second_user.username == second_user_response_data["username"]
    assert second_user.email == second_user_response_data["email"]
    assert second_user_response_data["role"] == "member"


def test_filter_workspace_members_without_matches_returns_empty_list(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?role=admin",
        headers=authorize_first_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK
    assert workspace_members_response.json() == []


def test_get_workspace_members_limit(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    owner_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == first_user.id,
        )
    )

    second_user_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == second_user.id,
        )
    )

    assert owner_membership is not None
    assert second_user_membership is not None
    assert owner_membership.id < second_user_membership.id

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?limit=1",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    returned_member = workspace_members_response_data[0]

    assert returned_member["id"] == owner_membership.id
    assert returned_member["user_id"] == first_user.id
    assert returned_member["role"] == "owner"


def test_get_workspace_members_offset(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    owner_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == first_user.id,
        )
    )

    second_user_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == second_user.id,
        )
    )

    assert owner_membership is not None
    assert second_user_membership is not None
    assert owner_membership.id < second_user_membership.id

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/?offset=1",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 1

    returned_member = workspace_members_response_data[0]

    assert returned_member["id"] == second_user_membership.id
    assert returned_member["user_id"] == second_user.id
    assert returned_member["role"] == "member"


def test_get_workspace_members_ordered_by_membership_id(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_members_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        headers=authorize_second_user,
    )

    assert workspace_members_response.status_code == status.HTTP_200_OK

    workspace_members_response_data = workspace_members_response.json()

    assert len(workspace_members_response_data) == 2

    membership_ids = [
        member["id"]
        for member in workspace_members_response_data
    ]

    assert membership_ids == sorted(membership_ids)
