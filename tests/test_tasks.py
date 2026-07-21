import pytest
from fastapi import status
from sqlalchemy import select

from app.models import Task, TaskComment, TaskActivity, Workspace


def test_member_can_create_task(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_second_user,
        json={
            "title": "first test task",
            "description": "first task description",
            "assignee_id": first_user.id,
        }
    )

    assert create_task_response.status_code == status.HTTP_201_CREATED

    task_data = create_task_response.json()

    task_obj = test_session.get(Task, task_data["id"])

    assert task_obj is not None
    assert task_obj.title == "first test task"
    assert task_obj.workspace_id == first_user_workspace.id
    assert task_obj.created_by_id == second_user.id
    assert task_obj.assignee_id == first_user.id
    assert task_obj.status == "todo"
    assert task_obj.priority == "medium"

    assert task_data["title"] == "first test task"
    assert task_data["workspace_id"] == first_user_workspace.id
    assert task_data["created_by_id"] == second_user.id


def test_create_task_non_member_gets_404(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
):
    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_second_user,
        json={
            "title": "first test task",
            "description": "first task description",
            "assignee_id": second_user.id,
        }
    )

    assert create_task_response.status_code == status.HTTP_404_NOT_FOUND
    assert create_task_response.json()["detail"] == "Workspace not found"


def test_create_task_with_non_member_assignee_gets_400(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    second_user,
    first_user_workspace,
):
    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_first_user,
        json={
            "title": "first test task",
            "description": "first task description",
            "assignee_id": second_user.id,
        }
    )

    assert create_task_response.status_code == status.HTTP_400_BAD_REQUEST
    assert create_task_response.json()["detail"] == "This user is not in this workspace"


def test_create_task_with_assignee_none_success(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
):
    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_first_user,
        json={
            "title": "first test task",
            "description": "first task description",
        }
    )

    assert create_task_response.status_code == status.HTTP_201_CREATED

    task_data = create_task_response.json()

    task_obj = test_session.get(Task, task_data["id"])

    assert task_obj is not None
    assert task_obj.title == "first test task"
    assert task_obj.workspace_id == first_user_workspace.id
    assert task_obj.created_by_id == first_user.id
    assert task_obj.status == "todo"
    assert task_obj.priority == "medium"
    assert task_obj.assignee_id is None

    assert task_data["title"] == "first test task"
    assert task_data["workspace_id"] == first_user_workspace.id
    assert task_data["created_by_id"] == first_user.id


def test_create_task_with_assignee_member_success(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_first_user,
        json={
            "title": "task with another assignee",
            "description": "task description",
            "assignee_id": second_user.id,
        },
    )

    assert create_task_response.status_code == status.HTTP_201_CREATED

    task_data = create_task_response.json()
    task_obj = test_session.get(Task, task_data["id"])

    assert task_obj is not None
    assert task_obj.created_by_id == first_user.id
    assert task_obj.assignee_id == second_user.id
    assert task_obj.workspace_id == first_user_workspace.id

    assert task_data["assignee_id"] == second_user.id
    assert task_data["created_by_id"] == first_user.id
    assert task_data["workspace_id"] == first_user_workspace.id


def test_member_can_list_workspace_tasks(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_second_user,
    )

    json_data = tasks_list_response.json()

    assert tasks_list_response.status_code == status.HTTP_200_OK
    assert len(json_data) == 2

    tasks_ids = {
        task["id"]
        for task in json_data
    }
    assert first_user_workspace_first_task.id in tasks_ids
    assert first_user_workspace_second_task.id in tasks_ids


def test_list_tasks_returns_only_current_workspace_tasks(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
    second_user_workspace_first_task,
):
    tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_first_user,
    )

    json_data = tasks_list_response.json()

    assert tasks_list_response.status_code == status.HTTP_200_OK
    assert len(json_data) == 2

    tasks_ids = {
        task["id"]
        for task in json_data
    }
    assert first_user_workspace_first_task.id in tasks_ids
    assert first_user_workspace_second_task.id in tasks_ids
    assert second_user_workspace_first_task.id not in tasks_ids


