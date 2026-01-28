"""
DevOps Sentinel - API Server
============================

FastAPI server entry point
Run with: python api_server.py
"""

from contextlib import asynccontextmanager
from datetime import datetime
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn


# App config
APP_NAME = "DevOps Sentinel API"
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    print(f"[{APP_NAME}] Starting on port {os.environ.get('PORT', 8000)}")
    yield
    print(f"[{APP_NAME}] Shutting down")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered incident memory for SRE teams",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Import and include routers
try:
    from src.api.quick_health_check import router as health_check_router
    app.include_router(health_check_router)
except ImportError:
    pass

try:
    from src.api.gdpr_endpoints import router as gdpr_router
    app.include_router(gdpr_router)
except ImportError:
    pass

try:
    from src.api.waitlist import router as waitlist_router
    app.include_router(waitlist_router)
except ImportError:
    pass


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/status")
async def status():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "stats": {
            "services": 0,
            "incidents": 0,
            "uptime": 99.9
        }
    }


@app.get("/api/services")
async def list_services():
    return {"services": [], "total": 0}


@app.get("/api/incidents")
async def list_incidents(status: str = "active"):
    return {"incidents": [], "total": 0}


@app.get("/api/oncall/current")
async def get_oncall():
    return {"current": None, "upcoming": []}


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )
