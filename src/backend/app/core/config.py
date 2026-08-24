from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    model_config = SettingsConfigDict(
        env_file="../../.env.local",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = ""
    PROJECT_NAME: str = "Bank Fraud Detection - FastAPI"
    PROJECT_DESCRIPTION: str = "banking API built with FastAPI"
    SITE_NAME: str = ""
    DATABASE_URL: str = ""


settings = Settings()