def test_list_tasks_filter_by_status(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
):
    first_user_workspace_first_task.status = "in_progress"
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    in_progress_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?status=in_progress",
        headers=authorize_first_user,
    )
    progress_task_data = in_progress_tasks_list_response.json()

    assert progress_task_data is not None
    assert in_progress_tasks_list_response.status_code == status.HTTP_200_OK

    in_progress_task_ids = {
        task["id"]
        for task in progress_task_data
    }

    assert first_user_workspace_first_task.id in in_progress_task_ids
    assert first_user_workspace_second_task.id not in in_progress_task_ids

    todo_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?status=todo",
        headers=authorize_first_user,
    )
    todo_task_data = todo_tasks_list_response.json()

    assert todo_task_data is not None
    assert todo_tasks_list_response.status_code == status.HTTP_200_OK

    todo_tasks_ids = {
        task["id"]
        for task in todo_task_data
    }

    assert first_user_workspace_first_task.id not in todo_tasks_ids
    assert first_user_workspace_second_task.id in todo_tasks_ids


def test_list_tasks_filter_by_priority(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
):
    first_user_workspace_first_task.priority = "high"
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    high_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?priority=high",
        headers=authorize_first_user,
    )
    high_task_data = high_tasks_list_response.json()

    assert high_task_data is not None
    assert high_tasks_list_response.status_code == status.HTTP_200_OK

    high_task_ids = {
        task["id"]
        for task in high_task_data
    }

    assert first_user_workspace_first_task.id in high_task_ids
    assert first_user_workspace_second_task.id not in high_task_ids

    medium_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?priority=medium",
        headers=authorize_first_user,
    )
    medium_task_data = medium_tasks_list_response.json()

    assert medium_task_data is not None
    assert medium_tasks_list_response.status_code == status.HTTP_200_OK

    medium_tasks_ids = {
        task["id"]
        for task in medium_task_data
    }

    assert first_user_workspace_first_task.id not in medium_tasks_ids
    assert first_user_workspace_second_task.id in medium_tasks_ids


def test_list_tasks_filter_by_assignee_id(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
):
    assignee_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?assignee_id={first_user.id}",
        headers=authorize_first_user,
    )

    assert assignee_tasks_list_response.status_code == status.HTTP_200_OK

    assignee_tasks_list_data = assignee_tasks_list_response.json()

    ids_assignee_tasks = {
        task["id"]
        for task in assignee_tasks_list_data
    }

    assert first_user_workspace_first_task.id in ids_assignee_tasks
    assert first_user_workspace_second_task.id not in ids_assignee_tasks


def test_list_tasks_limit_offset(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
):
    offset_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?offset=1",
        headers=authorize_first_user,
    )

    assert offset_tasks_list_response.status_code == status.HTTP_200_OK

    offset_tasks_list_response_data = offset_tasks_list_response.json()
    assert len(offset_tasks_list_response_data) == 1

    offset_tasks_ids = {
        task["id"]
        for task in offset_tasks_list_response_data
    }

    assert first_user_workspace_first_task.id not in offset_tasks_ids
    assert first_user_workspace_second_task.id in offset_tasks_ids

    limit_tasks_list_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/?limit=1",
        headers=authorize_first_user,
    )

    assert limit_tasks_list_response.status_code == status.HTTP_200_OK

    limit_tasks_list_response_data = limit_tasks_list_response.json()
    assert len(limit_tasks_list_response_data) == 1

    limit_tasks_ids = {
        task["id"]
        for task in limit_tasks_list_response_data
    }

    assert first_user_workspace_first_task.id in limit_tasks_ids
    assert first_user_workspace_second_task.id not in limit_tasks_ids


def test_member_can_get_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_task_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
    )

    assert get_task_response.status_code == status.HTTP_200_OK
    task_data = get_task_response.json()
    assert task_data["id"] == first_user_workspace_second_task.id
    assert task_data["title"] == first_user_workspace_second_task.title


def test_non_member_get_task_gets_404(
    test_db_client,
    first_user_workspace,
    first_user_workspace_first_task,
    authorize_second_user,
):
    get_task_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
    )

    assert get_task_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_task_from_another_workspace_gets_404(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace_first_task,
):
    get_task_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/",
        headers=authorize_first_user,
    )

    assert get_task_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_missing_task_gets_404(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    get_task_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/999999/",
        headers=authorize_first_user,
    )

    assert get_task_response.status_code == status.HTTP_404_NOT_FOUND


