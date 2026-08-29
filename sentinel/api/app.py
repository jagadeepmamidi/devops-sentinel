"""
Canonical FastAPI application for the monitoring MVP.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from sentinel.api.mvp_routes import router as monitoring_router
from sentinel.api.quick_health_check import router as quick_health_router
from sentinel.auth.auth_service import router as auth_router
from sentinel.setup.ai_setup import router as ai_setup_router
from sentinel.setup.supabase_setup import router as supabase_setup_router

from sentinel import __version__ as APP_VERSION

APP_NAME = "DevOps Sentinel API"
WEB_DIST_DIR = Path(__file__).resolve().parents[2] / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{APP_NAME}] Starting on port {os.environ.get('PORT', '8000')}")
    yield
    print(f"[{APP_NAME}] Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="CLI-first monitoring and incident response MVP",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    cors_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
    allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in {"1", "true", "yes"}
    if "*" in cors_origins and allow_credentials:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(quick_health_router)
    app.include_router(supabase_setup_router)
    app.include_router(ai_setup_router)
    app.include_router(monitoring_router)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": APP_VERSION, "timestamp": datetime.utcnow().isoformat()}

    @app.get("/api/status")
    async def status():
        return {
            "status": "healthy",
            "version": APP_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.get("/")
    async def root():
        index_path = WEB_DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse(
            {
                "name": APP_NAME,
                "version": APP_VERSION,
                "status": "running",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.get("/{full_path:path}")
    async def frontend(full_path: str):
        candidate = WEB_DIST_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)

        index_path = WEB_DIST_DIR / "index.html"
        if index_path.exists() and not full_path.startswith("api/"):
            return FileResponse(index_path)

        return JSONResponse({"detail": "Not Found"}, status_code=404)

    return app


app = create_app()
