"""FastAPI application entrypoint."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import lesson
from app.core import config
from app.core.logging import setup_logging

# Initialize logging as early as possible
setup_logging()

app = FastAPI(
    title="uLearn API",
    version="0.6.0",
    description="Backend API for the uLearn micro-learning platform",
)

# ---------------------------
# CORS configuration
# ---------------------------
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Health check
# ---------------------------
@app.get("/health", tags=["health"])
async def health_check():
    """
    Lightweight health endpoint.

    - No external dependencies
    - Safe for Render health checks
    - Exposes runtime execution mode
    """
    return {
        "status": "healthy",
        **config.runtime_mode(),
    }

# ---------------------------
# API routes
# ---------------------------
app.include_router(lesson.router)
