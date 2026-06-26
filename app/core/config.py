from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Team Task Manager API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./team_task_manager.db"
    SECRET_KEY: str = "dev-secret-key-change-me-team-task-manager-api"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()