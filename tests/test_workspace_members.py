from fastapi import status
from sqlalchemy import select

from app.models import WorkspaceMember, Task


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


def test_owner_can_get_workspace_member(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    second_user_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == second_user.id,
        )
    )

    assert second_user_membership is not None

    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{second_user_membership.id}/",
        headers=authorize_first_user,
    )

    assert workspace_member_response.status_code == status.HTTP_200_OK

    workspace_member_response_data = workspace_member_response.json()

    assert workspace_member_response_data["id"] == second_user_membership.id
    assert workspace_member_response_data["workspace_id"] == first_user_workspace.id
    assert workspace_member_response_data["user_id"] == second_user.id
    assert workspace_member_response_data["role"] == "member"
    assert workspace_member_response_data["username"] == second_user.username
    assert workspace_member_response_data["email"] == second_user.email


def test_admin_can_get_workspace_member(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(
        first_user_workspace,
        second_user,
        "admin",
    )

    owner_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == first_user.id,
        )
    )

    assert owner_membership is not None

    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/"
        f"{owner_membership.id}/",
        headers=authorize_second_user,
    )

    assert workspace_member_response.status_code == status.HTTP_200_OK

    workspace_member_response_data = workspace_member_response.json()

    assert workspace_member_response_data["id"] == owner_membership.id
    assert workspace_member_response_data["workspace_id"] == first_user_workspace.id
    assert workspace_member_response_data["user_id"] == first_user.id
    assert workspace_member_response_data["username"] == first_user.username
    assert workspace_member_response_data["email"] == first_user.email
    assert workspace_member_response_data["role"] == "owner"


def test_member_can_get_workspace_member(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(
        first_user_workspace,
        second_user,
        "member",
    )

    owner_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == first_user.id,
        )
    )

    assert owner_membership is not None

    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/"
        f"{owner_membership.id}/",
        headers=authorize_second_user,
    )

    assert workspace_member_response.status_code == status.HTTP_200_OK

    workspace_member_response_data = workspace_member_response.json()

    assert workspace_member_response_data["id"] == owner_membership.id
    assert workspace_member_response_data["workspace_id"] == first_user_workspace.id
    assert workspace_member_response_data["user_id"] == first_user.id
    assert workspace_member_response_data["username"] == first_user.username
    assert workspace_member_response_data["email"] == first_user.email
    assert workspace_member_response_data["role"] == "owner"


def test_get_missing_workspace_member_gets_404(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/999999/",
        headers=authorize_first_user,
    )

    assert workspace_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert workspace_member_response.json()["detail"] == "Workspace member not found"


def test_get_workspace_member_from_another_workspace_gets_404(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace,
    second_user,
):
    second_workspace_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == second_user_workspace.id,
            WorkspaceMember.user_id == second_user.id,
        )
    )

    assert second_workspace_membership is not None

    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/"
        f"{second_workspace_membership.id}/",
        headers=authorize_first_user,
    )

    assert workspace_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        workspace_member_response.json()["detail"]
        == "Workspace member not found"
    )


def test_non_member_get_workspace_member_gets_404(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user,
):
    owner_membership = test_session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == first_user_workspace.id,
            WorkspaceMember.user_id == first_user.id,
        )
    )

    assert owner_membership is not None

    workspace_member_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{owner_membership.id}/",
        headers=authorize_second_user,
    )

    assert workspace_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert workspace_member_response.json()["detail"] == "Workspace not found"


