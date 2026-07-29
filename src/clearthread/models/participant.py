"""Participant model for ClearThread (R4, R18, R19)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import Model


class RelationshipCategory(str, Enum):
    """Relationship categories (R4)."""

    PARTNER = "Partner"
    FORMER_PARTNER = "Former partner"
    FRIEND = "Friend"
    FAMILY = "Family"
    COWORKER = "Coworker"
    MANAGER = "Manager"
    COMMUNITY_MEMBER = "Community member"
    ACQUAINTANCE = "Acquaintance"
    UNKNOWN = "Unknown"
    CUSTOM = "Custom"


@dataclass
class Participant(Model):
    """Participant identity record (R4).

    Represents a person in the conversation data, including the user.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    source_id: str = ""
    display_name: str = ""
    aliases: list[str] = field(default_factory=list)

    # User identification (R4)
    is_user: bool = False
    is_past: bool = False

    # Relationship metadata
    category: RelationshipCategory = RelationshipCategory.UNKNOWN
    custom_category: str = ""
    start_date: date | None = None
    end_date: date | None = None

    # Counts
    message_count: int = 0
    media_count: int = 0

    # User-supplied data
    note: str = ""  # Up to 2000 characters (R4)

    # Exclusion (R19)
    excluded: bool = False

    # Display constraints (R4)
    MAX_DISPLAY_NAME_LEN = 100
    MAX_ALIAS_LEN = 100
    MAX_ALIASES = 10
    MAX_NOTE_LEN = 2000
    MAX_CUSTOM_CATEGORY_LEN = 50
    MAX_CUSTOM_CATEGORIES = 20

    def __post_init__(self):
        """Validate constraints."""
        if len(self.display_name) > self.MAX_DISPLAY_NAME_LEN:
            self.display_name = self.display_name[: self.MAX_DISPLAY_NAME_LEN]
        if len(self.note) > self.MAX_NOTE_LEN:
            self.note = self.note[: self.MAX_NOTE_LEN]
        if self.custom_category and len(self.custom_category) > self.MAX_CUSTOM_CATEGORY_LEN:
            self.custom_category = self.custom_category[: self.MAX_CUSTOM_CATEGORY_LEN]
        if len(self.aliases) > self.MAX_ALIASES:
            self.aliases = self.aliases[: self.MAX_ALIASES]
        for i, alias in enumerate(self.aliases):
            if len(alias) > self.MAX_ALIAS_LEN:
                self.aliases[i] = alias[: self.MAX_ALIAS_LEN]

    def add_alias(self, alias: str) -> bool:
        """Add an alias if under the limit."""
        if len(self.aliases) >= self.MAX_ALIASES:
            return False
        if len(alias) > self.MAX_ALIAS_LEN:
            alias = alias[: self.MAX_ALIAS_LEN]
        if alias not in self.aliases:
            self.aliases.append(alias)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "display_name": self.display_name,
            "aliases": self.aliases,
            "is_user": self.is_user,
            "is_past": self.is_past,
            "category": self.category.value if isinstance(self.category, RelationshipCategory) else self.category,
            "custom_category": self.custom_category,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "message_count": self.message_count,
            "media_count": self.media_count,
            "note": self.note,
            "excluded": self.excluded,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Participant:
        """Deserialize from dictionary."""
        from datetime import date as date_type

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date_type):
                return val
            return date.fromisoformat(val)

        category_val = data.get("category", "Unknown")
        if isinstance(category_val, str):
            try:
                category = RelationshipCategory(category_val)
            except ValueError:
                category = RelationshipCategory.CUSTOM
        else:
            category = category_val

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            source_id=data.get("source_id", ""),
            display_name=data.get("display_name", ""),
            aliases=data.get("aliases", []),
            is_user=data.get("is_user", False),
            is_past=data.get("is_past", False),
            category=category,
            custom_category=data.get("custom_category", ""),
            start_date=parse_date(data.get("start_date")),
            end_date=parse_date(data.get("end_date")),
            message_count=data.get("message_count", 0),
            media_count=data.get("media_count", 0),
            note=data.get("note", ""),
            excluded=data.get("excluded", False),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Participant(id={self.id}, name={self.display_name}, "
            f"category={self.category}, is_user={self.is_user})"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
