"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.storage.file_backend import FileBackend


def get_file_backend(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileBackend:
    """Get file backend instance."""
    return FileBackend(
        memories_dir=settings.memories_dir,
        sessions_dir=settings.sessions_dir,
    )


# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
FileBackendDep = Annotated[FileBackend, Depends(get_file_backend)]
