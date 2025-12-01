"""File-based storage backend for Learning Path Agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

import aiofiles
from pydantic import BaseModel

from app.storage.schemas import (
    AssessmentResult,
    CompletedCourse,
    LearnerProfile,
    LearningPreferences,
    SkillHistory,
)

T = TypeVar("T", bound=BaseModel)


class FileBackend:
    """File-based storage backend with support for JSON and Markdown files."""

    def __init__(
        self,
        memories_dir: Path = Path("./data/memories"),
        sessions_dir: Path = Path("./data/sessions"),
    ):
        self.memories_dir = Path(memories_dir)
        self.sessions_dir = Path(sessions_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.memories_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, path: str) -> Path:
        """Convert virtual path to actual file path."""
        if path.startswith("/memories/"):
            return self.memories_dir / path.replace("/memories/", "")
        elif path.startswith("/current_session/") or path.startswith("/sessions/"):
            clean_path = path.replace("/current_session/", "").replace("/sessions/", "")
            return self.sessions_dir / clean_path
        else:
            # Default to sessions directory
            return self.sessions_dir / path.lstrip("/")

    async def ls(self, path: str = "/") -> list[str]:
        """List files in a directory."""
        if path == "/" or path == "":
            return ["/memories/", "/current_session/"]

        actual_path = self._get_path(path)
        if not actual_path.exists():
            return []

        files = []
        for item in actual_path.iterdir():
            if item.is_dir():
                files.append(f"{item.name}/")
            else:
                files.append(item.name)
        return sorted(files)

    async def read_file(self, path: str) -> Optional[str]:
        """Read file contents."""
        actual_path = self._get_path(path)
        if not actual_path.exists():
            return None

        async with aiofiles.open(actual_path, "r", encoding="utf-8") as f:
            return await f.read()

    async def write_file(self, path: str, content: str) -> bool:
        """Write content to a file."""
        actual_path = self._get_path(path)
        actual_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(actual_path, "w", encoding="utf-8") as f:
            await f.write(content)
        return True

    async def edit_file(self, path: str, old_content: str, new_content: str) -> bool:
        """Edit file by replacing old content with new content."""
        current = await self.read_file(path)
        if current is None:
            return False

        if old_content not in current:
            return False

        updated = current.replace(old_content, new_content)
        return await self.write_file(path, updated)

    async def delete_file(self, path: str) -> bool:
        """Delete a file."""
        actual_path = self._get_path(path)
        if not actual_path.exists():
            return False

        actual_path.unlink()
        return True

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        actual_path = self._get_path(path)
        return actual_path.exists()

    # JSON-specific methods for structured data

    async def read_json(self, path: str, model: Type[T]) -> Optional[T]:
        """Read and parse JSON file into a Pydantic model."""
        content = await self.read_file(path)
        if content is None:
            return None

        try:
            data = json.loads(content)
            return model.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None

    async def write_json(self, path: str, data: BaseModel) -> bool:
        """Write Pydantic model to JSON file."""
        content = data.model_dump_json(indent=2)
        return await self.write_file(path, content)

    # Convenience methods for specific data types

    async def get_profile(self, user_id: str) -> Optional[LearnerProfile]:
        """Get learner profile."""
        return await self.read_json(f"/memories/{user_id}/profile.json", LearnerProfile)

    async def save_profile(self, profile: LearnerProfile) -> bool:
        """Save learner profile."""
        profile.updated_at = datetime.now()
        return await self.write_json(
            f"/memories/{profile.user_id}/profile.json", profile
        )

    async def get_preferences(self, user_id: str) -> Optional[LearningPreferences]:
        """Get learning preferences."""
        return await self.read_json(
            f"/memories/{user_id}/learning_preferences.json", LearningPreferences
        )

    async def save_preferences(self, preferences: LearningPreferences) -> bool:
        """Save learning preferences."""
        return await self.write_json(
            f"/memories/{preferences.user_id}/learning_preferences.json", preferences
        )

    async def get_assessment(self, session_id: str) -> Optional[AssessmentResult]:
        """Get assessment result by session ID."""
        return await self.read_json(
            f"/sessions/{session_id}/assessment.json", AssessmentResult
        )

    async def save_assessment(self, assessment: AssessmentResult) -> bool:
        """Save assessment result."""
        return await self.write_json(
            f"/sessions/{assessment.session_id}/assessment.json", assessment
        )

    async def get_skill_history(self, user_id: str) -> list[SkillHistory]:
        """Get skill history for a user."""
        content = await self.read_file(f"/memories/{user_id}/skill_history.json")
        if content is None:
            return []

        try:
            data = json.loads(content)
            return [SkillHistory.model_validate(item) for item in data]
        except (json.JSONDecodeError, ValueError):
            return []

    async def append_skill_history(self, user_id: str, history: SkillHistory) -> bool:
        """Append to skill history."""
        existing = await self.get_skill_history(user_id)
        existing.append(history)

        content = json.dumps(
            [h.model_dump(mode="json") for h in existing], indent=2, ensure_ascii=False
        )
        return await self.write_file(f"/memories/{user_id}/skill_history.json", content)

    async def get_completed_courses(self, user_id: str) -> list[CompletedCourse]:
        """Get completed courses for a user."""
        content = await self.read_file(f"/memories/{user_id}/completed_courses.json")
        if content is None:
            return []

        try:
            data = json.loads(content)
            return [CompletedCourse.model_validate(item) for item in data]
        except (json.JSONDecodeError, ValueError):
            return []

    async def add_completed_course(self, user_id: str, course: CompletedCourse) -> bool:
        """Add a completed course."""
        existing = await self.get_completed_courses(user_id)
        existing.append(course)

        content = json.dumps(
            [c.model_dump(mode="json") for c in existing], indent=2, ensure_ascii=False
        )
        return await self.write_file(
            f"/memories/{user_id}/completed_courses.json", content
        )

    async def write_diagnosis_markdown(
        self, session_id: str, phase: int, content: str
    ) -> bool:
        """Write diagnosis results as markdown."""
        return await self.write_file(
            f"/sessions/{session_id}/phase_{phase}_results.md", content
        )

    async def get_assessment_history(self, user_id: str) -> list[dict]:
        """Get assessment history for a user."""
        content = await self.read_file(f"/memories/{user_id}/assessment_history.json")
        if content is None:
            return []

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    async def append_assessment_history(
        self, user_id: str, assessment_summary: dict
    ) -> bool:
        """Append to assessment history."""
        existing = await self.get_assessment_history(user_id)
        existing.append(assessment_summary)

        content = json.dumps(existing, indent=2, ensure_ascii=False)
        return await self.write_file(
            f"/memories/{user_id}/assessment_history.json", content
        )
