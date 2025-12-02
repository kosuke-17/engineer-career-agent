"""Application entry point - imports from DDD presentation layer."""

# Re-export from the DDD presentation layer for backward compatibility
from app.presentation.main import app, create_app

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
