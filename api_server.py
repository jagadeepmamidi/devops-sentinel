"""
Thin runner for the canonical DevOps Sentinel API app.
"""

from __future__ import annotations

import os

import uvicorn

from sentinel.api.app import app


if __name__ == "__main__":
    uvicorn.run(
        "sentinel.api.app:app",
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", os.environ.get("PORT", "8000"))),
        reload=os.environ.get("API_RELOAD", "").lower() in {"1", "true", "yes"},
    )
