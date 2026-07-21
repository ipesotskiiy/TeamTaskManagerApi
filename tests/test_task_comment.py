from fastapi import status
from sqlalchemy import select

from app.models import TaskComment


def test_owner_create_comment(
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

    first_user_workspace_second_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_second_task)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_first_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    create_comment_response_data = create_comment_response.json()
    task_comment = test_session.get(TaskComment, create_comment_response_data["id"])

    assert task_comment.text == "test_owner_comment"
    assert task_comment.task_id == first_user_workspace_second_task.id
    assert task_comment.author_id == first_user.id


def test_admin_create_comment(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    create_comment_response_data = create_comment_response.json()
    task_comment = test_session.get(TaskComment, create_comment_response_data["id"])

    assert task_comment.text == "test_owner_comment"
    assert task_comment.task_id == first_user_workspace_second_task.id
    assert task_comment.author_id == second_user.id


def test_task_creator_create_comment(
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

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    create_comment_response_data = create_comment_response.json()
    task_comment = test_session.get(TaskComment, create_comment_response_data["id"])

    assert task_comment.text == "test_owner_comment"
    assert task_comment.task_id == first_user_workspace_second_task.id
    assert task_comment.author_id == second_user.id


def test_task_assignee_create_comment(
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

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    create_comment_response_data = create_comment_response.json()
    task_comment = test_session.get(TaskComment, create_comment_response_data["id"])

    assert task_comment.text == "test_owner_comment"
    assert task_comment.task_id == first_user_workspace_second_task.id
    assert task_comment.author_id == second_user.id


def test_task_unrelated_member_create_comment(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_403_FORBIDDEN

    create_comment_response_data = create_comment_response.json()
    assert create_comment_response_data["detail"] == "You can't comment this task"

    task_comments_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == first_user_workspace_second_task.id,
    )
    task_comment = test_session.execute(task_comments_stmt).scalars().one_or_none()

    assert task_comment is None


def test_task_no_member_create_comment(
    test_session,
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_second_task,
):
    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_404_NOT_FOUND

    create_comment_response_data = create_comment_response.json()
    assert create_comment_response_data["detail"] == "Workspace not found"

    task_comments_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == first_user_workspace_second_task.id,
    )
    task_comment = test_session.execute(task_comments_stmt).scalars().one_or_none()

    assert task_comment is None


def test_task_another_workspace_create_comment(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    second_user_workspace_first_task,
    add_workspace_member
):
    add_workspace_member(first_user_workspace, second_user)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_404_NOT_FOUND

    create_comment_response_data = create_comment_response.json()
    assert create_comment_response_data["detail"] == "Task not found"

    task_comments_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == second_user_workspace_first_task.id,
    )
    task_comment = test_session.execute(task_comments_stmt).scalars().one_or_none()

    assert task_comment is None


def test_missing_task_create_comment(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/99999999/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_first_user,
    )

    assert create_comment_response.status_code == status.HTTP_404_NOT_FOUND

    create_comment_response_data = create_comment_response.json()
    assert create_comment_response_data["detail"] == "Task not found"

def test_empty_text_comment_create(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": ""},
        headers=authorize_first_user,
    )

    assert create_comment_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    task_comments_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == first_user_workspace_first_task.id,
    )
    task_comment = test_session.execute(task_comments_stmt).scalars().one_or_none()

    assert task_comment is None


def test_len_text_more_one_thousand_comment_create(
    test_session,
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "a" * 1001},
        headers=authorize_first_user,
    )

    assert create_comment_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    task_comments_stmt = select(
        TaskComment,
    ).where(
        TaskComment.task_id == first_user_workspace_first_task.id,
    )
    task_comment = test_session.execute(task_comments_stmt).scalars().one_or_none()

    assert task_comment is None


