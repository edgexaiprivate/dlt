import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.models import Base  # registers all models


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title="MenuVision API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.ENVIRONMENT}


# Import routers — these will be filled in Phase 1 full build
try:
    from app.api.v1 import api_router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
except ImportError:
    pass  # Routers not yet created — health endpoint still works
