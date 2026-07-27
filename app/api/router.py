from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspace_router
from app.api.v1.tasks import router as task_router
from app.api.v1.task_comments import router as task_comment_router
from app.api.v1.task_activity import router as task_activity_router
from app.api.v1.workspace_member import router as workspace_member_router


TASK_DETAIL_PREFIX = "/workspaces/{workspace_id}/tasks/{task_id}"
WORKSPACE_DETAIL_PREFIX = "/workspaces/{workspace_id}"

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(workspace_router)
api_router.include_router(
    task_router,
    prefix=WORKSPACE_DETAIL_PREFIX
)
api_router.include_router(
    task_comment_router,
    prefix=TASK_DETAIL_PREFIX,
)
api_router.include_router(
    task_activity_router,
    prefix=TASK_DETAIL_PREFIX,
)
api_router.include_router(
    workspace_member_router,
    prefix=WORKSPACE_DETAIL_PREFIX,
)

