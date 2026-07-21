from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/")
def get_project_name() -> dict[str, str]:
    return {
        "message": settings.PROJECT_NAME,
    }