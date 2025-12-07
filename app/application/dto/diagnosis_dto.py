"""Data Transfer Objects for diagnosis system."""

from dataclasses import dataclass, field


@dataclass
class QuestionOption:
    """A single option for a question."""

    id: str
    label: str


@dataclass
class Question:
    """A structured question with options."""

    id: str
    text: str
    type: str  # "single" or "multiple"
    options: list[QuestionOption] = field(default_factory=list)


@dataclass
class Answer:
    """A user's answer to a question."""

    question_id: str
    selected_options: list[str] = field(default_factory=list)


@dataclass
class StructuredResponse:
    """Structured response from LLM containing message and questions."""

    message: str
    questions: list[Question] = field(default_factory=list)
    should_advance: bool = False
