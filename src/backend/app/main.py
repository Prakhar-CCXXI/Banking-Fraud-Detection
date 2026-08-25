from fastapi import FastAPI
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager
from backend.app.core.db import init_db


# 1. Add the asynccontextmanager decorator
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 2. Everything BEFORE yield runs on STARTUP
    print("Application is starting up...") 
    
    yield # 3. The yield statement is MANDATORY
    
    # 4. Everything AFTER yield runs on SHUTDOWN
    print("Application is shutting down...")

# 5. Pass the lifespan to the FastAPI instance

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/doc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.API_V1_STR)