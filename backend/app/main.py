import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api import api_router

# Optional Prometheus metrics
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Evidence-backed AI-powered GitHub repository auditing platform combining static analysis, AST security scanning, RAG, and agentic tool-calling.",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": "healthy"}


if PROM_AVAILABLE:
    @app.get("/metrics")
    async def metrics():
        data = generate_latest()
        from fastapi.responses import Response
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
