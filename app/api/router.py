from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspace_router
from app.api.v1.tasks import router as task_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(workspace_router)
api_router.include_router(task_router, prefix="/workspaces/{workspace_id}")
