"""Message model for ClearThread (R1, R3, R18)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentHash, ExclusionState, Model, ProvenanceRef, UserReviewState


class MessageType(str, Enum):
    """Types of messages (R3)."""

    TEXT = "text"
    MEDIA = "media"
    STICKER = "sticker"
    LINK = "link"
    SYSTEM_EVENT = "system_event"
    CALL = "call"
    REACTION_ONLY = "reaction_only"
    UNKNOWN = "unknown"


@dataclass
class AttachmentRef:
    """Reference to an attachment (image, video, audio, GIF, sticker)."""

    uri: str
    attachment_type: str  # image, video, audio, gif, sticker
    creation_timestamp: datetime | None = None
    title: str | None = None
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "uri": self.uri,
            "attachment_type": self.attachment_type,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
        }


@dataclass
class Reaction:
    """A reaction on a message."""

    actor: str
    reaction: str  # emoji or text
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "actor": self.actor,
            "reaction": self.reaction,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Message(Model):
    """Normalized message record (R3).

    Represents a single message with all required fields for analysis.
    """

    # Core fields
    id: UUID = field(default_factory=uuid4)
    source_id: str = ""
    conversation_id: UUID | None = None
    sender_id: UUID | None = None
    recipient_ids: list[UUID] = field(default_factory=list)

    # Timestamps
    original_timestamp: datetime | None = None
    normalized_utc: datetime = field(default_factory=datetime.utcnow)
    original_timezone: str | None = None

    # Content
    text: str = ""
    message_type: MessageType = MessageType.TEXT
    attachment_refs: list[AttachmentRef] = field(default_factory=list)
    reactions: list[Reaction] = field(default_factory=list)

    # Relationships
    reply_to: UUID | None = None
    forwarded: bool = False
    quoted_content: str = ""

    # State
    deleted: bool = False
    unsent: bool = False
    detected_language: str = "en"

    # Provenance
    provenance: ProvenanceRef | None = None
    content_hash: str = ""
    owner_authored: bool = False
    analysis_eligible: bool = True
    exclusion_state: ExclusionState = ExclusionState.INCLUDED

    # User annotations
    user_annotation: str = ""
    user_review_state: UserReviewState = UserReviewState.UNREVIEWED

    # Speaker attribution (R18)
    attribution_warning: bool = False
    sender_display_name: str = ""

    def __post_init__(self):
        """Compute content hash if not set."""
        if not self.content_hash:
            self.content_hash = self._compute_content_hash()

    def _compute_content_hash(self) -> str:
        """Compute SHA-256 content hash."""
        if self.content_hash:
            return self.content_hash
        raw = f"{self.sender_id}:{self.original_timestamp}:{self.text}:{self.message_type}"
        return ContentHash.compute(str(raw))

    @staticmethod
    def compute_dedup_hash(sender: str, timestamp: str, message_text: str) -> str:
        """Compute deduplication hash (R1)."""
        return ContentHash.compute_message(sender, timestamp, message_text)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "sender_id": str(self.sender_id) if self.sender_id else None,
            "recipient_ids": [str(rid) for rid in self.recipient_ids],
            "original_timestamp": self.original_timestamp.isoformat() if self.original_timestamp else None,
            "normalized_utc": self.normalized_utc.isoformat(),
            "original_timezone": self.original_timezone,
            "text": self.text,
            "message_type": self.message_type.value,
            "attachment_refs": [ref.to_dict() for ref in self.attachment_refs],
            "reactions": [r.to_dict() for r in self.reactions],
            "reply_to": str(self.reply_to) if self.reply_to else None,
            "forwarded": self.forwarded,
            "quoted_content": self.quoted_content,
            "deleted": self.deleted,
            "unsent": self.unsent,
            "detected_language": self.detected_language,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "content_hash": self.content_hash,
            "owner_authored": self.owner_authored,
            "analysis_eligible": self.analysis_eligible,
            "exclusion_state": self.exclusion_state.value,
            "user_annotation": self.user_annotation,
            "user_review_state": self.user_review_state.value,
            "attribution_warning": self.attribution_warning,
            "sender_display_name": self.sender_display_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """Deserialize from dictionary."""
        def parse_datetime(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        def parse_uuid(val):
            if val is None:
                return None
            if isinstance(val, UUID):
                return val
            return UUID(val)

        return cls(
            id=parse_uuid(data.get("id")),
            source_id=data.get("source_id", ""),
            conversation_id=parse_uuid(data.get("conversation_id")),
            sender_id=parse_uuid(data.get("sender_id")),
            recipient_ids=[parse_uuid(rid) for rid in data.get("recipient_ids", [])],
            original_timestamp=parse_datetime(data.get("original_timestamp")),
            normalized_utc=parse_datetime(data.get("normalized_utc")) or datetime.utcnow(),
            original_timezone=data.get("original_timezone"),
            text=data.get("text", ""),
            message_type=MessageType(data.get("message_type", "text")),
            attachment_refs=[AttachmentRef(**ref) for ref in data.get("attachment_refs", [])],
            reactions=[Reaction(**r) for r in data.get("reactions", [])],
            reply_to=parse_uuid(data.get("reply_to")),
            forwarded=data.get("forwarded", False),
            quoted_content=data.get("quoted_content", ""),
            deleted=data.get("deleted", False),
            unsent=data.get("unsent", False),
            detected_language=data.get("detected_language", "en"),
            provenance=ProvenanceRef.from_dict(data["provenance"]) if data.get("provenance") else None,
            content_hash=data.get("content_hash", ""),
            owner_authored=data.get("owner_authored", False),
            analysis_eligible=data.get("analysis_eligible", True),
            exclusion_state=ExclusionState(data.get("exclusion_state", "included")),
            user_annotation=data.get("user_annotation", ""),
            user_review_state=UserReviewState(data.get("user_review_state", "unreviewed")),
            attribution_warning=data.get("attribution_warning", False),
            sender_display_name=data.get("sender_display_name", ""),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Message(id={self.id}, sender={self.sender_display_name}, "
            f"type={self.message_type}, text={self.text[:50]}...)"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
