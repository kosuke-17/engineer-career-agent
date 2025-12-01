"""Tests for roadmap generation tool."""

import json

from app.tools.roadmap import generate_learning_roadmap


class TestGenerateLearningRoadmap:
    """Tests for generate_learning_roadmap tool."""

    def test_basic_roadmap_generation(self):
        """Test basic roadmap generation."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 5.0,
                "recommended_domain": "backend",
                "technical_assessment": json.dumps({"Python": {"score": 6}}),
                "learning_style": "project_based",
                "available_hours_per_week": 15,
            }
        )
        data = json.loads(result)

        assert "summary" in data
        assert "phases" in data
        assert len(data["phases"]) == 4  # 4 quarters
        assert "learner_profile" in data

    def test_roadmap_with_low_foundation(self):
        """Test roadmap for learner with low foundation score."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 2.0,
                "recommended_domain": "frontend",
                "technical_assessment": "{}",
                "learning_style": "video",
                "available_hours_per_week": 5,
            }
        )
        data = json.loads(result)

        profile = data["learner_profile"]
        assert profile["start_level"] == "beginner"
        assert profile["pace"] == "slow"

    def test_roadmap_with_high_foundation(self):
        """Test roadmap for learner with high foundation score."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 8.0,
                "recommended_domain": "devops",
                "technical_assessment": "{}",
                "learning_style": "text",
                "available_hours_per_week": 20,
            }
        )
        data = json.loads(result)

        profile = data["learner_profile"]
        assert profile["start_level"] == "advanced"
        assert profile["pace"] == "intensive"

    def test_roadmap_phases_structure(self):
        """Test that each phase has required fields."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 5.0,
                "recommended_domain": "backend",
                "technical_assessment": "{}",
                "learning_style": "project_based",
                "available_hours_per_week": 10,
            }
        )
        data = json.loads(result)

        for phase in data["phases"]:
            assert "phase" in phase
            assert "name" in phase
            assert "duration_weeks" in phase
            assert "focus" in phase
            assert "goals" in phase
            assert "projects" in phase
            assert "milestones" in phase

    def test_roadmap_weekly_schedule(self):
        """Test weekly schedule suggestion."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 5.0,
                "recommended_domain": "backend",
                "technical_assessment": "{}",
                "learning_style": "project_based",
                "available_hours_per_week": 20,
            }
        )
        data = json.loads(result)

        schedule = data["weekly_schedule_suggestion"]
        assert schedule["total_hours"] == 20
        assert "distribution" in schedule
        assert sum(schedule["distribution"].values()) <= 20

    def test_success_tips_included(self):
        """Test that success tips are included."""
        result = generate_learning_roadmap.invoke(
            {
                "foundation_score": 5.0,
                "recommended_domain": "backend",
                "technical_assessment": "{}",
                "learning_style": "project_based",
                "available_hours_per_week": 10,
            }
        )
        data = json.loads(result)

        assert "success_tips" in data
        assert len(data["success_tips"]) > 0
