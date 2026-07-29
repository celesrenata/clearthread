"""RelationshipChapter model for ClearThread (R25)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentCategory, Model, ProvenanceRef


class ChapterSectionType(str, Enum):
    """Types of sections in a relationship chapter."""

    DOCUMENTED_FACT = "documented_fact"
    CALCULATED_PATTERN = "calculated_pattern"
    AI_GENERATED_SUMMARY = "ai_generated_summary"
    USER_SUPPLIED_CONTEXT = "user_supplied_context"
    UNCERTAIN_MISSING = "uncertain_missing"


@dataclass
class ChapterSection:
    """A section within a relationship chapter."""

    section_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    section_type: ChapterSectionType = ChapterSectionType.AI_GENERATED_SUMMARY
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    evidence_citations: list[str] = field(default_factory=list)  # Episode IDs
    user_edits: str = ""
    is_user_editable: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "section_id": str(self.section_id),
            "title": self.title,
            "content": self.content,
            "section_type": self.section_type.value,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "evidence_citations": self.evidence_citations,
            "user_edits": self.user_edits,
            "is_user_editable": self.is_user_editable,
        }


@dataclass
class RelationshipChapter(Model):
    """Relationship chapter reconstruction (R25).

    An organized narrative reconstruction of an individual relationship.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    relationship_id: UUID = field(default_factory=uuid4)
    participant_id: UUID = field(default_factory=uuid4)

    # Metadata
    title: str = ""
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None

    # Sections
    sections: list[ChapterSection] = field(default_factory=list)

    # Summary fields
    how_relationship_began: str = ""
    major_phases: list[str] = field(default_factory=list)
    positive_patterns: list[str] = field(default_factory=list)
    negative_patterns: list[str] = field(default_factory=list)
    recurring_conflicts: list[str] = field(default_factory=list)
    boundary_discussions: list[str] = field(default_factory=list)
    repair_attempts: list[str] = field(default_factory=list)
    reconciliations: list[str] = field(default_factory=list)
    turning_points: list[str] = field(default_factory=list)
    contact_periods: list[str] = field(default_factory=list)
    no_contact_periods: list[str] = field(default_factory=list)
    ending: str = ""
    post_relationship_contact: str = ""
    user_reflections: list[str] = field(default_factory=list)

    # Provenance
    provenance: ProvenanceRef | None = None

    # Quality (R25)
    has_positive_pattern: bool = False
    has_negative_pattern: bool = False
    insufficient_data: bool = False
    source_episode_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "relationship_id": str(self.relationship_id),
            "participant_id": str(self.participant_id),
            "title": self.title,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "sections": [s.to_dict() for s in self.sections],
            "how_relationship_began": self.how_relationship_began,
            "major_phases": self.major_phases,
            "positive_patterns": self.positive_patterns,
            "negative_patterns": self.negative_patterns,
            "recurring_conflicts": self.recurring_conflicts,
            "boundary_discussions": self.boundary_discussions,
            "repair_attempts": self.repair_attempts,
            "reconciliations": self.reconciliations,
            "turning_points": self.turning_points,
            "contact_periods": self.contact_periods,
            "no_contact_periods": self.no_contact_periods,
            "ending": self.ending,
            "post_relationship_contact": self.post_relationship_contact,
            "user_reflections": self.user_reflections,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "has_positive_pattern": self.has_positive_pattern,
            "has_negative_pattern": self.has_negative_pattern,
            "insufficient_data": self.insufficient_data,
            "source_episode_count": self.source_episode_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationshipChapter:
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
            return ChapterSection(
                section_id=parse_uuid(sec_data.get("section_id")),
                title=sec_data.get("title", ""),
                content=sec_data.get("content", ""),
                section_type=ChapterSectionType(sec_data.get("section_type", "ai_generated_summary")),
                date_range_start=parse_datetime(sec_data.get("date_range_start")),
                date_range_end=parse_datetime(sec_data.get("date_range_end")),
                evidence_citations=sec_data.get("evidence_citations", []),
                user_edits=sec_data.get("user_edits", ""),
                is_user_editable=sec_data.get("is_user_editable", True),
            )

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            relationship_id=parse_uuid(data.get("relationship_id")),
            participant_id=parse_uuid(data.get("participant_id")),
            title=data.get("title", ""),
            date_range_start=parse_datetime(data.get("date_range_start")),
            date_range_end=parse_datetime(data.get("date_range_end")),
            sections=[parse_section(s) for s in data.get("sections", [])],
            how_relationship_began=data.get("how_relationship_began", ""),
            major_phases=data.get("major_phases", []),
            positive_patterns=data.get("positive_patterns", []),
            negative_patterns=data.get("negative_patterns", []),
            recurring_conflicts=data.get("recurring_conflicts", []),
            boundary_discussions=data.get("boundary_discussions", []),
            repair_attempts=data.get("repair_attempts", []),
            reconciliations=data.get("reconciliations", []),
            turning_points=data.get("turning_points", []),
            contact_periods=data.get("contact_periods", []),
            no_contact_periods=data.get("no_contact_periods", []),
            ending=data.get("ending", ""),
            post_relationship_contact=data.get("post_relationship_contact", ""),
            user_reflections=data.get("user_reflections", []),
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
            has_positive_pattern=data.get("has_positive_pattern", False),
            has_negative_pattern=data.get("has_negative_pattern", False),
            insufficient_data=data.get("insufficient_data", False),
            source_episode_count=data.get("source_episode_count", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "relationship_id": str(self.relationship_id),
            "participant_id": str(self.participant_id),
            "title": self.title,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "sections": [s.to_dict() for s in self.sections],
            "how_relationship_began": self.how_relationship_began,
            "major_phases": self.major_phases,
            "positive_patterns": self.positive_patterns,
            "negative_patterns": self.negative_patterns,
            "recurring_conflicts": self.recurring_conflicts,
            "boundary_discussions": self.boundary_discussions,
            "repair_attempts": self.repair_attempts,
            "reconciliations": self.reconciliations,
            "turning_points": self.turning_points,
            "contact_periods": self.contact_periods,
            "no_contact_periods": self.no_contact_periods,
            "ending": self.ending,
            "post_relationship_contact": self.post_relationship_contact,
            "user_reflections": self.user_reflections,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "has_positive_pattern": self.has_positive_pattern,
            "has_negative_pattern": self.has_negative_pattern,
            "insufficient_data": self.insufficient_data,
            "source_episode_count": self.source_episode_count,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RelationshipChapter(id={self.id}, title={self.title}, "
            f"episodes={self.source_episode_count})"
        )