def test_owner_can_create_workspace_member_with_default_role(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": second_user.id
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_201_CREATED

    add_member_response_data = add_member_response.json()

    assert add_member_response_data["role"] == "member"
    assert add_member_response_data["workspace_id"] == first_user_workspace.id
    assert add_member_response_data["user_id"] == second_user.id
    assert add_member_response_data["username"] == second_user.username
    assert add_member_response_data["email"] == second_user.email
    assert "created_at" in add_member_response_data
    assert "id" in add_member_response_data

    membership = test_session.get(WorkspaceMember, add_member_response_data["id"])

    assert membership is not None
    assert membership.role == add_member_response_data["role"]
    assert membership.workspace_id == add_member_response_data["workspace_id"]
    assert membership.user_id == add_member_response_data["user_id"]
    assert membership.created_at is not None
    assert membership.id is not None


def test_owner_can_create_workspace_admin(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": second_user.id,
        "role": "admin",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_201_CREATED

    add_member_response_data = add_member_response.json()
    assert add_member_response_data["role"] == "admin"
    assert add_member_response_data["workspace_id"] == first_user_workspace.id
    assert add_member_response_data["user_id"] == second_user.id
    assert add_member_response_data["username"] == second_user.username
    assert add_member_response_data["email"] == second_user.email
    assert "created_at" in add_member_response_data
    assert "id" in add_member_response_data

    membership = test_session.get(WorkspaceMember, add_member_response_data["id"])
    assert membership is not None
    assert membership.role == add_member_response_data["role"]
    assert membership.workspace_id == add_member_response_data["workspace_id"]
    assert membership.user_id == add_member_response_data["user_id"]
    assert membership.created_at is not None
    assert membership.id is not None


def test_admin_can_create_workspace_member(
    test_session,
    test_db_client,
    second_user,
    third_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    add_member_data = {
        "user_id": third_user.id,
        "role": "member",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    assert add_member_response.status_code == status.HTTP_201_CREATED

    add_member_response_data = add_member_response.json()
    assert add_member_response_data["role"] == "member"
    assert add_member_response_data["workspace_id"] == first_user_workspace.id
    assert add_member_response_data["user_id"] == third_user.id
    assert add_member_response_data["username"] == third_user.username
    assert add_member_response_data["email"] == third_user.email
    assert "created_at" in add_member_response_data
    assert "id" in add_member_response_data

    membership = test_session.get(WorkspaceMember, add_member_response_data["id"])
    assert membership is not None
    assert membership.role == add_member_response_data["role"]
    assert membership.workspace_id == add_member_response_data["workspace_id"]
    assert membership.user_id == add_member_response_data["user_id"]
    assert membership.created_at is not None
    assert membership.id is not None


def test_admin_cannot_create_workspace_admin(
    test_session,
    test_db_client,
    second_user,
    third_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    add_member_data = {
        "user_id": third_user.id,
        "role": "admin",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    assert add_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert add_member_response.json()["detail"] == "Only owner can add workspace admin"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )
    membership = test_session.scalar(membership_stmt)

    assert membership is None


def test_member_cannot_create_workspace_member(
    test_session,
    test_db_client,
    second_user,
    third_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    add_member_data = {
        "user_id": third_user.id,
        "role": "member",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    assert add_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert add_member_response.json()["detail"] == "You cannot add workspace members"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )
    membership = test_session.scalar(membership_stmt)

    assert membership is None


def test_non_member_create_workspace_member_gets_404(
    test_session,
    test_db_client,
    third_user,
    first_user_workspace,
    authorize_second_user,
):
    add_member_data = {
        "user_id": third_user.id,
        "role": "member",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    assert add_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert add_member_response.json()["detail"] == "Workspace not found"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )
    membership = test_session.scalar(membership_stmt)

    assert membership is None


def test_create_workspace_member_with_missing_user_gets_404(
    test_session,
    test_db_client,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": 999999999999,
        "role": "member",
    }
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    old_count_membership = len(test_session.scalars(membership_stmt).all())

    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert add_member_response.json()["detail"] == "User not found"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    new_count_membership = len(test_session.scalars(membership_stmt).all())

    assert old_count_membership == new_count_membership


def test_create_duplicate_workspace_member_gets_409(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    add_member_data = {
        "user_id": second_user.id,
        "role": "member",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_409_CONFLICT
    assert add_member_response.json()["detail"] == "User is already a workspace member"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id
    )
    membership_count = len(test_session.scalars(membership_stmt).all())

    assert membership_count == 1


def test_owner_cannot_add_self_as_workspace_member(
    test_session,
    test_db_client,
    first_user,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": first_user.id,
        "role": "member",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_409_CONFLICT
    assert add_member_response.json()["detail"] == "User is already a workspace member"

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id
    )
    membership_count = len(test_session.scalars(membership_stmt).all())

    assert membership_count == 1


def test_create_workspace_member_with_owner_role_gets_422(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": second_user.id,
        "role": "owner",
    }
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id
    )
    membership = test_session.scalar(membership_stmt)

    assert membership is None


def test_create_workspace_member_with_zero_user_id_gets_422(
    test_session,
    test_db_client,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "user_id": 0,
        "role": "member",
    }
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    old_count_membership = len(test_session.scalars(membership_stmt).all())

    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    new_count_membership = len(test_session.scalars(membership_stmt).all())

    assert old_count_membership == new_count_membership


def test_create_workspace_member_without_user_id_gets_422(
    test_session,
    test_db_client,
    first_user_workspace,
    authorize_first_user,
):
    add_member_data = {
        "role": "member",
    }
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    old_count_membership = len(test_session.scalars(membership_stmt).all())

    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_first_user,
    )

    assert add_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    new_count_membership = len(test_session.scalars(membership_stmt).all())

    assert old_count_membership == new_count_membership


def test_member_adding_missing_user_gets_403_before_user_lookup(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    add_member_data = {
        "user_id": 9999999999,
        "role": "member",
    }
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    old_count_membership = len(test_session.scalars(membership_stmt).all())
    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    new_count_membership = len(test_session.scalars(membership_stmt).all())

    assert add_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert add_member_response.json()["detail"] == "You cannot add workspace members"
    assert old_count_membership == new_count_membership


def test_non_member_adding_missing_user_gets_workspace_404(
    test_session,
    test_db_client,
    first_user_workspace,
    authorize_second_user,
):
    add_member_data = {
        "user_id": 9999999999,
        "role": "member",
    }
    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    old_count_membership = len(test_session.scalars(membership_stmt).all())

    add_member_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/",
        json=add_member_data,
        headers=authorize_second_user,
    )

    membership_stmt = select(
        WorkspaceMember,
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
    )
    new_count_membership = len(test_session.scalars(membership_stmt).all())

    assert add_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert add_member_response.json()["detail"] == "Workspace not found"
    assert old_count_membership == new_count_membership


def test_owner_can_promote_workspace_member_to_admin(
    test_session,
    test_db_client,
    first_user,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )

    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }

    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_200_OK

    workspace_membership_data = update_member_response.json()

    assert workspace_membership_data["user_id"] == second_user.id
    assert workspace_membership_data["username"] == second_user.username
    assert workspace_membership_data["email"] == second_user.email
    assert workspace_membership_data["role"] == "admin"

    new_workspace_membership = test_session.get(WorkspaceMember, workspace_membership_data["id"])

    assert new_workspace_membership is not None
    assert new_workspace_membership.user_id == second_user.id
    assert new_workspace_membership.role == "admin"


def test_owner_can_demote_workspace_admin_to_member(
    test_session,
    test_db_client,
    first_user,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )

    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    update_member_data = {
        "role": "member",
    }

    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_200_OK

    workspace_membership_data = update_member_response.json()

    assert workspace_membership_data["user_id"] == second_user.id
    assert workspace_membership_data["username"] == second_user.username
    assert workspace_membership_data["email"] == second_user.email
    assert workspace_membership_data["role"] == "member"

    new_workspace_membership = test_session.get(WorkspaceMember, workspace_membership_data["id"])

    assert new_workspace_membership is not None
    assert new_workspace_membership.user_id == second_user.id
    assert new_workspace_membership.role == "member"


def test_owner_can_update_workspace_member_with_same_role(
    test_session,
    test_db_client,
    first_user,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )

    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    update_member_data = {
        "role": "member",
    }

    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_200_OK

    workspace_membership_data = update_member_response.json()

    assert workspace_membership_data["user_id"] == second_user.id
    assert workspace_membership_data["username"] == second_user.username
    assert workspace_membership_data["email"] == second_user.email
    assert workspace_membership_data["role"] == "member"

    new_workspace_membership = test_session.get(WorkspaceMember, workspace_membership_data["id"])

    assert new_workspace_membership is not None
    assert new_workspace_membership.user_id == second_user.id
    assert new_workspace_membership.role == "member"

    assert workspace_member.id == new_workspace_membership.id


def test_admin_cannot_update_workspace_member_role(
    test_session,
    test_db_client,
    third_user,
    second_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    add_workspace_member(first_user_workspace, third_user)

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )

    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }

    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_second_user,
    )

    assert update_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert update_member_response.json()["detail"] == "Only owner can change workspace member roles"

    membership_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )

    membership = test_session.scalar(membership_stmt)

    assert membership is not None
    assert membership.role == "member"


def test_member_cannot_update_workspace_member_role(
    test_session,
    test_db_client,
    third_user,
    second_user,
    first_user_workspace,
    authorize_second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    add_workspace_member(first_user_workspace, third_user)

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )

    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }

    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_second_user,
    )

    assert update_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert update_member_response.json()["detail"] == "Only owner can change workspace member roles"

    membership_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )

    membership = test_session.scalar(membership_stmt)

    assert membership is not None
    assert membership.role == "member"


