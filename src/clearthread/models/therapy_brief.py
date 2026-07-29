"""TherapyBrief model for ClearThread (R10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentCategory, Model, ProvenanceRef


class BriefDetailLevel(str, Enum):
    """Detail levels for therapy briefs (R10)."""

    SUMMARY = "summary"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class BriefSectionType(str, Enum):
    """Types of sections in a therapy brief (R10)."""

    EVENTS_SINCE_PREVIOUS_SESSION = "events_since_previous_session"
    EMOTIONAL_RELATIONSHIP_CONCERNS = "emotional_relationship_concerns"
    CONFLICTS = "conflicts"
    BOUNDARIES_ATTEMPTED = "boundaries_attempted"
    SUPPORT_RECEIVED = "support_received"
    REPAIR_ATTEMPTS = "repair_attempts"
    REPEATED_PATTERNS = "repeated_patterns"
    POSITIVE_CHANGES = "positive_changes"
    DISCUSSION_QUESTIONS = "discussion_questions"
    RELEVANT_EXCERPTS = "relevant_excerpts"
    USER_ANNOTATIONS = "user_annotations"
    DATA_LIMITATIONS = "data_limitations"


@dataclass
class BriefSection:
    """A section within a therapy brief."""

    section_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    section_type: BriefSectionType = BriefSectionType.EVENTS_SINCE_PREVIOUS_SESSION
    source_category: ContentCategory = ContentCategory.CALCULATED_PATTERN
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    evidence_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "section_id": str(self.section_id),
            "title": self.title,
            "content": self.content,
            "section_type": self.section_type.value,
            "source_category": self.source_category.value,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "evidence_items": self.evidence_items,
        }


@dataclass
class TherapyBrief(Model):
    """Therapy brief (R10).

    A user-configured export summarizing selected relationships, episodes, and patterns.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Selection criteria
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    relationship_ids: list[UUID] = field(default_factory=list)
    episode_ids: list[UUID] = field(default_factory=list)
    topic_filters: list[str] = field(default_factory=list)

    # Display options
    include_message_excerpts: bool = True
    participant_name_visibility: bool = True
    sensitive_media_exclusion: bool = False
    detail_level: BriefDetailLevel = BriefDetailLevel.STANDARD

    # Sections
    sections: list[BriefSection] = field(default_factory=list)

    # Reflection questions (R10: 3-10)
    reflection_questions: list[str] = field(default_factory=list)

    # Data limitations (R10)
    data_limitations: str = ""

    # Export state
    export_format: str = "markdown"  # markdown, pdf, json, private_view
    is_finalized: bool = False

    # Provenance
    provenance: ProvenanceRef | None = None

    # Constraints (R10)
    MIN_REFLECTION_QUESTIONS = 3
    MAX_REFLECTION_QUESTIONS = 10

    def add_section(self, section: BriefSection) -> None:
        """Add a section to the brief."""
        self.sections.append(section)
        self.updated_at = datetime.utcnow()

    def add_reflection_question(self, question: str) -> bool:
        """Add a reflection question if under limit."""
        if len(self.reflection_questions) >= self.MAX_REFLECTION_QUESTIONS:
            return False
        self.reflection_questions.append(question)
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "relationship_ids": [str(rid) for rid in self.relationship_ids],
            "episode_ids": [str(eid) for eid in self.episode_ids],
            "topic_filters": self.topic_filters,
            "include_message_excerpts": self.include_message_excerpts,
            "participant_name_visibility": self.participant_name_visibility,
            "sensitive_media_exclusion": self.sensitive_media_exclusion,
            "detail_level": self.detail_level.value,
            "sections": [s.to_dict() for s in self.sections],
            "reflection_questions": self.reflection_questions,
            "data_limitations": self.data_limitations,
            "export_format": self.export_format,
            "is_finalized": self.is_finalized,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TherapyBrief:
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

        def parse_section(sec_data):
            from clearthread.models.base import ContentCategory

            return BriefSection(
                section_id=parse_uuid(sec_data.get("section_id")),
                title=sec_data.get("title", ""),
                content=sec_data.get("content", ""),
                section_type=BriefSectionType(sec_data.get("section_type", "events_since_previous_session")),
                source_category=ContentCategory(sec_data.get("source_category", "calculated_pattern")),
                date_range_start=parse_datetime(sec_data.get("date_range_start")),
                date_range_end=parse_datetime(sec_data.get("date_range_end")),
                evidence_items=sec_data.get("evidence_items", []),
            )

        detail_level_val = data.get("detail_level", "standard")
        if isinstance(detail_level_val, str):
            try:
                detail_level = BriefDetailLevel(detail_level_val)
            except ValueError:
                detail_level = BriefDetailLevel.STANDARD
        else:
            detail_level = detail_level_val

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            title=data.get("title", ""),
            created_at=parse_datetime(data.get("created_at")) or datetime.utcnow(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.utcnow(),
            date_range_start=parse_datetime(data.get("date_range_start")),
            date_range_end=parse_datetime(data.get("date_range_end")),
            relationship_ids=[parse_uuid(rid) for rid in data.get("relationship_ids", [])],
            episode_ids=[parse_uuid(eid) for eid in data.get("episode_ids", [])],
            topic_filters=data.get("topic_filters", []),
            include_message_excerpts=data.get("include_message_excerpts", True),
            participant_name_visibility=data.get("participant_name_visibility", True),
            sensitive_media_exclusion=data.get("sensitive_media_exclusion", False),
            detail_level=detail_level,
            sections=[parse_section(s) for s in data.get("sections", [])],
            reflection_questions=data.get("reflection_questions", []),
            data_limitations=data.get("data_limitations", ""),
            export_format=data.get("export_format", "markdown"),
            is_finalized=data.get("is_finalized", False),
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "relationship_ids": [str(rid) for rid in self.relationship_ids],
            "episode_ids": [str(eid) for eid in self.episode_ids],
            "topic_filters": self.topic_filters,
            "include_message_excerpts": self.include_message_excerpts,
            "participant_name_visibility": self.participant_name_visibility,
            "sensitive_media_exclusion": self.sensitive_media_exclusion,
            "detail_level": self.detail_level.value,
            "sections": [s.to_dict() for s in self.sections],
            "reflection_questions": self.reflection_questions,
            "data_limitations": self.data_limitations,
            "export_format": self.export_format,
            "is_finalized": self.is_finalized,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TherapyBrief(id={self.id}, title={self.title}, "
            f"sections={len(self.sections)}, questions={len(self.reflection_questions)})"
        )
