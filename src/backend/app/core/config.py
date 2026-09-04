import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".envs/.env.local"),
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bank Fraud Detection - FastAPI"
    PROJECT_DESCRIPTION: str = "banking API built with FastAPI"
    SITE_NAME: str = "NextGen Banking"

    POSTGRES_USER: str = "alphaogilo"
    POSTGRES_PASSWORD: str = "Pass12345"
    POSTGRES_DB: str = "bank"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = (
        "postgresql+asyncpg://alphaogilo:Pass12345@postgres:5432/bank"
    )

    MAIL_FROM: str = "noreply@gmail.com"
    MAIL_FROM_NAME: str = "Banking Project"
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    MAILPIT_UI_PORT: int = 8025

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    CELERY_FLOWER_USER: str = "admin"
    CELERY_FLOWER_PASSWORD: str = "Pass123456"


    OTP_EXPIRATION_MINUTES: int=2 if ENVIRONMENT == "local" else 5 
    LOGIN_ATTEMPTS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 2 if ENVIRONMENT == "local" else 5 

    @property
    def redis_db(self) -> int:
        return self.REDIS_DB

    @property
    def redis_host(self) -> str:
        return self.REDIS_HOST

    @property
    def redis_port(self) -> int:
        return self.REDIS_PORT

    @property
    def rabbitmq_host(self) -> str:
        return self.RABBITMQ_HOST

    @property
    def rabbitmq_port(self) -> int:
        return self.RABBITMQ_PORT


settings = Settings()