def test_member_get_list_comments_workspace_tasks(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id in task_comments_ids


def test_member_get_list_current_task_comment(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    first_user_first_workspace_second_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id in task_comments_ids
    assert first_user_first_workspace_second_task_first_comment.id not in task_comments_ids


def test_get_exclude_comments_from_another_workspace(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    second_user_first_workspace_first_task_first_comment,
):
    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        headers=authorize_first_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id in task_comments_ids
    assert second_user_first_workspace_first_task_first_comment.id not in task_comments_ids


def test_no_member_get_list_task_comment(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
):

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_404_NOT_FOUND


def test_missing_task_get_list_comment(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
):
    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/9999999/comments/",
        headers=authorize_first_user,
    )

    assert get_comments_response.status_code == status.HTTP_404_NOT_FOUND


def test_limit_get_list_comment_tasks(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    assert (first_user_first_workspace_first_task_first_comment.id <
            first_user_first_workspace_first_task_second_comment.id)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/?limit=1",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id not in task_comments_ids


def test_offset_get_list_comment_tasks(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    assert (first_user_first_workspace_first_task_first_comment.id <
            first_user_first_workspace_first_task_second_comment.id)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/?offset=1",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id not in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id in task_comments_ids


def test_author_filter_get_list_comment_tasks(
    test_session,
    test_db_client,
    first_user,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_first_workspace_first_task_second_comment.author_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_first_workspace_first_task_second_comment)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/?"
        f"comment_author={first_user.id}",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK

    get_comments_response_data = get_comments_response.json()

    task_comments_ids = {
        task["id"]
        for task in get_comments_response_data
    }

    assert first_user_first_workspace_first_task_first_comment.id in task_comments_ids
    assert first_user_first_workspace_first_task_second_comment.id not in task_comments_ids


def test_author_no_matching_filter_get_list_comment_tasks(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    first_user_first_workspace_first_task_second_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/?"
        f"comment_author={second_user.id}",
        headers=authorize_second_user,
    )

    assert get_comments_response.status_code == status.HTTP_200_OK
    assert get_comments_response.json() == []


def test_member_get_task_comment(
    test_db_client,
    first_user_workspace,
    second_user,
    authorize_second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert get_comment_response.status_code == status.HTTP_200_OK

    get_comment_response_data = get_comment_response.json()

    assert get_comment_response_data["id"] == first_user_first_workspace_first_task_first_comment.id
    assert get_comment_response_data["text"] == first_user_first_workspace_first_task_first_comment.text


def test_no_member_get_task_comment(
        test_db_client,
        first_user_workspace,
        authorize_second_user,
        first_user_workspace_first_task,
        first_user_first_workspace_first_task_first_comment,
):

    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comment_response.json()["detail"] == "Workspace not found"


def test_get_task_comment_from_another_task(
    test_db_client,
    first_user_workspace,
    authorize_first_user,
    first_user_workspace_second_task,
    first_user_first_workspace_first_task_first_comment,
):
    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_first_user,
    )

    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comment_response.json()["detail"] == "Task comment not found"


def test_get_task_comment_from_another_workspace(
    test_db_client,
    second_user_workspace,
    authorize_second_user,
    second_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{second_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )
    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comment_response.json()["detail"] == "Task comment not found"


def test_get_task_comment_missing_comment(
    test_db_client,
    first_user_workspace,
    authorize_first_user,
    first_user_workspace_first_task,
):
    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/9999999/",
        headers=authorize_first_user,
    )
    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comment_response.json()["detail"] == "Task comment not found"


def test_get_task_comment_missing_task(
    test_db_client,
    first_user_workspace,
    authorize_first_user,
    first_user_first_workspace_first_task_first_comment,
):
    get_comment_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/999999/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_first_user,
    )
    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comment_response.json()["detail"] == "Task not found"


def test_owner_can_update_comment(
        test_session,
        test_db_client,
        second_user,
        authorize_first_user,
        authorize_second_user,
        first_user_workspace,
        first_user_workspace_first_task,
        add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    task_comment = test_session.get(TaskComment, create_comment_response.json()["id"])
    old_text = task_comment.text

    update_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{task_comment.id}/",
        json={"text": "update_owner_test_comment"},
        headers=authorize_first_user,
    )

    assert update_comment_response.status_code == status.HTTP_200_OK

    assert task_comment.text != old_text
    assert task_comment.text == "update_owner_test_comment"


def test_admin_can_update_comment(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    old_text = first_user_first_workspace_first_task_first_comment.text

    update_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_admin_test_comment"},
        headers=authorize_second_user,
    )

    assert update_comment_response.status_code == status.HTTP_200_OK
    assert first_user_first_workspace_first_task_first_comment.text != old_text
    assert first_user_first_workspace_first_task_first_comment.text == "update_admin_test_comment"


def test_author_update_comment(
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

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    task_comment = test_session.get(TaskComment, create_comment_response.json()["id"])
    old_text = task_comment.text

    update_author_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{task_comment.id}/",
        json={"text": "update_author_test_comment"},
        headers=authorize_second_user,
    )

    assert update_author_comment_response.status_code == status.HTTP_200_OK
    assert task_comment.text != old_text
    assert task_comment.text == "update_author_test_comment"

def test_member_no_update_another_user_task_comment(
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    old_text = first_user_first_workspace_first_task_first_comment.text
    update_member_another_user_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_member_test_comment"},
        headers=authorize_second_user,
    )

    assert update_member_another_user_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_creator_no_update_another_comment(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    old_text = first_user_first_workspace_first_task_first_comment.text

    update_creator_another_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_creator_test_comment"},
        headers=authorize_second_user,
    )

    assert update_creator_another_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_assignee_no_update_another_comment(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)
    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    old_text = first_user_first_workspace_first_task_first_comment.text

    update_assignee_another_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_assignee_test_comment"},
        headers=authorize_second_user,
    )

    assert update_assignee_another_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_no_member_update_comment(
    test_db_client,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    old_text = first_user_first_workspace_first_task_first_comment.text

    update_no_member_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_no_member_test_comment"},
        headers=authorize_second_user,
    )

    assert update_no_member_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_update_comment_in_another_task(
    test_session,
    test_db_client,
    second_user,
    authorize_second_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_workspace_second_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
):
    add_workspace_member(first_user_workspace, second_user)

    old_text = first_user_first_workspace_first_task_first_comment.text

    update_another_task_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_second_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_no_member_test_comment"},
        headers=authorize_second_user,
    )

    assert update_another_task_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert first_user_first_workspace_first_task_first_comment.text == old_text
    assert update_another_task_comment_response.json()["detail"] == "Task comment not found"


