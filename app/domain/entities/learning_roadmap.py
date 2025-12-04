"""Learning roadmap domain entities.

This module defines the domain entities for the learning roadmap generation feature
using LangGraph agents.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceLink:
    """A reference link for learning resources."""

    title: str
    url: str


@dataclass
class TechnologyInfo:
    """Information about a technology gathered from research.

    Attributes:
        name: The name of the technology (e.g., "React", "Next.js").
        summary: A brief summary of what the technology is and its main features.
        links: Reference links for detailed information and tutorials.
    """

    name: str
    summary: str
    links: list[SourceLink] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "summary": self.summary,
            "links": [{"title": link.title, "url": link.url} for link in self.links],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TechnologyInfo":
        """Create from dictionary representation."""
        links = [
            SourceLink(title=link["title"], url=link["url"])
            for link in data.get("links", [])
        ]
        return cls(
            name=data["name"],
            summary=data.get("summary", ""),
            links=links,
        )


@dataclass
class LearningStep:
    """A single learning step within a phase.

    Attributes:
        topic: The learning topic (e.g., "Environment Setup").
        estimated_time: Estimated time to complete (e.g., "4h").
        source_links: Reference links for this step.
    """

    topic: str
    estimated_time: str
    source_links: list[SourceLink] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "topic": self.topic,
            "estimatedTime": self.estimated_time,
            "sourceLinks": [
                {"title": link.title, "url": link.url} for link in self.source_links
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningStep":
        """Create from dictionary representation."""
        links = [
            SourceLink(title=link["title"], url=link["url"])
            for link in data.get("sourceLinks", [])
        ]
        return cls(
            topic=data["topic"],
            estimated_time=data.get("estimatedTime", ""),
            source_links=links,
        )


@dataclass
class LearningPhase:
    """A learning phase containing multiple steps.

    Attributes:
        phase_name: Name of the phase (e.g., "基礎", "応用", "実践").
        order: Order of this phase in the roadmap.
        steps: List of learning steps in this phase.
    """

    phase_name: str
    order: int
    steps: list[LearningStep] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "phaseName": self.phase_name,
            "order": self.order,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningPhase":
        """Create from dictionary representation."""
        steps = [LearningStep.from_dict(step) for step in data.get("steps", [])]
        return cls(
            phase_name=data["phaseName"],
            order=data.get("order", 0),
            steps=steps,
        )


@dataclass
class TechnologyRoadmap:
    """Roadmap for a single technology.

    Attributes:
        name: Technology name.
        summary: Summary from research.
        phases: Learning phases for this technology.
    """

    name: str
    summary: str
    phases: list[LearningPhase] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "summary": self.summary,
            "phases": [phase.to_dict() for phase in self.phases],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TechnologyRoadmap":
        """Create from dictionary representation."""
        phases = [LearningPhase.from_dict(phase) for phase in data.get("phases", [])]
        return cls(
            name=data["name"],
            summary=data.get("summary", ""),
            phases=phases,
        )


@dataclass
class LearningRoadmap:
    """Complete learning roadmap entity.

    This is the final output of the LangGraph agent workflow.

    Attributes:
        title: Title of the roadmap.
        technologies: List of technology roadmaps.
        user_request: Original user request.
        extracted_tags: Tags extracted from user request.
    """

    title: str
    technologies: list[TechnologyRoadmap] = field(default_factory=list)
    user_request: Optional[str] = None
    extracted_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation matching the JSON schema."""
        return {
            "roadmapTitle": self.title,
            "technologies": [tech.to_dict() for tech in self.technologies],
            "userRequest": self.user_request,
            "extractedTags": self.extracted_tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearningRoadmap":
        """Create from dictionary representation."""
        technologies = [
            TechnologyRoadmap.from_dict(tech) for tech in data.get("technologies", [])
        ]
        return cls(
            title=data.get("roadmapTitle", ""),
            technologies=technologies,
            user_request=data.get("userRequest"),
            extracted_tags=data.get("extractedTags", []),
        )

    def to_json_schema(self) -> dict:
        """Convert to the exact JSON schema format specified in requirements."""
        return {
            "roadmapTitle": self.title,
            "technologies": [
                {
                    "name": tech.name,
                    "summary": tech.summary,
                    "phases": [
                        {
                            "phaseName": phase.phase_name,
                            "order": phase.order,
                            "steps": [
                                {
                                    "topic": step.topic,
                                    "estimatedTime": step.estimated_time,
                                    "sourceLinks": [
                                        {"title": link.title, "url": link.url}
                                        for link in step.source_links
                                    ],
                                }
                                for step in phase.steps
                            ],
                        }
                        for phase in tech.phases
                    ],
                }
                for tech in self.technologies
            ],
        }

