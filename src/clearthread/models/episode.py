"""Episode model for ClearThread (R6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentCategory, Model, ProvenanceRef


class EpisodeType(str, Enum):
    """Types of episodes (R6)."""

    CONFLICT = "conflict"
    BOUNDARY_SETTING = "boundary_setting"
    EMOTIONAL_SUPPORT = "emotional_support"
    PRACTICAL_SUPPORT = "practical_support"
    REQUEST = "request"
    REFUSAL = "refusal"
    APOLOGY = "apology"
    REPAIR_ATTEMPT = "repair_attempt"
    RECONCILIATION = "reconciliation"
    BREAKUP = "breakup"
    FINANCIAL_DISCUSSION = "financial_discussion"
    HEALTH_EVENT = "health_event"
    GRIEF = "grief"
    WORK_STRESS = "work_stress"
    MAJOR_DECISION = "major_decision"
    POSITIVE_CELEBRATION = "positive_celebration"
    ACTS_OF_CARE = "acts_of_care"
    GROWTH_MOMENT = "growth_moment"
    USER_DEFINED = "user_defined"


class EpisodeStatus(str, Enum):
    """Episode review status."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"
    SPLIT = "split"
    MERGED = "merged"
    DEFERRED = "deferred"


@dataclass
class MessageRef:
    """Reference to a message in episode context."""

    message_id: UUID
    position: int  # position relative to episode boundary


@dataclass
class Episode(Model):
    """Episode record (R6).

    A contiguous or semantically connected sequence of messages about a meaningful topic.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID | None = None

    # Boundaries
    start_message_id: UUID | None = None
    end_message_id: UUID | None = None

    # Context messages (R6: 3-10 on each boundary)
    context_before: list[MessageRef] = field(default_factory=list)
    context_after: list[MessageRef] = field(default_factory=list)

    # Classification
    episode_type: EpisodeType = EpisodeType.USER_DEFINED
    confidence: float = 0.0  # 0.0 to 1.0 (R6)
    status: EpisodeStatus = EpisodeStatus.PROPOSED
    user_classification: str | None = None

    # Content
    title: str = ""
    description: str = ""

    # Provenance
    provenance: ProvenanceRef | None = None
    content_category: ContentCategory = ContentCategory.CALCULATED_PATTERN

    # User interaction
    user_notes: str = ""
    confidence_score: float = 0.0  # Alias for confidence
    context_messages_count: int = 0  # Total messages in episode

    # Constraints (R6)
    MIN_CONTEXT_MESSAGES = 3
    MAX_CONTEXT_MESSAGES = 10
    MIN_CONFIDENCE = 0.5  # (R6)
    MAX_UNREVIEWED = 20  # (R6)

    def __post_init__(self):
        """Validate constraints."""
        if self.confidence < 0.0:
            self.confidence = 0.0
        if self.confidence > 1.0:
            self.confidence = 1.0
        # Ensure context messages are within bounds (R6)
        if len(self.context_before) > self.MAX_CONTEXT_MESSAGES:
            self.context_before = self.context_before[: self.MAX_CONTEXT_MESSAGES]
        if len(self.context_after) > self.MAX_CONTEXT_MESSAGES:
            self.context_after = self.context_after[: self.MAX_CONTEXT_MESSAGES]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "start_message_id": str(self.start_message_id) if self.start_message_id else None,
            "end_message_id": str(self.end_message_id) if self.end_message_id else None,
            "context_before": [
                {"message_id": str(ref.message_id), "position": ref.position}
                for ref in self.context_before
            ],
            "context_after": [
                {"message_id": str(ref.message_id), "position": ref.position}
                for ref in self.context_after
            ],
            "episode_type": self.episode_type.value,
            "confidence": self.confidence,
            "status": self.status.value,
            "user_classification": self.user_classification,
            "title": self.title,
            "description": self.description,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "content_category": self.content_category.value,
            "user_notes": self.user_notes,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        """Deserialize from dictionary."""

        def parse_uuid(val):
            if val is None:
                return None
            from uuid import UUID

            if isinstance(val, UUID):
                return val
            return UUID(val)

        def parse_message_ref(ref_data):
            return MessageRef(
                message_id=parse_uuid(ref_data["message_id"]),
                position=ref_data.get("position", 0),
            )

        episode_type_val = data.get("episode_type", "user_defined")
        if isinstance(episode_type_val, str):
            try:
                episode_type = EpisodeType(episode_type_val)
            except ValueError:
                episode_type = EpisodeType.USER_DEFINED
        else:
            episode_type = episode_type_val

        status_val = data.get("status", "proposed")
        if isinstance(status_val, str):
            try:
                status = EpisodeStatus(status_val)
            except ValueError:
                status = EpisodeStatus.PROPOSED
        else:
            status = status_val

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            conversation_id=parse_uuid(data.get("conversation_id")),
            start_message_id=parse_uuid(data.get("start_message_id")),
            end_message_id=parse_uuid(data.get("end_message_id")),
            context_before=[parse_message_ref(r) for r in data.get("context_before", [])],
            context_after=[parse_message_ref(r) for r in data.get("context_after", [])],
            episode_type=episode_type,
            confidence=data.get("confidence", 0.0),
            status=status,
            user_classification=data.get("user_classification"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
            content_category=ContentCategory(data.get("content_category", "calculated_pattern")),
            user_notes=data.get("user_notes", ""),
            confidence_score=data.get("confidence_score", data.get("confidence", 0.0)),
        )

    def is_surfaceable(self) -> bool:
        """Check if episode meets confidence threshold for review inbox (R6)."""
        return self.confidence >= self.MIN_CONFIDENCE

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Episode(id={self.id}, type={self.episode_type}, "
            f"confidence={self.confidence:.2f}, status={self.status.value})"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