def test_update_comment_in_another_workspace(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    second_user_first_workspace_first_task_first_comment,
):
    old_text = second_user_first_workspace_first_task_first_comment.text
    update_another_workspace_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{second_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "update_no_member_test_comment"},
        headers=authorize_first_user,
    )

    assert update_another_workspace_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert second_user_first_workspace_first_task_first_comment.text == old_text


def test_update_missing_task_comment(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
):
    update_missing_task_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/9999999/",
        json={"text": "update_no_member_test_comment"},
        headers=authorize_first_user,
    )

    assert update_missing_task_response.status_code == status.HTTP_404_NOT_FOUND
    assert update_missing_task_response.json()["detail"] == "Task comment not found"

def test_update_empty_body_task_comment(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    old_text = first_user_first_workspace_first_task_first_comment.text
    update_empty_body_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={},
        headers=authorize_first_user,
    )

    assert update_empty_body_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_update_empty_text_task_comment(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    old_text = first_user_first_workspace_first_task_first_comment.text
    update_empty_text_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": ""},
        headers=authorize_first_user,
    )

    assert update_empty_text_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_update_text_more_high_border_task_comment(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
):
    old_text = first_user_first_workspace_first_task_first_comment.text
    update_more_text_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        json={"text": "a" * 1001},
        headers=authorize_first_user,
    )

    assert update_more_text_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert first_user_first_workspace_first_task_first_comment.text == old_text


def test_owner_delete_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    add_workspace_member,
    authorize_second_user,
    authorize_first_user,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    task_comment = test_session.get(TaskComment, create_comment_response.json()["id"])

    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{task_comment.id}/",
        headers=authorize_first_user,
    )

    assert delete_comment_response.status_code == status.HTTP_204_NO_CONTENT
    assert test_session.get(TaskComment, task_comment.id) is None


