"""FastAPI application entry point for Learning Path Agent."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import diagnosis, profile
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    settings.ensure_directories()
    print(f"Starting Learning Path Agent in {settings.app_env} mode...")
    yield
    # Shutdown
    print("Shutting down Learning Path Agent...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Learning Path Customization Agent",
        description="AI-powered learning path customization service using Deep Agent",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(diagnosis.router, prefix="/diagnosis", tags=["Diagnosis"])
    app.include_router(profile.router, prefix="/profile", tags=["Profile"])

    @app.get("/", tags=["Health"])
    async def root() -> dict:
        """Root endpoint for health check."""
        return {
            "status": "healthy",
            "service": "Learning Path Customization Agent",
            "version": "1.0.0",
        }

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
