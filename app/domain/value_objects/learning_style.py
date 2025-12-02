"""Learning style value object."""

from enum import Enum


class LearningStyle(str, Enum):
    """Learning style preferences."""

    PROJECT_BASED = "project_based"
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    COMMUNITY = "community"

    @property
    def display_name(self) -> str:
        """Get display name for the learning style."""
        names = {
            LearningStyle.PROJECT_BASED: "プロジェクトベース学習",
            LearningStyle.VIDEO: "動画学習",
            LearningStyle.TEXT: "テキスト/書籍学習",
            LearningStyle.INTERACTIVE: "インタラクティブ演習",
            LearningStyle.COMMUNITY: "コミュニティ学習",
        }
        return names.get(self, self.value)

