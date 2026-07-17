from fastapi import status


def test_member_get_task_activities(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_activity,
    first_user_first_workspace_first_task_second_activity,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/",
        headers=authorize_second_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK

    task_activities_id = {
        task_activity["id"]
        for task_activity in get_activities_response.json()
    }

    assert first_user_first_workspace_first_task_first_activity.id in task_activities_id
    assert first_user_first_workspace_first_task_second_activity.id in task_activities_id


def test_return_only_current_task_activities(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_activity,
    first_user_first_workspace_first_task_second_activity,
    first_user_first_workspace_second_task_first_activity,
):
    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/",
        headers=authorize_first_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK

    task_activities_id = {
        task_activity["id"]
        for task_activity in get_activities_response.json()
    }

    assert first_user_first_workspace_first_task_first_activity.id in task_activities_id
    assert first_user_first_workspace_first_task_second_activity.id in task_activities_id
    assert first_user_first_workspace_second_task_first_activity.id not in task_activities_id


def test_return_only_current_workspace_activities(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_activity,
    first_user_first_workspace_first_task_second_activity,
    second_user_first_workspace_first_task_first_activity,
):
    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/",
        headers=authorize_first_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK

    task_activities_id = {
        task_activity["id"]
        for task_activity in get_activities_response.json()
    }

    assert first_user_first_workspace_first_task_first_activity.id in task_activities_id
    assert first_user_first_workspace_first_task_second_activity.id in task_activities_id
    assert second_user_first_workspace_first_task_first_activity.id not in task_activities_id


def test_task_without_activities(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/",
        headers=authorize_first_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK
    assert get_activities_response.json() == []


def test_non_member_get_task_activities(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    get_task_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/",
        headers=authorize_second_user,
    )

    assert get_task_activities_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_task_activities_response.json()["detail"] == "Workspace not found"


def test_get_task_from_another_workspace(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    second_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_task_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/activities/",
        headers=authorize_second_user,
    )

    assert get_task_activities_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_task_activities_response.json()["detail"] == "Task not found"


def test_get_missing_task(
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    get_task_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/99999999/activities/",
        headers=authorize_first_user,
    )

    assert get_task_activities_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_task_activities_response.json()["detail"] == "Task not found"


def test_member_get_task_activities_with_limit(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_activity,
    first_user_first_workspace_first_task_second_activity,
):
    assert (first_user_first_workspace_first_task_first_activity.id <
            first_user_first_workspace_first_task_second_activity.id)

    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/?limit=1",
        headers=authorize_first_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK

    task_activities_id = {
        task_activity["id"]
        for task_activity in get_activities_response.json()
    }

    assert first_user_first_workspace_first_task_first_activity.id in task_activities_id
    assert first_user_first_workspace_first_task_second_activity.id not in task_activities_id


def test_member_get_task_activities_with_offset(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_activity,
    first_user_first_workspace_first_task_second_activity,
):
    assert (first_user_first_workspace_first_task_first_activity.id <
            first_user_first_workspace_first_task_second_activity.id)

    get_activities_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/activities/?offset=1",
        headers=authorize_first_user,
    )

    assert get_activities_response.status_code == status.HTTP_200_OK

    task_activities_id = {
        task_activity["id"]
        for task_activity in get_activities_response.json()
    }

    assert first_user_first_workspace_first_task_first_activity.id not in task_activities_id
    assert first_user_first_workspace_first_task_second_activity.id in task_activities_id
