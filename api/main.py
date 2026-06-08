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
from .middleware.rate_limiter import RateLimitMiddleware
from .middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
)
from .routes import auth, br, proposals, matching, feedback, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BR Matching System...")
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

# Middleware (order matters — outermost first)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
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

# Routers
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(br.router, prefix=PREFIX)
app.include_router(proposals.router, prefix=PREFIX)
app.include_router(matching.router, prefix=PREFIX)
app.include_router(feedback.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)


@app.get("/health")
async def health():
    try:
        import torch
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
    except Exception:
        gpu = "unknown"
    return {"status": "healthy", "version": settings.APP_VERSION, "gpu": gpu}


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}