def test_admin_delete_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user, "admin")

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_204_NO_CONTENT
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is None


def test_author_delete_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    first_user,
    second_user,
    first_user_workspace_first_task,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    first_user_workspace_first_task.assignee_id = first_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)
    task_comment = test_session.get(TaskComment, create_comment_response.json()["id"])

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{task_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_204_NO_CONTENT
    assert test_session.get(TaskComment, task_comment.id) is None


def test_author_delete_another_author_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    create_comment_response = test_db_client.post(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/comments/",
        json={"text": "test_owner_comment"},
        headers=authorize_second_user,
    )

    assert create_comment_response.status_code == status.HTTP_201_CREATED

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is not None


def test_member_delete_another_author_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user)

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is not None


def test_task_creator_delete_another_author_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.created_by_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is not None


def test_task_assignee_delete_another_author_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    second_user,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    add_workspace_member,
    authorize_second_user,
):
    add_workspace_member(first_user_workspace, second_user)

    first_user_workspace_first_task.assignee_id = second_user.id
    test_session.commit()
    test_session.refresh(first_user_workspace_first_task)

    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_403_FORBIDDEN
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is not None


def test_workspace_no_member_delete_another_author_comment(
    test_session,
    test_db_client,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_first_task_first_comment,
    authorize_second_user,
):
    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_second_user,
    )

    assert delete_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert test_session.get(TaskComment, first_user_first_workspace_first_task_first_comment.id) is not None

def test_delete_comment_from_another_task(
    test_session,
    test_db_client,
    first_user_workspace,
    first_user_workspace_first_task,
    first_user_first_workspace_second_task_first_comment,
    authorize_first_user,
):
    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_second_task_first_comment.id}/",
        headers=authorize_first_user,
    )
    assert delete_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert test_session.get(TaskComment, first_user_first_workspace_second_task_first_comment.id) is not None


def test_delete_comment_from_another_workspace(
    test_session,
    test_db_client,
    second_user_workspace,
    second_user_workspace_first_task,
    first_user_first_workspace_second_task_first_comment,
    authorize_second_user,
):
    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{second_user_workspace.id}/tasks/{second_user_workspace_first_task.id}/"
        f"comments/{first_user_first_workspace_second_task_first_comment.id}/",
        headers=authorize_second_user,
    )
    assert delete_comment_response.status_code == status.HTTP_404_NOT_FOUND
    assert test_session.get(TaskComment, first_user_first_workspace_second_task_first_comment.id) is not None


def test_delete_task_comment_with_missing_comment_id(
    test_session,
    test_db_client,
    first_user_workspace,
    first_user_workspace_first_task,
    authorize_first_user,
):
    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/{first_user_workspace_first_task.id}/"
        f"comments/99999/",
        headers=authorize_first_user,
    )
    assert delete_comment_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_comments_for_task_from_another_workspace_gets_404(
    test_db_client,
    authorize_first_user,
    first_user_workspace,
    second_user_workspace_first_task,
):
    get_comments_response = test_db_client.get(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/"
        f"{second_user_workspace_first_task.id}/comments/",
        headers=authorize_first_user,
    )

    assert get_comments_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_comments_response.json()["detail"] == "Task not found"


def test_update_comment_missing_task_gets_404(
        test_db_client,
        authorize_first_user,
        first_user_workspace,
        second_user_first_workspace_first_task_first_comment,
):
    get_comment_response = test_db_client.patch(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/999999/"
        f"comments/{second_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_first_user,
        json={"text": "test_owner_comment"},
    )
    assert get_comment_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_comment_missing_task_gets_404(
        test_db_client,
        authorize_first_user,
        first_user_workspace,
        second_user_first_workspace_first_task_first_comment,
):
    delete_comment_response = test_db_client.delete(
        f"/api/v1/workspaces/{first_user_workspace.id}/tasks/999999/"
        f"comments/{second_user_first_workspace_first_task_first_comment.id}/",
        headers=authorize_first_user,
    )
    assert delete_comment_response.status_code == status.HTTP_404_NOT_FOUND
