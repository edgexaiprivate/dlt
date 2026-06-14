import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.db.session import engine
from app.db.redis import get_redis, close_redis
from app.database_models import Base  # noqa: F401 — ensures models are registered
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    print(f"🚀 MenuVision API starting ({settings.ENVIRONMENT})")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Warm up Redis connection
    await get_redis()
    print("✅ Redis connected")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_redis()
    await engine.dispose()
    print("👋 MenuVision API shut down")


app = FastAPI(
    title="MenuVision API",
    description="Dynamic food menu display system for restaurants",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title="MenuVision API",
#         version="1.0.0",
#         description="Dynamic food menu display system for restaurants",
#         routes=app.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "HTTPBearer": {
#             "type": "http",
#             "scheme": "bearer",
#             "description": "JWT Bearer token authentication"
#         }
#     }
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


# app.openapi = custom_openapi
# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files (uploaded images) ─────────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ─── API routes ──────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.ENVIRONMENT}
