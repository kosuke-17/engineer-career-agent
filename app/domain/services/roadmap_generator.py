"""Roadmap generation domain service."""

from typing import Any

from ..entities import (
    Learner,
    LearningRoadmap,
    QuarterPlan,
    Milestone,
    LearningResource,
)
from ..value_objects import EngineeringDomain


class RoadmapGeneratorService:
    """Domain service for roadmap generation operations."""

    @staticmethod
    def calculate_duration(
        learner: Learner,
        target_domain: EngineeringDomain,
    ) -> int:
        """Calculate recommended learning duration in months.

        Args:
            learner: The learner entity.
            target_domain: The target engineering domain.

        Returns:
            Recommended duration in months.
        """
        # Base duration
        base_months = 12

        # Adjust based on experience
        experience = learner.profile.experience_years or 0
        if experience >= 3:
            base_months -= 3
        elif experience >= 1:
            base_months -= 1

        # Adjust based on weekly hours
        weekly_hours = learner.profile.weekly_hours or 10
        if weekly_hours >= 20:
            base_months = int(base_months * 0.75)
        elif weekly_hours < 10:
            base_months = int(base_months * 1.25)

        # Ensure minimum duration
        return max(6, min(24, base_months))

    @staticmethod
    def create_basic_roadmap(
        learner: Learner,
        target_domain: EngineeringDomain,
        duration_months: int = 12,
    ) -> LearningRoadmap:
        """Create a basic roadmap structure.

        For detailed roadmap generation with AI, use the application layer.

        Args:
            learner: The learner entity.
            target_domain: The target engineering domain.
            duration_months: Duration in months.

        Returns:
            A LearningRoadmap entity with basic structure.
        """
        roadmap = LearningRoadmap.create(
            user_id=learner.id,
            target_domain=target_domain,
            target_role=learner.profile.target_role or target_domain.display_name,
            duration_months=duration_months,
        )

        # Create quarter plans based on domain
        quarter_themes = RoadmapGeneratorService._get_quarter_themes(target_domain)

        for i, theme in enumerate(quarter_themes, 1):
            quarter = QuarterPlan(
                quarter=i,
                theme=theme["theme"],
                goals=theme["goals"],
            )
            roadmap.add_quarter(quarter)

        return roadmap

    @staticmethod
    def _get_quarter_themes(domain: EngineeringDomain) -> list[dict[str, Any]]:
        """Get quarter themes for a domain."""
        themes = {
            EngineeringDomain.FRONTEND: [
                {
                    "theme": "Web基礎",
                    "goals": ["HTML/CSS習得", "JavaScript基礎", "レスポンシブデザイン"],
                },
                {
                    "theme": "モダンフレームワーク",
                    "goals": ["React/Vue習得", "状態管理", "コンポーネント設計"],
                },
                {
                    "theme": "高度な開発",
                    "goals": ["TypeScript", "テスト", "パフォーマンス最適化"],
                },
                {
                    "theme": "実践プロジェクト",
                    "goals": ["ポートフォリオ作成", "OSS貢献", "技術発信"],
                },
            ],
            EngineeringDomain.BACKEND: [
                {
                    "theme": "プログラミング基礎",
                    "goals": ["Python/Java習得", "データ構造", "アルゴリズム"],
                },
                {
                    "theme": "Web開発基礎",
                    "goals": ["REST API設計", "データベース", "認証・認可"],
                },
                {
                    "theme": "システム設計",
                    "goals": ["アーキテクチャパターン", "マイクロサービス", "キャッシュ戦略"],
                },
                {
                    "theme": "運用・スケーリング",
                    "goals": ["監視・ログ", "パフォーマンス", "セキュリティ"],
                },
            ],
            EngineeringDomain.DEVOPS: [
                {
                    "theme": "Linux/クラウド基礎",
                    "goals": ["Linux操作", "AWS/GCP基礎", "ネットワーク基礎"],
                },
                {
                    "theme": "コンテナ技術",
                    "goals": ["Docker", "Kubernetes基礎", "コンテナオーケストレーション"],
                },
                {
                    "theme": "CI/CD",
                    "goals": ["GitHub Actions", "自動テスト", "デプロイ自動化"],
                },
                {
                    "theme": "インフラ運用",
                    "goals": ["IaC(Terraform)", "監視・アラート", "セキュリティ"],
                },
            ],
        }

        return themes.get(
            domain,
            [
                {"theme": f"Q{i} 学習フェーズ", "goals": ["基礎習得", "応用学習", "実践"]}
                for i in range(1, 5)
            ],
        )

    @staticmethod
    def parse_roadmap_result(
        result: dict[str, Any],
        learner: Learner,
        target_domain: EngineeringDomain,
    ) -> LearningRoadmap:
        """Parse roadmap result from LLM into a LearningRoadmap entity.

        Args:
            result: Dictionary containing roadmap data from LLM.
            learner: The learner entity.
            target_domain: The target engineering domain.

        Returns:
            A LearningRoadmap entity.
        """
        roadmap = LearningRoadmap.create(
            user_id=learner.id,
            target_domain=target_domain,
            target_role=result.get("target_role", learner.profile.target_role),
            duration_months=result.get("duration_months", 12),
        )

        # Parse quarters
        for quarter_data in result.get("quarters", []):
            milestones = []
            for milestone_data in quarter_data.get("milestones", []):
                resources = []
                for resource_data in milestone_data.get("resources", []):
                    resources.append(
                        LearningResource(
                            title=resource_data.get("title", ""),
                            type=resource_data.get("type", "course"),
                            url=resource_data.get("url"),
                            estimated_hours=resource_data.get("estimated_hours"),
                        )
                    )

                milestones.append(
                    Milestone(
                        title=milestone_data.get("title", ""),
                        description=milestone_data.get("description", ""),
                        skills=milestone_data.get("skills", []),
                        resources=resources,
                        estimated_weeks=milestone_data.get("estimated_weeks", 4),
                    )
                )

            quarter = QuarterPlan(
                quarter=quarter_data.get("quarter", 1),
                theme=quarter_data.get("theme", ""),
                milestones=milestones,
                goals=quarter_data.get("goals", []),
            )
            roadmap.add_quarter(quarter)

        roadmap.prerequisites = result.get("prerequisites", [])
        roadmap.final_project = result.get("final_project")
        roadmap.notes = result.get("notes")

        return roadmap

