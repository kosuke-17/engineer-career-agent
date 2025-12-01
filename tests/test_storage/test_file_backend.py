"""Tests for file backend storage."""

import json
from pathlib import Path

import pytest
import pytest_asyncio

from app.storage.file_backend import FileBackend
from app.storage.schemas import (
    LearnerProfile,
    LearningPreferences,
    LearningStyle,
    SkillHistory,
    SkillScore,
    SkillLevel,
    CompletedCourse,
)


@pytest_asyncio.fixture
async def file_backend(test_data_dirs: dict[str, Path]) -> FileBackend:
    """Create a file backend instance for testing."""
    return FileBackend(
        memories_dir=test_data_dirs["memories"],
        sessions_dir=test_data_dirs["sessions"],
    )


class TestFileBackendBasicOperations:
    """Tests for basic file operations."""

    @pytest.mark.asyncio
    async def test_ls_root(self, file_backend: FileBackend):
        """Test listing root directory."""
        files = await file_backend.ls("/")
        assert "/memories/" in files
        assert "/current_session/" in files

    @pytest.mark.asyncio
    async def test_write_and_read_file(self, file_backend: FileBackend):
        """Test writing and reading a file."""
        path = "/sessions/test/test_file.txt"
        content = "Hello, World!"

        # Write file
        result = await file_backend.write_file(path, content)
        assert result is True

        # Read file
        read_content = await file_backend.read_file(path)
        assert read_content == content

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, file_backend: FileBackend):
        """Test reading a file that doesn't exist."""
        content = await file_backend.read_file("/nonexistent/file.txt")
        assert content is None

    @pytest.mark.asyncio
    async def test_file_exists(self, file_backend: FileBackend):
        """Test checking if a file exists."""
        path = "/sessions/test/exists.txt"

        # File doesn't exist initially
        assert await file_backend.file_exists(path) is False

        # Create file
        await file_backend.write_file(path, "content")

        # Now it exists
        assert await file_backend.file_exists(path) is True

    @pytest.mark.asyncio
    async def test_delete_file(self, file_backend: FileBackend):
        """Test deleting a file."""
        path = "/sessions/test/to_delete.txt"

        # Create and verify file exists
        await file_backend.write_file(path, "content")
        assert await file_backend.file_exists(path) is True

        # Delete file
        result = await file_backend.delete_file(path)
        assert result is True

        # Verify file is deleted
        assert await file_backend.file_exists(path) is False

    @pytest.mark.asyncio
    async def test_edit_file(self, file_backend: FileBackend):
        """Test editing a file."""
        path = "/sessions/test/to_edit.txt"
        original = "Hello, World!"
        await file_backend.write_file(path, original)

        # Edit file
        result = await file_backend.edit_file(path, "World", "Python")
        assert result is True

        # Verify content
        content = await file_backend.read_file(path)
        assert content == "Hello, Python!"


class TestFileBackendProfile:
    """Tests for profile-related operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_profile(self, file_backend: FileBackend):
        """Test saving and retrieving a learner profile."""
        profile = LearnerProfile(
            user_id="test-user-1",
            name="テストユーザー",
            years_of_experience=3,
            goal="バックエンド開発を学ぶ",
            learning_hours_per_week=10,
            preferred_learning_style=LearningStyle.PROJECT_BASED,
        )

        # Save profile
        result = await file_backend.save_profile(profile)
        assert result is True

        # Retrieve profile
        retrieved = await file_backend.get_profile("test-user-1")
        assert retrieved is not None
        assert retrieved.name == "テストユーザー"
        assert retrieved.years_of_experience == 3

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self, file_backend: FileBackend):
        """Test getting a profile that doesn't exist."""
        profile = await file_backend.get_profile("nonexistent-user")
        assert profile is None


class TestFileBackendPreferences:
    """Tests for learning preferences operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_preferences(self, file_backend: FileBackend):
        """Test saving and retrieving learning preferences."""
        preferences = LearningPreferences(
            user_id="test-user-2",
            project_based=True,
            community_learning=False,
            preferred_languages=["Python", "JavaScript"],
        )

        # Save preferences
        result = await file_backend.save_preferences(preferences)
        assert result is True

        # Retrieve preferences
        retrieved = await file_backend.get_preferences("test-user-2")
        assert retrieved is not None
        assert retrieved.project_based is True
        assert "Python" in retrieved.preferred_languages


class TestFileBackendSkillHistory:
    """Tests for skill history operations."""

    @pytest.mark.asyncio
    async def test_append_and_get_skill_history(self, file_backend: FileBackend):
        """Test appending and retrieving skill history."""
        user_id = "test-user-3"

        history1 = SkillHistory(
            overall_level=5.0,
            skills=[
                SkillScore(skill_name="Python", score=6.0, level=SkillLevel.INTERMEDIATE)
            ],
        )

        history2 = SkillHistory(
            overall_level=6.0,
            skills=[
                SkillScore(skill_name="Python", score=7.0, level=SkillLevel.ADVANCED)
            ],
        )

        # Append histories
        await file_backend.append_skill_history(user_id, history1)
        await file_backend.append_skill_history(user_id, history2)

        # Retrieve history
        histories = await file_backend.get_skill_history(user_id)
        assert len(histories) == 2
        assert histories[0].overall_level == 5.0
        assert histories[1].overall_level == 6.0


class TestFileBackendCourses:
    """Tests for completed courses operations."""

    @pytest.mark.asyncio
    async def test_add_and_get_completed_courses(self, file_backend: FileBackend):
        """Test adding and retrieving completed courses."""
        user_id = "test-user-4"

        course = CompletedCourse(
            course_id="python-101",
            course_name="Python入門",
            provider="Udemy",
            score=85.0,
            skills_gained=["Python基礎", "OOP"],
        )

        # Add course
        result = await file_backend.add_completed_course(user_id, course)
        assert result is True

        # Retrieve courses
        courses = await file_backend.get_completed_courses(user_id)
        assert len(courses) == 1
        assert courses[0].course_name == "Python入門"
        assert courses[0].score == 85.0


