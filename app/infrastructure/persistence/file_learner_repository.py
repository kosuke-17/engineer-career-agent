"""File-based learner repository implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.domain.entities import Learner, LearnerProfile
from app.domain.repositories import LearnerRepository
from app.domain.value_objects import (
    DomainAptitude,
    EngineeringDomain,
    LearningStyle,
    SkillScore,
)


class FileLearnerRepository(LearnerRepository):
    """File-based implementation of LearnerRepository."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, user_id: str) -> Path:
        """Get the file path for a learner."""
        # パストラバーサル対策
        safe_id = user_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        path = (self.base_path / f"{safe_id}.json").resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid user ID: path traversal detected")
        return path

    async def find_by_id(self, user_id: str) -> Optional[Learner]:
        """Find a learner by their ID."""
        file_path = self._get_file_path(user_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._dict_to_learner(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def save(self, learner: Learner) -> None:
        """Save a learner entity."""
        file_path = self._get_file_path(learner.id)
        data = self._learner_to_dict(learner)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def delete(self, user_id: str) -> bool:
        """Delete a learner by their ID."""
        file_path = self._get_file_path(user_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def exists(self, user_id: str) -> bool:
        """Check if a learner exists."""
        file_path = self._get_file_path(user_id)
        return file_path.exists()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Learner]:
        """List all learners with pagination."""
        learners = []
        files = sorted(self.base_path.glob("*.json"))

        for file_path in files[offset : offset + limit]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                learner = self._dict_to_learner(data)
                learners.append(learner)
            except (json.JSONDecodeError, KeyError):
                continue

        return learners

    def _learner_to_dict(self, learner: Learner) -> dict:
        """Convert learner entity to dictionary."""
        return {
            "id": learner.id,
            "profile": {
                "experience_years": learner.profile.experience_years,
                "current_role": learner.profile.current_role,
                "target_role": learner.profile.target_role,
                "preferred_styles": [s.value for s in learner.profile.preferred_styles],
                "weekly_hours": learner.profile.weekly_hours,
                "interests": learner.profile.interests,
                "constraints": learner.profile.constraints,
            },
            "skill_scores": [
                {
                    "skill_name": s.skill_name,
                    "score": s.score,
                    "level": s.level.value,
                    "notes": s.notes,
                }
                for s in learner.skill_scores
            ],
            "domain_aptitudes": [
                {
                    "domain": a.domain.value,
                    "score": a.score,
                    "reasoning": a.reasoning,
                }
                for a in learner.domain_aptitudes
            ],
            "created_at": learner.created_at.isoformat(),
            "updated_at": learner.updated_at.isoformat(),
        }

    def _dict_to_learner(self, data: dict) -> Learner:
        """Convert dictionary to learner entity."""
        # Parse profile
        profile_data = data.get("profile", {})
        preferred_styles = []
        for style in profile_data.get("preferred_styles", []):
            try:
                preferred_styles.append(LearningStyle(style))
            except ValueError:
                continue

        profile = LearnerProfile(
            experience_years=profile_data.get("experience_years"),
            current_role=profile_data.get("current_role"),
            target_role=profile_data.get("target_role"),
            preferred_styles=preferred_styles,
            weekly_hours=profile_data.get("weekly_hours"),
            interests=profile_data.get("interests", []),
            constraints=profile_data.get("constraints", []),
        )

        # Parse skill scores
        skill_scores = []
        for s_data in data.get("skill_scores", []):
            try:
                score = SkillScore.create(
                    skill_name=s_data["skill_name"],
                    score=float(s_data["score"]),
                    notes=s_data.get("notes"),
                )
                skill_scores.append(score)
            except (ValueError, KeyError):
                continue

        # Parse domain aptitudes
        domain_aptitudes = []
        for a_data in data.get("domain_aptitudes", []):
            try:
                aptitude = DomainAptitude(
                    domain=EngineeringDomain(a_data["domain"]),
                    score=float(a_data["score"]),
                    reasoning=a_data.get("reasoning"),
                )
                domain_aptitudes.append(aptitude)
            except (ValueError, KeyError):
                continue

        # Parse timestamps
        created_at = datetime.now()
        updated_at = datetime.now()
        if "created_at" in data:
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass
        if "updated_at" in data:
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                pass

        learner = Learner(
            id=data["id"],
            profile=profile,
            skill_scores=skill_scores,
            domain_aptitudes=domain_aptitudes,
            created_at=created_at,
            updated_at=updated_at,
        )
        return learner

