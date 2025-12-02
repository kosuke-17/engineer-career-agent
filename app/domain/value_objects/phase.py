"""Phase value objects."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PhaseStatus(str, Enum):
    """Status of a diagnosis phase."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Phase(str, Enum):
    """Diagnosis phase types."""

    FOUNDATION = "foundation"
    DOMAIN = "domain"
    TECHNICAL = "technical"
    ARCHITECTURE = "architecture"
    ROADMAP = "roadmap"

    @property
    def display_name(self) -> str:
        """Get display name for the phase."""
        names = {
            Phase.FOUNDATION: "基礎スキル診断",
            Phase.DOMAIN: "専攻領域選定",
            Phase.TECHNICAL: "詳細技術診断",
            Phase.ARCHITECTURE: "アーキテクチャ適性",
            Phase.ROADMAP: "学習ロードマップ生成",
        }
        return names.get(self, self.value)

    @property
    def description(self) -> str:
        """Get description for the phase."""
        descriptions = {
            Phase.FOUNDATION: "プログラミング基礎、アルゴリズム、データ構造を診断",
            Phase.DOMAIN: "フロントエンド/バックエンド/インフラなど適性を判定",
            Phase.TECHNICAL: "選定領域の具体的な技術スタック適性を評価",
            Phase.ARCHITECTURE: "システム設計・アーキテクチャ思考能力を診断",
            Phase.ROADMAP: "全ての診断結果から最適な学習パスを生成",
        }
        return descriptions.get(self, "")

    @property
    def order(self) -> int:
        """Get the order of the phase."""
        order_map = {
            Phase.FOUNDATION: 1,
            Phase.DOMAIN: 2,
            Phase.TECHNICAL: 3,
            Phase.ARCHITECTURE: 4,
            Phase.ROADMAP: 5,
        }
        return order_map.get(self, 0)

    def next_phase(self) -> Optional["Phase"]:
        """Get the next phase in sequence."""
        phases = list(Phase)
        current_idx = phases.index(self)
        if current_idx < len(phases) - 1:
            return phases[current_idx + 1]
        return None

    def is_final(self) -> bool:
        """Check if this is the final phase."""
        return self == Phase.ROADMAP