def test_non_member_cannot_list_tasks(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
):
    get_list_tasks_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_second_user,
    )

    assert get_list_tasks_response.status_code == status.HTTP_404_NOT_FOUND


def test_owner_can_delete_task(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
    )

    assert delete_task_response.status_code == status.HTTP_204_NO_CONTENT

    test_session.expire_all()
    deleted_task = test_session.get(Task, first_user_workspace_first_task.id)

    assert deleted_task is None


def test_admin_can_delete_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
    )

    assert delete_task_response.status_code == status.HTTP_204_NO_CONTENT

    test_session.expire_all()
    deleted_task = test_session.get(Task, first_user_workspace_first_task.id)

    assert deleted_task is None


def test_creator_can_delete_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
    )

    assert delete_task_response.status_code == status.HTTP_204_NO_CONTENT

    test_session.expire_all()
    deleted_task = test_session.get(Task, first_user_workspace_first_task.id)

    assert deleted_task is None


def test_assignee_only_cannot_delete_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
    )

    assert delete_task_response.status_code == status.HTTP_403_FORBIDDEN
    assert "You cannot delete this task" in delete_task_response.text

    task = test_session.get(Task, first_user_workspace_second_task.id)
    assert task is not None



def test_regular_member_cannot_delete_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
    )

    assert delete_task_response.status_code == status.HTTP_403_FORBIDDEN
    assert "You cannot delete this task" in delete_task_response.text

    task = test_session.get(Task, first_user_workspace_second_task.id)
    assert task is not None


def test_non_member_delete_gets_404(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
    )

    assert delete_task_response.status_code == status.HTTP_404_NOT_FOUND

    task = test_session.get(Task, first_user_workspace_second_task.id)
    assert task is not None


def test_delete_task_from_another_workspace_gets_404(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace_first_task,
):
    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/",
        headers=authorize_first_user,
    )

    assert delete_task_response.status_code == status.HTTP_404_NOT_FOUND

    task = test_session.get(Task, second_user_workspace_first_task.id)
    assert task is not None


