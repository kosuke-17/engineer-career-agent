"""Tests for assessment tools."""

import json

from app.tools.assessment import (
    assess_domain_aptitude,
    assess_foundation_skills,
    assess_technical_depth,
    fetch_learning_resources,
)


class TestAssessFoundationSkills:
    """Tests for assess_foundation_skills tool."""

    def test_programming_assessment(self):
        """Test programming assessment returns valid questions."""
        result = assess_foundation_skills.invoke({"assessment_type": "programming"})
        data = json.loads(result)

        assert "questions" in data
        assert "evaluation_criteria" in data
        assert len(data["questions"]) > 0
        assert "beginner" in data["evaluation_criteria"]
        assert "intermediate" in data["evaluation_criteria"]
        assert "advanced" in data["evaluation_criteria"]

    def test_algorithms_assessment(self):
        """Test algorithms assessment returns valid questions."""
        result = assess_foundation_skills.invoke({"assessment_type": "algorithms"})
        data = json.loads(result)

        assert "questions" in data
        assert "evaluation_criteria" in data
        assert any("Big O" in q or "計算量" in q for q in data["questions"])

    def test_data_structures_assessment(self):
        """Test data structures assessment returns valid questions."""
        result = assess_foundation_skills.invoke({"assessment_type": "data_structures"})
        data = json.loads(result)

        assert "questions" in data
        assert "evaluation_criteria" in data
        assert any("配列" in q or "リスト" in q for q in data["questions"])


class TestAssessDomainAptitude:
    """Tests for assess_domain_aptitude tool."""

    def test_single_domain(self):
        """Test assessment for a single domain."""
        result = assess_domain_aptitude.invoke({"domains": "backend"})
        data = json.loads(result)

        assert "backend" in data
        assert "name" in data["backend"]
        assert "questions" in data["backend"]
        assert "key_skills" in data["backend"]

    def test_multiple_domains(self):
        """Test assessment for multiple domains."""
        result = assess_domain_aptitude.invoke({"domains": "frontend,backend,devops"})
        data = json.loads(result)

        assert "frontend" in data
        assert "backend" in data
        assert "devops" in data

    def test_unknown_domain(self):
        """Test handling of unknown domain."""
        result = assess_domain_aptitude.invoke({"domains": "unknown_domain"})
        data = json.loads(result)

        assert "unknown_domain" in data
        assert "error" in data["unknown_domain"]


class TestAssessTechnicalDepth:
    """Tests for assess_technical_depth tool."""

    def test_known_technologies(self):
        """Test assessment for known technologies."""
        result = assess_technical_depth.invoke(
            {
                "domain": "backend",
                "technologies": "Python,FastAPI",
            }
        )
        data = json.loads(result)

        assert "domain" in data
        assert "technologies" in data
        assert "Python" in data["technologies"]
        assert "FastAPI" in data["technologies"]

    def test_unknown_technology(self):
        """Test handling of unknown technology."""
        result = assess_technical_depth.invoke(
            {
                "domain": "backend",
                "technologies": "UnknownTech",
            }
        )
        data = json.loads(result)

        assert "UnknownTech" in data["technologies"]
        # Should still return questions for unknown tech
        assert "questions" in data["technologies"]["UnknownTech"]


class TestFetchLearningResources:
    """Tests for fetch_learning_resources tool."""

    def test_beginner_python_video(self):
        """Test fetching beginner Python video resources."""
        result = fetch_learning_resources.invoke(
            {
                "skill_level": "beginner",
                "topic": "Python",
                "preferred_format": "video",
            }
        )
        data = json.loads(result)

        assert data["topic"] == "Python"
        assert data["skill_level"] == "beginner"
        assert data["format"] == "video"
        assert "resources" in data
        assert len(data["resources"]) > 0

    def test_intermediate_react_project(self):
        """Test fetching intermediate React project resources."""
        result = fetch_learning_resources.invoke(
            {
                "skill_level": "intermediate",
                "topic": "React",
                "preferred_format": "project",
            }
        )
        data = json.loads(result)

        assert data["topic"] == "React"
        assert data["skill_level"] == "intermediate"
        assert "resources" in data

    def test_unknown_topic_fallback(self):
        """Test fallback resources for unknown topic."""
        result = fetch_learning_resources.invoke(
            {
                "skill_level": "beginner",
                "topic": "UnknownTopic",
                "preferred_format": "text",
            }
        )
        data = json.loads(result)

        assert "resources" in data
        assert "note" in data  # Should include a note about fallback
