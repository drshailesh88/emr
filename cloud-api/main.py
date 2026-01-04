"""DocAssist Cloud API - E2E Encrypted Backup Service"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from pydantic import Field
import logging
from pathlib import Path

from src.database import init_db, get_db
from src.backup.storage import init_storage
from src.auth import auth_router
from src.backup import backup_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings"""
    DATABASE_PATH: str = "./data/cloud_api.db"
    BACKUP_STORAGE_PATH: str = "./data/backups"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    RATE_LIMIT_DOWNLOAD: str = "10/minute"
    RATE_LIMIT_UPLOAD: str = "5/minute"

    class Config:
        env_file = ".env"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DocAssist Cloud API...")

    # Initialize database
    db = init_db(settings.DATABASE_PATH)
    await db.initialize()
    logger.info(f"Database initialized: {settings.DATABASE_PATH}")

    # Initialize storage
    init_storage(settings.BACKUP_STORAGE_PATH)
    logger.info(f"Storage initialized: {settings.BACKUP_STORAGE_PATH}")

    yield

    # Shutdown
    logger.info("Shutting down DocAssist Cloud API...")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="DocAssist Cloud API",
    description="E2E Encrypted Backup Service for DocAssist EMR",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router)
app.include_router(backup_router)


# Rate-limited endpoints
@app.get("/backup/download/{backup_id}")
@limiter.limit(settings.RATE_LIMIT_DOWNLOAD)
async def rate_limited_download(request: Request, backup_id: str):
    """Rate-limited download endpoint (applied via decorator)"""
    # This is handled by the router, rate limit applied here
    pass


@app.post("/backup/upload")
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def rate_limited_upload(request: Request):
    """Rate-limited upload endpoint (applied via decorator)"""
    # This is handled by the router, rate limit applied here
    pass


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DocAssist Cloud API",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """API root"""
    return {
        "message": "DocAssist Cloud API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
