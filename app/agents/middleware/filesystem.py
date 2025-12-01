"""Filesystem Middleware for managing learner profiles and session data."""

from typing import Optional, Any
import json

from app.storage.file_backend import FileBackend
from app.storage.schemas import (
    LearnerProfile,
    LearningPreferences,
    AssessmentResult,
    SkillHistory,
    CompletedCourse,
)


class FilesystemMiddleware:
    """Middleware for filesystem operations with short-term and long-term storage."""

    def __init__(self, backend: FileBackend):
        self.backend = backend

    def get_system_prompt_addition(self) -> str:
        """Get system prompt addition for filesystem operations."""
        return """
## ファイルシステムアクセス

以下のツールを使用してファイルシステムにアクセスできます：

### 短期ファイル（現在のセッション、一時的）
- `/current_session/diagnosis_results.md`: 現在の診断中間結果
- `/current_session/questions.md`: 質問履歴
- `/current_session/answers.md`: 回答と推論

### 長期ファイル（永続化、`/memories/` プレフィックス）
- `/memories/{user_id}/profile.json`: エンジニアの基本情報・目標
- `/memories/{user_id}/skill_history.json`: スキルレベルの履歴推移
- `/memories/{user_id}/completed_courses.json`: 完了した学習コース
- `/memories/{user_id}/learning_preferences.json`: 学習スタイル・得意分野
- `/memories/{user_id}/assessment_history.json`: 過去の診断結果

### 使用方法
1. `ls` - ファイル一覧を確認
2. `read_file` - 過去の学習履歴を読み込み
3. `write_file` - 新しい発見を保存
4. `edit_file` - 進行中の診断結果を更新

推奨を提供する際は、必ず過去の学習履歴を参照してください。
"""

    async def ls(self, path: str = "/") -> dict:
        """
        List files in a directory.

        Args:
            path: Directory path to list

        Returns:
            Dictionary with files list and metadata
        """
        files = await self.backend.ls(path)
        return {
            "path": path,
            "files": files,
            "count": len(files),
        }

    async def read_file(self, path: str) -> dict:
        """
        Read file contents.

        Args:
            path: File path to read

        Returns:
            Dictionary with file contents or error
        """
        content = await self.backend.read_file(path)
        if content is None:
            return {
                "success": False,
                "error": f"File not found: {path}",
                "path": path,
            }

        return {
            "success": True,
            "path": path,
            "content": content,
        }

    async def write_file(self, path: str, content: str) -> dict:
        """
        Write content to a file.

        Args:
            path: File path to write
            content: Content to write

        Returns:
            Dictionary with success status
        """
        success = await self.backend.write_file(path, content)
        return {
            "success": success,
            "path": path,
            "message": f"File written successfully: {path}" if success else f"Failed to write: {path}",
        }

    async def edit_file(self, path: str, old_content: str, new_content: str) -> dict:
        """
        Edit file by replacing content.

        Args:
            path: File path to edit
            old_content: Content to replace
            new_content: New content

        Returns:
            Dictionary with success status
        """
        success = await self.backend.edit_file(path, old_content, new_content)
        return {
            "success": success,
            "path": path,
            "message": f"File edited successfully: {path}" if success else f"Failed to edit: {path}",
        }

    # High-level convenience methods

    async def get_learner_profile(self, user_id: str) -> Optional[LearnerProfile]:
        """Get learner profile."""
        return await self.backend.get_profile(user_id)

    async def save_learner_profile(self, profile: LearnerProfile) -> bool:
        """Save learner profile."""
        return await self.backend.save_profile(profile)

    async def get_learning_preferences(self, user_id: str) -> Optional[LearningPreferences]:
        """Get learning preferences."""
        return await self.backend.get_preferences(user_id)

    async def save_learning_preferences(self, preferences: LearningPreferences) -> bool:
        """Save learning preferences."""
        return await self.backend.save_preferences(preferences)

    async def get_assessment_result(self, session_id: str) -> Optional[AssessmentResult]:
        """Get assessment result."""
        return await self.backend.get_assessment(session_id)

    async def save_assessment_result(self, assessment: AssessmentResult) -> bool:
        """Save assessment result."""
        return await self.backend.save_assessment(assessment)

    async def get_skill_history(self, user_id: str) -> list[SkillHistory]:
        """Get skill history."""
        return await self.backend.get_skill_history(user_id)

    async def add_skill_history(self, user_id: str, history: SkillHistory) -> bool:
        """Add skill history entry."""
        return await self.backend.append_skill_history(user_id, history)

    async def get_completed_courses(self, user_id: str) -> list[CompletedCourse]:
        """Get completed courses."""
        return await self.backend.get_completed_courses(user_id)

    async def add_completed_course(self, user_id: str, course: CompletedCourse) -> bool:
        """Add completed course."""
        return await self.backend.add_completed_course(user_id, course)

    async def get_assessment_history(self, user_id: str) -> list[dict]:
        """Get assessment history."""
        return await self.backend.get_assessment_history(user_id)

    async def add_assessment_history(self, user_id: str, summary: dict) -> bool:
        """Add assessment history entry."""
        return await self.backend.append_assessment_history(user_id, summary)

    async def save_diagnosis_markdown(
        self, session_id: str, phase: int, content: str
    ) -> bool:
        """Save diagnosis results as markdown."""
        return await self.backend.write_diagnosis_markdown(session_id, phase, content)

    async def load_user_context(self, user_id: str) -> dict:
        """
        Load complete user context for agent.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with all user-related data
        """
        profile = await self.get_learner_profile(user_id)
        preferences = await self.get_learning_preferences(user_id)
        skill_history = await self.get_skill_history(user_id)
        completed_courses = await self.get_completed_courses(user_id)
        assessment_history = await self.get_assessment_history(user_id)

        return {
            "user_id": user_id,
            "profile": profile.model_dump() if profile else None,
            "preferences": preferences.model_dump() if preferences else None,
            "skill_history": [h.model_dump() for h in skill_history],
            "completed_courses": [c.model_dump() for c in completed_courses],
            "assessment_history": assessment_history,
            "has_previous_data": bool(profile or assessment_history),
        }

    def format_user_context_for_prompt(self, context: dict) -> str:
        """
        Format user context for inclusion in prompt.

        Args:
            context: User context dictionary

        Returns:
            Formatted string for prompt
        """
        if not context.get("has_previous_data"):
            return "この学習者は初めての診断です。基本情報から収集してください。"

        lines = ["## 学習者の既存データ\n"]

        if context.get("profile"):
            profile = context["profile"]
            lines.append(f"### 基本プロフィール")
            lines.append(f"- 名前: {profile.get('name', '不明')}")
            lines.append(f"- 経験年数: {profile.get('years_of_experience', 0)}年")
            lines.append(f"- 目標: {profile.get('goal', '未設定')}")
            lines.append(f"- 週間学習時間: {profile.get('learning_hours_per_week', 0)}時間")
            lines.append("")

        if context.get("preferences"):
            prefs = context["preferences"]
            lines.append(f"### 学習スタイル")
            lines.append(f"- プロジェクトベース: {'はい' if prefs.get('project_based') else 'いいえ'}")
            lines.append(f"- 希望言語: {', '.join(prefs.get('preferred_languages', []))}")
            lines.append("")

        if context.get("skill_history"):
            latest = context["skill_history"][-1] if context["skill_history"] else None
            if latest:
                lines.append(f"### 最新スキルレベル")
                lines.append(f"- 全体レベル: {latest.get('overall_level', 0)}/10")
                lines.append("")

        if context.get("assessment_history"):
            lines.append(f"### 診断履歴")
            lines.append(f"- 過去の診断回数: {len(context['assessment_history'])}回")
            lines.append("")

        return "\n".join(lines)

