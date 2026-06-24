from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Team Task Manager API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./team_task_manager.db"


settings = Settings()