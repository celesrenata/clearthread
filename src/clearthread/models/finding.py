"""Finding model for ClearThread (R8, R21, R24)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentCategory, EvidenceReference, Model, ProvenanceRef


class ConfidenceLevel(str, Enum):
    """Confidence levels for findings (R8)."""

    STRONG = "Strong"
    MODERATE = "Moderate"
    PRELIMINARY = "Preliminary"


class FindingStatus(str, Enum):
    """Finding review status."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CORRECTED = "corrected"
    REJECTED = "rejected"


@dataclass
class ReflectionQuestionEntry:
    """A reflection question associated with a finding."""

    question: str
    data_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "question": self.question,
            "data_reference": self.data_reference,
        }


@dataclass
class Finding(Model):
    """Pattern finding record (R8, R21).

    A pattern or observation derived from analysis, always linked to supporting evidence.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    title: str = ""  # Max 80 characters (R8)
    explanation: str = ""  # Plain-language explanation

    # Evidence
    evidence_references: list[EvidenceReference] = field(default_factory=list)
    counterexamples: list[EvidenceReference] = field(default_factory=list)

    # Confidence (R8)
    confidence_level: ConfidenceLevel = ConfidenceLevel.PRELIMINARY
    confidence_percentage: float = 0.0  # 0-100% (R16)
    applicable_period_start: datetime | None = None
    applicable_period_end: datetime | None = None

    # Data limitations
    data_limitations: str = ""

    # Reflection questions (R8: at least 2)
    reflection_questions: list[ReflectionQuestionEntry] = field(default_factory=list)

    # Provenance
    provenance: ProvenanceRef | None = None

    # Review state
    status: FindingStatus = FindingStatus.PROPOSED
    content_category: ContentCategory = ContentCategory.CALCULATED_PATTERN

    # User corrections
    user_correction: str = ""  # Up to 5000 characters (R9)
    user_rejection_reason: str = ""

    # Model info (R13)
    model_name: str = ""
    model_version: str = ""
    prompt_version: str = ""

    # Constraints (R8)
    MAX_TITLE_LEN = 80
    MAX_USER_CORRECTION_LEN = 5000
    MIN_REFLECTION_QUESTIONS = 2
    MIN_EXCHANGES_FOR_PATTERN = 5  # (R8)
    MIN_MESSAGES_FOR_FINDING = 20  # (R9)

    def __post_init__(self):
        """Validate constraints."""
        if len(self.title) > self.MAX_TITLE_LEN:
            self.title = self.title[: self.MAX_TITLE_LEN]
        if len(self.user_correction) > self.MAX_USER_CORRECTION_LEN:
            self.user_correction = self.user_correction[: self.MAX_USER_CORRECTION_LEN]
        if self.confidence_percentage < 0:
            self.confidence_percentage = 0.0
        if self.confidence_percentage > 100:
            self.confidence_percentage = 100.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "explanation": self.explanation,
            "evidence_references": [ref.to_dict() for ref in self.evidence_references],
            "counterexamples": [ref.to_dict() for ref in self.counterexamples],
            "confidence_level": self.confidence_level.value,
            "confidence_percentage": self.confidence_percentage,
            "applicable_period_start": self.applicable_period_start.isoformat()
            if self.applicable_period_start
            else None,
            "applicable_period_end": self.applicable_period_end.isoformat()
            if self.applicable_period_end
            else None,
            "data_limitations": self.data_limitations,
            "reflection_questions": [q.to_dict() for q in self.reflection_questions],
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "status": self.status.value,
            "content_category": self.content_category.value,
            "user_correction": self.user_correction,
            "user_rejection_reason": self.user_rejection_reason,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
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

        def parse_evidence_ref(ref_data):
            from clearthread.models.base import EvidenceReference

            return EvidenceReference(
                message_id=parse_uuid(ref_data["message_id"]),
                source_id=ref_data["source_id"],
                conversation_id=parse_uuid(ref_data.get("conversation_id")),
                context_before=[parse_uuid(m) for m in ref_data.get("context_before", [])],
                context_after=[parse_uuid(m) for m in ref_data.get("context_after", [])],
                excerpt=ref_data.get("excerpt", ""),
            )

        confidence_level_val = data.get("confidence_level", "Preliminary")
        if isinstance(confidence_level_val, str):
            try:
                confidence_level = ConfidenceLevel(confidence_level_val)
            except ValueError:
                confidence_level = ConfidenceLevel.PRELIMINARY
        else:
            confidence_level = confidence_level_val

        status_val = data.get("status", "proposed")
        if isinstance(status_val, str):
            try:
                status = FindingStatus(status_val)
            except ValueError:
                status = FindingStatus.PROPOSED
        else:
            status = status_val

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            title=data.get("title", ""),
            explanation=data.get("explanation", ""),
            evidence_references=[parse_evidence_ref(r) for r in data.get("evidence_references", [])],
            counterexamples=[parse_evidence_ref(r) for r in data.get("counterexamples", [])],
            confidence_level=confidence_level,
            confidence_percentage=data.get("confidence_percentage", 0.0),
            applicable_period_start=parse_datetime(data.get("applicable_period_start")),
            applicable_period_end=parse_datetime(data.get("applicable_period_end")),
            data_limitations=data.get("data_limitations", ""),
            reflection_questions=[
                ReflectionQuestionEntry(**q) for q in data.get("reflection_questions", [])
            ],
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
            status=status,
            content_category=data.get("content_category", "calculated_pattern"),
            user_correction=data.get("user_correction", ""),
            user_rejection_reason=data.get("user_rejection_reason", ""),
            model_name=data.get("model_name", ""),
            model_version=data.get("model_version", ""),
            prompt_version=data.get("prompt_version", ""),
        )

    def has_sufficient_evidence(self) -> bool:
        """Check if finding has minimum evidence (R8)."""
        return len(self.evidence_references) >= 3

    def has_sufficient_exchanges(self, exchange_count: int) -> bool:
        """Check if there are enough exchanges for a pattern finding (R8)."""
        return exchange_count >= self.MIN_EXCHANGES_FOR_PATTERN

    def needs_more_data(self, message_count: int) -> bool:
        """Check if relationship has enough messages for findings (R9)."""
        return message_count < self.MIN_MESSAGES_FOR_FINDING

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Finding(id={self.id}, title={self.title}, "
            f"confidence={self.confidence_level.value}, "
            f"evidence={len(self.evidence_references)})"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
