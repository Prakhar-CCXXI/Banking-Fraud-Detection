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
    ACTIVATION_TOKEN_EXPIRATION_MINUTES: int = 2 if ENVIRONMENT == "local" else 5 

    API_BASE_URL : str = ""
    SUPPORT_EMAIL : str = ""
    JWT_SECRET_KEY : str = ""
    JWT_ALGORITHM : str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRATION_MINUTES : int = 30 if ENVIRONMENT == "local" else 15
    JWT_REFRESH_TOKEN_EXPIRATION_DAYS : int = 1

    #Custom Cookie Settings 
    COOKIE_SECURE: bool = False if ENVIRONMENT == "local" else True 
    # Ensures cookies are only transmitted over **encrypted HTTPS connections** in production/staging, while allowing unencrypted HTTP for local development
    COOKIE_ACCESS_NAME: str = "access_token" 
    # Sets the cookie key name that will store the short-lived **JWT access token**
    COOKIE_REFRESH_NAME: str = "refresh_token" 
    # Sets the cookie key name that will store the longer-lived **JWT refresh token**
    COOKIE_LOGGED_IN_NAME: str = "logged_in" 
    # Sets the cookie name used to signal **authentication state to the frontend UI** without exposing sensitive JWTs to JavaScript.
    COOKIE_HTTP_ONLY: bool = True 
    # Disables client-side JavaScript access to the cookies, protecting authentication tokens against Cross-Site Scripting (XSS) attacks.
    COOKIE_SAMESITE: str = "lax" 
    # Restricts cross-site cookie transmission to defend against Cross-Site Request Forgery (CSRF) while allowing standard top-level navigation.
    COOKIE_PATH: str = "/"
    # Makes the authentication cookies accessible across the **entire domain and all API sub-paths.


    SIGNING_KEY : str = ""
    # Defines the secret configuration key used to sign JWT access and refresh tokens to make them tamper-resistant

    # python -c import secrets; print(secrets.token_urlsafe(38)) 
    # • import secrets: Imports Python's built-in secrets module, which is explicitly designed for generating cryptographically secure random numbers and strings.
    # • token_urlsafe(38): Generates a random string containing 38 random bytes, which is then Base64-encoded to make it safe to use in URLs. Because Base64 expands the byte count by roughly 33%, the resulting string length is 51 characters.



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