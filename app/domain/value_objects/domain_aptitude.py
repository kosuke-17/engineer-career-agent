"""Domain aptitude value objects."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EngineeringDomain(str, Enum):
    """Engineering domain types."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    ML_ENGINEERING = "ml_engineering"
    MOBILE = "mobile"
    SYSTEMS = "systems"

    @property
    def display_name(self) -> str:
        """Get display name for the domain."""
        names = {
            EngineeringDomain.FRONTEND: "フロントエンド開発",
            EngineeringDomain.BACKEND: "バックエンド開発",
            EngineeringDomain.FULLSTACK: "フルスタック開発",
            EngineeringDomain.DEVOPS: "DevOps/インフラ",
            EngineeringDomain.ML_ENGINEERING: "機械学習エンジニアリング",
            EngineeringDomain.MOBILE: "モバイル開発",
            EngineeringDomain.SYSTEMS: "システムプログラミング",
        }
        return names.get(self, self.value)


@dataclass(frozen=True)
class DomainAptitude:
    """Value object representing aptitude for an engineering domain."""

    domain: EngineeringDomain
    score: float
    reasoning: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate score range."""
        if not 0 <= self.score <= 10:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")

    def is_recommended(self) -> bool:
        """Check if this domain is recommended (score >= 7)."""
        return self.score >= 7

    def is_suitable(self) -> bool:
        """Check if this domain is suitable (score >= 5)."""
        return self.score >= 5
