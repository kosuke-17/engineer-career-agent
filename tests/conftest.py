"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest  # pyright: ignore[reportMissingImports]
import pytest_asyncio  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app modules
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"


@pytest.fixture(scope="session")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def test_data_dirs(temp_data_dir: Path) -> dict[str, Path]:
    """Create test data directories."""
    memories_dir = temp_data_dir / "memories"
    sessions_dir = temp_data_dir / "sessions"
    memories_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return {
        "memories": memories_dir,
        "sessions": sessions_dir,
    }


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    from app.main import app  # pyright: ignore[reportMissingImports]

    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    from app.main import app  # pyright: ignore[reportMissingImports]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_user_id() -> str:
    """Return a sample user ID for testing."""
    return "test-user-123"


@pytest.fixture
def sample_session_id() -> str:
    """Return a sample session ID for testing."""
    return "test-session-456"


@pytest.fixture
def sample_profile_data() -> dict:
    """Return sample profile data for testing."""
    return {
        "name": "テストユーザー",
        "email": "test@example.com",
        "years_of_experience": 3,
        "current_role": "ソフトウェアエンジニア",
        "target_role": "シニアバックエンドエンジニア",
        "goal": "バックエンド開発スキルを向上させたい",
        "learning_hours_per_week": 15,
        "preferred_learning_style": "project_based",
        "preferred_languages": ["Python", "Go"],
    }
