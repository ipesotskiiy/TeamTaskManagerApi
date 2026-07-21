from typing import Final


TASK_UPDATE_EVENT_BY_FIELD: Final[dict[str, str]] = {
    "status": "status_changed",
    "priority": "priority_changed",
    "assignee_id": "assignee_changed",
    "title": "title_changed",
    "due_date": "due_date_changed",
}

COMMENT_CREATED_EVENT: Final[str] = "comment_created"
COMMENT_UPDATED_EVENT: Final[str] = "comment_updated"
COMMENT_DELETED_EVENT: Final[str] = "comment_deleted"
