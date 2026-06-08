import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.exc import IntegrityError

from .config import settings
from .database import engine, Base
from .middleware.logging import RequestLoggingMiddleware
from .middleware.redis_rate_limiter import RedisRateLimitMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
)
from .routes import auth, br, proposals, matching, feedback, admin
from .routes import export, search, analytics, webhooks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BR Matching System v%s ...", settings.APP_VERSION)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    yield
    logger.info("Shutting down BR Matching System.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware stack (outermost → innermost)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RedisRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

# Phase 1
app.include_router(auth.router, prefix=PREFIX)
app.include_router(br.router, prefix=PREFIX)
app.include_router(proposals.router, prefix=PREFIX)
app.include_router(matching.router, prefix=PREFIX)
app.include_router(feedback.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)

# Phase 2
app.include_router(export.router, prefix=PREFIX)
app.include_router(search.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(webhooks.router, prefix=PREFIX)


# ── Task status endpoint ──────────────────────────────────────────────────────
@app.get("/api/v1/tasks/{task_id}", tags=["tasks"])
async def get_task_status(task_id: str):
    """Poll the status of a Celery background task."""
    from .tasks.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    response = {"task_id": task_id, "status": result.status}
    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = str(result.result)
    return response


@app.get("/health")
async def health():
    checks: dict = {"api": "ok"}
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
    try:
        import torch
        checks["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu_only"
    except ImportError:
        checks["gpu"] = "torch_not_installed"
    return {"status": "healthy", "version": settings.APP_VERSION, "checks": checks}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "phase": "2",
    }