def test_non_member_cannot_update_workspace_member_role(
    test_session,
    test_db_client,
    first_user,
    second_user,
    first_user_workspace,
    authorize_second_user,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_second_user,
    )

    assert update_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_member_response.json()["detail"] == "Workspace not found"

    workspace_membership_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id
    )

    membership = test_session.scalar(workspace_membership_stmt)

    assert membership is not None
    assert membership.role == "owner"


def test_unauthenticated_user_cannot_update_workspace_member_role(
    test_session,
    test_db_client,
    first_user,
    first_user_workspace,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
    )

    assert update_member_response.status_code == status.HTTP_401_UNAUTHORIZED

    workspace_membership_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id
    )

    membership = test_session.scalar(workspace_membership_stmt)

    assert membership is not None
    assert membership.role == "owner"


def test_owner_cannot_update_member_from_another_workspace(
    test_session,
    test_db_client,
    third_user,
    first_user_workspace,
    second_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(second_user_workspace, third_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == second_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_member_response.json()["detail"] == "Workspace member not found"

    workspace_membership_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == second_user_workspace.id,
        WorkspaceMember.user_id == third_user.id
    )

    membership = test_session.scalar(workspace_membership_stmt)

    assert membership is not None
    assert membership.role == "member"


def test_update_workspace_member_returns_404_for_missing_membership(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/9999/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_member_response.json()["detail"] == "Workspace member not found"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_update_workspace_member_returns_404_for_missing_workspace(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/9999/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_member_response.json()["detail"] == "Workspace not found"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_owner_cannot_change_workspace_owner_role(
    test_session,
    test_db_client,
    first_user,
    first_user_workspace,
    authorize_first_user,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "owner"

    update_member_data = {
        "role": "admin",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert update_member_response.json()["detail"] == "Workspace owner role cannot be changed"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "owner"


def test_workspace_member_role_cannot_be_changed_to_owner(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {
        "role": "owner",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_update_workspace_member_rejects_invalid_role(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {
        "role": "owner_t",
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_update_workspace_member_rejects_empty_body(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {}
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_update_workspace_member_rejects_null_role(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    authorize_first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"

    update_member_data = {
        "role": None,
    }
    update_member_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        json=update_member_data,
        headers=authorize_first_user,
    )

    assert update_member_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)
    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_owner_can_delete_workspace_member(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_204_NO_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is None


def test_owner_can_delete_workspace_admin(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "admin"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_204_NO_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is None


def test_admin_can_delete_workspace_member(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    second_user,
    third_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    add_workspace_member(first_user_workspace, third_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_204_NO_CONTENT

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is None


def test_admin_cannot_delete_workspace_admin(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    second_user,
    third_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    add_workspace_member(first_user_workspace, third_user, "admin")
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "admin"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_member_response.json()["detail"] == "Admin can remove only member"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "admin"


def test_admin_cannot_delete_workspace_owner(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    second_user,
    first_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_member_response.json()["detail"] == "Admin can remove only member"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"


def test_member_cannot_delete_workspace_member(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    second_user,
    third_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    add_workspace_member(first_user_workspace, third_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_member_response.json()["detail"] == "Member cannot remove anyone from workspace"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == third_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"


def test_owner_cannot_delete_workspace_owner(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_member_response.json()["detail"] == "Workspace owner cannot be removed"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"


def test_non_member_cannot_delete_workspace_member(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    second_user,
    first_user,
    add_workspace_member,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_second_user,
    )

    assert delete_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_member_response.json()["detail"] == "Workspace not found"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"


def test_unauthenticated_user_cannot_delete_workspace_member(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user,
    add_workspace_member,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
    )

    assert delete_member_response.status_code == status.HTTP_401_UNAUTHORIZED

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == first_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "owner"


def test_delete_workspace_member_returns_404_for_missing_membership(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    add_workspace_member,
):
    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/99999/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_member_response.json()["detail"] == "Workspace member not found"


def test_delete_workspace_member_returns_404_for_missing_workspace(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/999999/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_member_response.json()["detail"] == "Workspace not found"


def test_owner_cannot_delete_member_from_another_workspace(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace,
    second_user,
    add_workspace_member,
):
    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == second_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_member_response.json()["detail"] == "Workspace member not found"

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == second_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None


def test_deleting_workspace_member_unassigns_member_from_workspace_tasks(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    add_workspace_member,
    authorize_first_user,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    first_user_workspace_second_task.assignee_id = second_user.id

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_204_NO_CONTENT

    first_task = test_session.get(Task, first_user_workspace_first_task.id)
    second_task = test_session.get(Task, first_user_workspace_second_task.id)

    assert first_task.assignee_id is None
    assert second_task.assignee_id is None


def test_deleting_workspace_member_does_not_unassign_tasks_from_another_workspace(
    test_session,
    test_db_client,
    second_user,
    first_user_workspace,
    second_user_workspace,
    add_workspace_member,
    authorize_first_user,
    first_user_workspace_first_task,
    second_user_workspace_first_task,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    second_user_workspace_first_task.assignee_id = second_user.id

    workspace_member_stmt = select(
        WorkspaceMember
    ).where(
        WorkspaceMember.workspace_id == first_user_workspace.id,
        WorkspaceMember.user_id == second_user.id,
    )
    workspace_member = test_session.scalar(workspace_member_stmt)

    assert workspace_member is not None
    assert workspace_member.role == "member"

    delete_member_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/members/{workspace_member.id}/",
        headers=authorize_first_user,
    )

    assert delete_member_response.status_code == status.HTTP_204_NO_CONTENT

    first_task = test_session.get(Task, first_user_workspace_first_task.id)
    second_task = test_session.get(Task, second_user_workspace_first_task.id)

    assert first_task.assignee_id is None
    assert second_task.assignee_id == second_user.id
