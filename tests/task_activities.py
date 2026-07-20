from fastapi import status
from sqlalchemy import select

from app.models import TaskActivity


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


def test_change_task_status_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"status": "done"}
    old_status = first_user_workspace_first_task.status

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == old_status
    assert task_activity.new_value == data["status"]
    assert task_activity.event_type == "status_changed"
    assert task_activity.field_name == "status"


def test_change_task_priority_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"priority": "high"}
    old_priority = first_user_workspace_first_task.priority

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == old_priority
    assert task_activity.new_value == data["priority"]
    assert task_activity.event_type == "priority_changed"
    assert task_activity.field_name == "priority"


def test_change_task_assignee_create_activity(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    data = {"assignee_id": second_user.id}
    old_assignee = first_user_workspace_first_task.assignee_id

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == str(old_assignee)
    assert task_activity.new_value == str(data["assignee_id"])
    assert task_activity.event_type == "assignee_changed"
    assert task_activity.field_name == "assignee_id"


def test_remove_task_assignee_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"assignee_id": None}
    old_assignee = first_user_workspace_first_task.assignee_id

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == str(old_assignee)
    assert task_activity.new_value == data["assignee_id"]
    assert task_activity.event_type == "assignee_changed"
    assert task_activity.field_name == "assignee_id"


def test_change_task_title_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"title": "new_title_for_test_activity"}
    old_title = first_user_workspace_first_task.title

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == old_title
    assert task_activity.new_value == data["title"]
    assert task_activity.event_type == "title_changed"
    assert task_activity.field_name == "title"


def test_change_task_due_date_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"due_date": "2026-08-15T12:30:00"}
    old_due_date = first_user_workspace_first_task.due_date

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == old_due_date
    assert task_activity.new_value == data["due_date"]
    assert task_activity.event_type == "due_date_changed"
    assert task_activity.field_name == "due_date"


def test_multiple_changed_fields_create_multiple_activities(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {
        "title": "new_title_for_test_activity",
        "priority": "high",
    }
    old_title = first_user_workspace_first_task.title
    old_priority = first_user_workspace_first_task.priority

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activities = test_session.execute(task_activity_stmt).scalars().all()

    assert len(task_activities) == 2

    activity_event_types = {
        task_activity.event_type
        for task_activity in task_activities
    }

    assert activity_event_types == {
        "title_changed",
        "priority_changed",
    }

    for task_activity in task_activities:
        if task_activity.event_type == "title_changed":
            assert task_activity.field_name == "title"
            assert task_activity.new_value == data["title"]
            assert task_activity.old_value == old_title
        elif task_activity.event_type == "priority_changed":
            assert task_activity.field_name == "priority"
            assert task_activity.new_value == data["priority"]
            assert task_activity.old_value == old_priority

def test_same_field_value_no_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {
        "title": first_user_workspace_first_task.title,
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None


def test_change_description_no_create_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {
        "description": "new description",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None


def test_change_task_title_and_description_create_one_activity(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {
        "title": "new_title_for_test_activity",
        "description": "new description",
    }
    old_title = first_user_workspace_first_task.title

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.old_value == old_title
    assert task_activity.new_value == data["title"]
    assert task_activity.event_type == "title_changed"
    assert task_activity.field_name == "title"


def test_task_activity_contains_actor_task_workspace(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    data = {"title": "new_title_for_test_activity"}

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_200_OK

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
        TaskActivity.actor_id == first_user.id
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is not None
    assert task_activity.actor_id == first_user.id
    assert task_activity.task_id == first_user_workspace_first_task.id
    assert task_activity.workspace_id == first_user_workspace.id


def test_forbidden_patch_creates_no_activity(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    first_user_workspace_first_task.assignee_id = second_user.id

    test_session.commit()

    data = {"priority": "high"}

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN
    assert update_task_response.json()["detail"] == "You are trying to change fields that are not allowed for you"

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None


def test_invalid_assignee_creates_no_activity(
    test_session,
    test_db_client,
    second_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):

    data = {
        "assignee_id": second_user.id
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data,
    )
    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST
    assert update_task_response.json()["detail"] == "This user is not in this workspace"

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == first_user_workspace_first_task.id,
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None