def test_owner_can_update_any_task_field(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    update_data = {
        "title": "updated task title",
        "description": "updated task description",
        "status": "in_progress",
        "priority": "high",
        "assignee_id": second_user.id,
        "due_date": "2030-01-01T12:00:00",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()

    assert task_data["title"] == update_data["title"]
    assert task_data["description"] == update_data["description"]
    assert task_data["status"] == update_data["status"]
    assert task_data["priority"] == update_data["priority"]
    assert task_data["assignee_id"] == second_user.id
    assert task_data["due_date"] is not None

    test_session.refresh(first_user_workspace_second_task)

    assert first_user_workspace_second_task.title == update_data["title"]
    assert first_user_workspace_second_task.description == update_data["description"]
    assert first_user_workspace_second_task.status == update_data["status"]
    assert first_user_workspace_second_task.priority == update_data["priority"]
    assert first_user_workspace_second_task.assignee_id == second_user.id
    assert first_user_workspace_second_task.due_date is not None


def test_admin_can_update_any_task_field(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    update_data = {
        "title": "updated task title",
        "description": "updated task description",
        "status": "in_progress",
        "priority": "high",
        "assignee_id": second_user.id,
        "due_date": "2030-01-01T12:00:00",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()

    assert task_data["title"] == update_data["title"]
    assert task_data["description"] == update_data["description"]
    assert task_data["status"] == update_data["status"]
    assert task_data["priority"] == update_data["priority"]
    assert task_data["assignee_id"] == second_user.id
    assert task_data["due_date"] is not None

    test_session.refresh(first_user_workspace_second_task)

    assert first_user_workspace_second_task.title == update_data["title"]
    assert first_user_workspace_second_task.description == update_data["description"]
    assert first_user_workspace_second_task.status == update_data["status"]
    assert first_user_workspace_second_task.priority == update_data["priority"]
    assert first_user_workspace_second_task.assignee_id == second_user.id
    assert first_user_workspace_second_task.due_date is not None


def test_creator_can_update_title_description_priority_due_date(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.created_by_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "title": "updated task title",
        "description": "updated task description",
        "priority": "high",
        "due_date": "2030-01-01T12:00:00",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()

    assert task_data["title"] == update_data["title"]
    assert task_data["description"] == update_data["description"]
    assert task_data["priority"] == update_data["priority"]
    assert task_data["due_date"] is not None

    test_session.refresh(first_user_workspace_second_task)

    assert first_user_workspace_second_task.title == update_data["title"]
    assert first_user_workspace_second_task.description == update_data["description"]
    assert first_user_workspace_second_task.priority == update_data["priority"]
    assert first_user_workspace_second_task.due_date is not None


def test_assignee_can_update_status(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "status": "in_progress",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()
    assert task_data["status"] == update_data["status"]

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.status == update_data["status"]


def test_creator_and_assignee_can_update_creator_fields_and_status(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.assignee_id = second_user.id
    first_user_workspace_second_task.created_by_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "title": "updated task title",
        "description": "updated task description",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2030-01-01T12:00:00",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()
    assert task_data["title"] == update_data["title"]
    assert task_data["description"] == update_data["description"]
    assert task_data["status"] == update_data["status"]
    assert task_data["priority"] == update_data["priority"]
    assert task_data["due_date"] is not None

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title == update_data["title"]
    assert first_user_workspace_second_task.description == update_data["description"]
    assert first_user_workspace_second_task.status == update_data["status"]
    assert first_user_workspace_second_task.priority == update_data["priority"]
    assert first_user_workspace_second_task.due_date is not None


def test_regular_member_cannot_update_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    update_data = {
        "title": "updated task title",
        "description": "updated task description",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2030-01-01T12:00:00",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN
    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title != update_data["title"]
    assert first_user_workspace_second_task.description != update_data["description"]
    assert first_user_workspace_second_task.status != update_data["status"]
    assert first_user_workspace_second_task.priority != update_data["priority"]


def test_creator_cannot_update_status(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.created_by_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "status": "in_progress",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.status != update_data["status"]


def test_creator_cannot_update_assignee_id(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.created_by_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "assignee_id": second_user.id,
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.assignee_id != update_data["assignee_id"]


def test_assignee_cannot_update_title(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.assignee_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "title": "updated task title",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title != update_data["title"]


def test_update_task_empty_payload_gets_400(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    old_title = first_user_workspace_second_task.title
    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json={},
    )

    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title is not None
    assert first_user_workspace_second_task.title == old_title


def test_update_task_title_none_gets_400(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    old_title = first_user_workspace_second_task.title
    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json={"title": None},
    )

    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title is not None
    assert first_user_workspace_second_task.title == old_title


def test_update_task_status_none_gets_400(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    old_status = first_user_workspace_second_task.status
    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json={"status": None},
    )

    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.status is not None
    assert first_user_workspace_second_task.status == old_status


def test_update_task_priority_none_gets_400(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    old_priority = first_user_workspace_second_task.priority
    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json={"priority": None},
    )

    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.priority is not None
    assert first_user_workspace_second_task.priority == old_priority


def test_owner_can_set_assignee_to_workspace_member(
    test_session,
    test_db_client,
    authorize_first_user,
    second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    update_data = {
        "assignee_id": second_user.id,
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()
    assert task_data["assignee_id"] == second_user.id

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.assignee_id == second_user.id


def test_owner_cannot_set_non_member_assignee(
    test_session,
    test_db_client,
    authorize_first_user,
    second_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    update_data = {
        "assignee_id": second_user.id,
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_400_BAD_REQUEST

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.assignee_id != second_user.id


def test_owner_can_set_assignee_to_none(
    test_session,
    test_db_client,
    authorize_first_user,
    second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_second_task.assignee_id = second_user.id

    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    update_data = {
        "assignee_id": None,
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_200_OK

    task_data = update_task_response.json()
    assert task_data["assignee_id"] != second_user.id
    assert task_data["assignee_id"] is None

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.assignee_id != second_user.id
    assert first_user_workspace_second_task.assignee_id is None


def test_non_member_update_task_gets_404(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    update_data = {
        "title": "updated task title",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/",
        headers=authorize_second_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_404_NOT_FOUND

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title != update_data["title"]


def test_update_task_from_another_workspace_gets_404(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace_first_task,
):
    update_data = {
        "title": "updated task title",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_404_NOT_FOUND

    test_session.refresh(second_user_workspace_first_task)
    assert second_user_workspace_first_task.title != update_data["title"]


def test_update_missing_task_gets_404(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    update_data = {
        "title": "updated task title",
    }

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/999999/",
        headers=authorize_first_user,
        json=update_data,
    )

    assert update_task_response.status_code == status.HTTP_404_NOT_FOUND

    test_session.refresh(first_user_workspace_second_task)
    assert first_user_workspace_second_task.title != update_data["title"]


@pytest.mark.parametrize(
    "data",
    [
        {"title": ""},
        {"title": "a" * 201},
        {
            "title": "valid title",
            "priority": "super_duper",
        },
        {
            "title": "valid title",
            "assignee_id": 0,
        },
        {
            "title": "valid title",
            "due_date": "hi",
        },
    ],
)
def test_create_task_invalid_payload_gets_422(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    add_workspace_member,
    data
):
    add_workspace_member(first_user_workspace, second_user)

    create_task_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/",
        headers=authorize_second_user,
        json=data
    )

    assert create_task_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "data",
    [
        {"title": ""},
        {"title": "a" * 201},
        {"status": "unknown_status"},
        {"priority": "super_duper"},
        {"assignee_id": 0},
        {"due_date": "hi"}
    ]
)
def test_update_task_invalid_payload_gets_422(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    data
):

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
        json=data
    )

    assert update_task_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_assignee_mixed_allowed_and_forbidden_fields_gets_403_without_partial_update(
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
    test_session.refresh(first_user_workspace_first_task)

    data = {
        "status": "in_progress",
        "title": "new_updated_title",
    }

    old_status = first_user_workspace_first_task.status
    old_title = first_user_workspace_first_task.title

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
        json=data
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_first_task)

    assert first_user_workspace_first_task.status == old_status
    assert first_user_workspace_first_task.title == old_title


def test_creator_and_assignee_cannot_update_assignee_id(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    first_user_workspace_first_task.assignee_id = second_user.id
    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    data = {
        "assignee_id": first_user.id,
    }

    old_assignee_id = first_user_workspace_first_task.assignee_id

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
        json=data
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_first_task)

    assert first_user_workspace_first_task.assignee_id == old_assignee_id


def test_delete_missing_task_gets_404(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/9999999999999999/",
        headers=authorize_first_user,
    )

    assert delete_task_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_task_cascades_comments_and_activities(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    task_id = first_user_workspace_first_task.id
    comment_id = first_user_first_workspace_first_task_first_comment.id

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_first_user,
    )

    assert delete_task_response.status_code == status.HTTP_204_NO_CONTENT

    task = test_session.get(Task, task_id)
    assert task is None

    task_comment = test_session.get(TaskComment, comment_id)
    assert task_comment is None

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == first_user_workspace.id,
        TaskActivity.task_id == task_id,
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None


def test_delete_workspace_cascades_tasks_comments_and_activities(
    test_session,
    test_db_client,
    first_user,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    workspace_id = first_user_workspace.id
    task_id = first_user_workspace_first_task.id
    comment_id = first_user_first_workspace_first_task_first_comment.id

    delete_task_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/",
        headers=authorize_first_user,
    )

    assert delete_task_response.status_code == status.HTTP_204_NO_CONTENT

    workspace = test_session.get(Workspace, workspace_id)
    assert workspace is None

    task = test_session.get(Task, task_id)
    assert task is None

    task_comment = test_session.get(TaskComment, comment_id)
    assert task_comment is None

    task_activity_stmt = select(
        TaskActivity,
    ).where(
        TaskActivity.workspace_id == workspace_id,
        TaskActivity.task_id == task_id,
    )

    task_activity = test_session.execute(task_activity_stmt).scalars().one_or_none()

    assert task_activity is None

def test_creator_mixed_allowed_and_forbidden_fields_gets_403_without_partial_update(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    data = {
        "title": "hi",
        "status": "in_progress"
    }

    old_title = first_user_workspace_first_task.title
    old_status = first_user_workspace_first_task.status

    update_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/",
        headers=authorize_second_user,
        json=data
    )

    assert update_task_response.status_code == status.HTTP_403_FORBIDDEN

    test_session.refresh(first_user_workspace_first_task)

    assert first_user_workspace_first_task.title == old_title
    assert first_user_workspace_first_task.status == old_status
