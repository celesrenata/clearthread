"""ReflectionQuestion model for ClearThread (R26)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import Model, ProvenanceRef


@dataclass
class ReflectionQuestion(Model):
    """Reflection question (R26).

    A non-directive question generated to prompt user self-reflection.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    question_text: str = ""

    # Data references
    finding_id: UUID | None = None
    episode_id: UUID | None = None
    pattern_id: UUID | None = None
    data_element_reference: str = ""

    # Generation
    is_ai_generated: bool = True
    provenance: ProvenanceRef | None = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # User interaction
    is_dismissed: bool = False
    user_reflection: str = ""  # User's answer to the question
    is_saved_as_annotation: bool = False

    # Constraints (R26)
    MAX_QUESTIONS_PER_FINDING = 5
    MIN_QUESTIONS_PER_FINDING = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "question_text": self.question_text,
            "finding_id": str(self.finding_id) if self.finding_id else None,
            "episode_id": str(self.episode_id) if self.episode_id else None,
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "data_element_reference": self.data_element_reference,
            "is_ai_generated": self.is_ai_generated,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "generated_at": self.generated_at.isoformat(),
            "is_dismissed": self.is_dismissed,
            "user_reflection": self.user_reflection,
            "is_saved_as_annotation": self.is_saved_as_annotation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReflectionQuestion:
        """Deserialize from dictionary."""
        from uuid import UUID

        def parse_uuid(val):
            if val is None:
                return None
            if isinstance(val, UUID):
                return val
            return UUID(val)

        def parse_datetime(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            question_text=data.get("question_text", ""),
            finding_id=parse_uuid(data.get("finding_id")),
            episode_id=parse_uuid(data.get("episode_id")),
            pattern_id=parse_uuid(data.get("pattern_id")),
            data_element_reference=data.get("data_element_reference", ""),
            is_ai_generated=data.get("is_ai_generated", True),
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
            generated_at=parse_datetime(data.get("generated_at")) or datetime.utcnow(),
            is_dismissed=data.get("is_dismissed", False),
            user_reflection=data.get("user_reflection", ""),
            is_saved_as_annotation=data.get("is_saved_as_annotation", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "question_text": self.question_text,
            "finding_id": str(self.finding_id) if self.finding_id else None,
            "episode_id": str(self.episode_id) if self.episode_id else None,
            "pattern_id": str(self.pattern_id) if self.pattern_id else None,
            "data_element_reference": self.data_element_reference,
            "is_ai_generated": self.is_ai_generated,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "generated_at": self.generated_at.isoformat(),
            "is_dismissed": self.is_dismissed,
            "user_reflection": self.user_reflection,
            "is_saved_as_annotation": self.is_saved_as_annotation,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ReflectionQuestion(id={self.id}, text={self.question_text[:50]}...)"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
