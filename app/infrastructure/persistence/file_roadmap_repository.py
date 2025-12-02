"""File-based roadmap repository implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.domain.entities import (
    LearningRoadmap,
    LearningResource,
    Milestone,
    QuarterPlan,
)
from app.domain.repositories import RoadmapRepository
from app.domain.value_objects import EngineeringDomain


class FileRoadmapRepository(RoadmapRepository):
    """File-based implementation of RoadmapRepository."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, roadmap_id: str) -> Path:
        """Get the file path for a roadmap."""
        # パストラバーサル対策
        safe_id = roadmap_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        path = (self.base_path / f"{safe_id}.json").resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid roadmap ID: path traversal detected")
        return path

    async def find_by_id(self, roadmap_id: str) -> Optional[LearningRoadmap]:
        """Find a roadmap by ID."""
        file_path = self._get_file_path(roadmap_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._dict_to_roadmap(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def find_by_user_id(self, user_id: str) -> list[LearningRoadmap]:
        """Find all roadmaps for a user."""
        roadmaps = []
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("user_id") == user_id:
                    roadmap = self._dict_to_roadmap(data)
                    roadmaps.append(roadmap)
            except (json.JSONDecodeError, KeyError):
                continue
        return roadmaps

    async def find_latest_by_user_id(
        self, user_id: str
    ) -> Optional[LearningRoadmap]:
        """Find the latest roadmap for a user."""
        roadmaps = await self.find_by_user_id(user_id)
        if not roadmaps:
            return None
        return max(roadmaps, key=lambda r: r.created_at)

    async def save(self, roadmap: LearningRoadmap) -> None:
        """Save a roadmap."""
        file_path = self._get_file_path(roadmap.id)
        data = self._roadmap_to_dict(roadmap)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def delete(self, roadmap_id: str) -> bool:
        """Delete a roadmap by ID."""
        file_path = self._get_file_path(roadmap_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def _roadmap_to_dict(self, roadmap: LearningRoadmap) -> dict:
        """Convert roadmap entity to dictionary."""
        return {
            "id": roadmap.id,
            "user_id": roadmap.user_id,
            "target_domain": roadmap.target_domain.value if roadmap.target_domain else None,
            "target_role": roadmap.target_role,
            "duration_months": roadmap.duration_months,
            "quarters": [
                {
                    "quarter": q.quarter,
                    "theme": q.theme,
                    "goals": q.goals,
                    "milestones": [
                        {
                            "title": m.title,
                            "description": m.description,
                            "skills": m.skills,
                            "resources": [
                                {
                                    "title": r.title,
                                    "type": r.type,
                                    "url": r.url,
                                    "estimated_hours": r.estimated_hours,
                                    "priority": r.priority,
                                }
                                for r in m.resources
                            ],
                            "estimated_weeks": m.estimated_weeks,
                            "is_completed": m.is_completed,
                        }
                        for m in q.milestones
                    ],
                }
                for q in roadmap.quarters
            ],
            "prerequisites": roadmap.prerequisites,
            "final_project": roadmap.final_project,
            "notes": roadmap.notes,
            "created_at": roadmap.created_at.isoformat(),
            "updated_at": roadmap.updated_at.isoformat(),
        }

    def _dict_to_roadmap(self, data: dict) -> LearningRoadmap:
        """Convert dictionary to roadmap entity."""
        # Parse target domain
        target_domain = None
        if data.get("target_domain"):
            try:
                target_domain = EngineeringDomain(data["target_domain"])
            except ValueError:
                pass

        # Parse quarters
        quarters = []
        for q_data in data.get("quarters", []):
            milestones = []
            for m_data in q_data.get("milestones", []):
                resources = []
                for r_data in m_data.get("resources", []):
                    resources.append(
                        LearningResource(
                            title=r_data.get("title", ""),
                            type=r_data.get("type", "course"),
                            url=r_data.get("url"),
                            estimated_hours=r_data.get("estimated_hours"),
                            priority=r_data.get("priority", 1),
                        )
                    )

                milestones.append(
                    Milestone(
                        title=m_data.get("title", ""),
                        description=m_data.get("description", ""),
                        skills=m_data.get("skills", []),
                        resources=resources,
                        estimated_weeks=m_data.get("estimated_weeks", 4),
                        is_completed=m_data.get("is_completed", False),
                    )
                )

            quarters.append(
                QuarterPlan(
                    quarter=q_data.get("quarter", 1),
                    theme=q_data.get("theme", ""),
                    milestones=milestones,
                    goals=q_data.get("goals", []),
                )
            )

        # Parse timestamps
        created_at = datetime.now()
        updated_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                pass

        return LearningRoadmap(
            id=data["id"],
            user_id=data.get("user_id"),
            target_domain=target_domain,
            target_role=data.get("target_role"),
            duration_months=data.get("duration_months", 12),
            quarters=quarters,
            prerequisites=data.get("prerequisites", []),
            final_project=data.get("final_project"),
            notes=data.get("notes"),
            created_at=created_at,
            updated_at=updated_at,
        )

