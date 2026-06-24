from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Team Task Manager API"
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()