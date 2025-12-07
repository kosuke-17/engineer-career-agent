"""FastAPI application entry point with DDD architecture."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.presentation.api.routes.learning_roadmap_router import (
    router as learning_roadmap_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    settings.ensure_directories()
    print(f"Starting Learning Path Agent (DDD) in {settings.app_env} mode...")
    print(f"Using LLM provider: {settings.llm_provider.value}")
    yield
    print("Shutting down Learning Path Agent...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Learning Path Customization Agent",
        description="AI-powered learning path customization service using DDD architecture",
        version="2.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        learning_roadmap_router,
        prefix="/api/learning-roadmap",
        tags=["Learning Roadmap"],
    )

    # Health check endpoints
    @app.get("/", tags=["Health"])
    async def root() -> dict:
        """Root endpoint."""
        return {
            "status": "healthy",
            "service": "Learning Path Customization Agent",
            "version": "2.0.0",
            "architecture": "DDD",
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
        "app.presentation.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
