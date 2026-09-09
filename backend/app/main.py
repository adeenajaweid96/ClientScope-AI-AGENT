"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import routes_upload, routes_projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("ClientScope AI starting...")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"File storage: {settings.FILE_STORAGE_PATH}")

    yield

    # Shutdown
    print("ClientScope AI shutting down...")


app = FastAPI(
    title="ClientScope AI",
    description="Turns messy client material into structured project specifications",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_upload.router)
app.include_router(routes_projects.router)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "clientscope-ai",
        "version": "0.1.0"
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "ClientScope AI API",
        "docs": "/docs",
        "health": "/health"
    }
