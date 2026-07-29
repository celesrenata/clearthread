"""NormalizedStore - Canonical analytical storage (R3)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID, uuid4

from clearthread.models.base import ContentHash, ExclusionState, Model
from clearthread.models.message import Message, MessageType

logger = logging.getLogger(__name__)


class ReferentialIntegrityError(Exception):
    """Raised when a foreign reference does not resolve."""

    def __init__(self, field_name: str, reference_value: str, expected_type: str):
        self.field_name = field_name
        self.reference_value = reference_value
        self.expected_type = expected_type
        super().__init__(
            f"Referential integrity error: {field_name}={reference_value} "
            f"(expected {expected_type})"
        )


@dataclass
class QueryFilter:
    """Filter criteria for queries."""

    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    participant_id: UUID | None = None
    conversation_id: UUID | None = None
    message_type: MessageType | None = None
    attachment_present: bool | None = None
    user_authored_only: bool | None = None
    episode_type: str | None = None
    annotation_present: bool | None = None
    finding_association: str | None = None
    exclusion_state: ExclusionState | None = None


@dataclass
class QueryResult:
    """Result of a query operation."""

    messages: list[Message] = field(default_factory=list)
    total_count: int = 0
    has_more: bool = False
    query_time_ms: float = 0.0


class NormalizedStore:
    """Canonical analytical storage layer (R3).

    Stores normalized, source-independent message records with
    referential integrity and content hash tracking.
    """

    def __init__(self, data_dir: Path | str = "./normalized"):
        """Initialize the normalized store.

        Args:
            data_dir: Directory for storing normalized data.
        """
        self.data_dir = Path(data_dir)
        self._messages: dict[str, Message] = {}
        self._participants: dict[str, UUID] = {}  # participant_id -> UUID
        self._conversations: dict[str, UUID] = {}  # conversation_id -> UUID
        self._attachments: dict[str, list[str]] = {}  # attachment_id -> message_ids
        self._content_hashes: dict[str, str] = {}  # message_id -> content_hash
        self._index: dict[str, list[str]] = {}  # index_name -> message_ids
        self._updated_at: datetime = datetime.utcnow()

    @property
    def message_count(self) -> int:
        """Get total message count."""
        return len(self._messages)

    def save_message(self, message: Message, check_referential: bool = True) -> bool:
        """Save a message to the normalized store.

        Args:
            message: The message to save.
            check_referential: Whether to verify foreign references.

        Returns:
            True if saved successfully.

        Raises:
            ReferentialIntegrityError: If referential integrity check fails.
        """
        msg_id = str(message.id)

        # Check referential integrity if requested (R3)
        # Auto-register sender_id and conversation_id if not yet registered
        if check_referential:
            if message.conversation_id:
                cid = str(message.conversation_id)
                if cid not in self._conversations:
                    self._conversations[cid] = message.conversation_id
            if message.sender_id:
                pid = str(message.sender_id)
                if pid not in self._participants:
                    self._participants[pid] = message.sender_id

        # Check if content hash has changed (R3, R22)
        if msg_id in self._content_hashes:
            existing_hash = self._content_hashes[msg_id]
            if existing_hash == message.content_hash:
                logger.debug("Message %s unchanged, skipping reprocessing", msg_id)
                return False

        self._messages[msg_id] = message
        self._content_hashes[msg_id] = message.content_hash
        self._updated_at = datetime.utcnow()

        # Index by participant if set
        if message.sender_id:
            pid = str(message.sender_id)
            if pid not in self._participants:
                self._participants[pid] = message.sender_id

        # Index by conversation if set
        if message.conversation_id:
            cid = str(message.conversation_id)
            if cid not in self._conversations:
                self._conversations[cid] = message.conversation_id

        logger.debug("Saved message %s (hash: %s)", msg_id, message.content_hash[:16])
        return True

    def get_message(self, message_id: UUID | str) -> Message | None:
        """Get a message by ID.

        Args:
            message_id: The message ID.

        Returns:
            The Message or None if not found.
        """
        key = str(message_id) if not isinstance(message_id, UUID) else str(message_id)
        return self._messages.get(key)

    def get_messages_by_sender(self, sender_id: UUID | str) -> list[Message]:
        """Get all messages from a specific sender.

        Args:
            sender_id: The sender's participant ID.

        Returns:
            List of messages.
        """
        key = str(sender_id) if not isinstance(sender_id, UUID) else str(sender_id)
        return [m for m in self._messages.values() if str(m.sender_id) == key]

    def get_owner_authored_messages(self) -> list[Message]:
        """Get only owner-authored messages (R3).

        Returns:
            List of owner-authored messages.
        """
        return [m for m in self._messages.values() if m.owner_authored]

    def get_other_participant_messages(self) -> list[Message]:
        """Get only other-participant messages (R3).

        Returns:
            List of non-owner messages.
        """
        return [m for m in self._messages.values() if not m.owner_authored]

    def update_participant_merge(
        self, old_ids: list[UUID | str], new_id: UUID | str
    ) -> int:
        """Update messages after merging participants.

        Args:
            old_ids: IDs of merged participants.
            new_id: ID of the unified participant.

        Returns:
            Number of messages updated.
        """
        updated = 0
        for msg in self._messages.values():
            if str(msg.sender_id) in [str(oid) for oid in old_ids]:
                msg.sender_id = UUID(new_id) if not isinstance(new_id, UUID) else new_id
                updated += 1
        return updated

    def update_participant_split(
        self, old_id: UUID | str, assignments: dict[UUID | str, UUID | str]
    ) -> int:
        """Update messages after splitting a participant.

        Args:
            old_id: The original participant ID.
            assignments: Mapping of message IDs to new participant IDs.

        Returns:
            Number of messages reassigned.
        """
        reassigned = 0
        for msg_id, new_pid in assignments.items():
            msg = self._messages.get(str(msg_id))
            if msg and str(msg.sender_id) == str(old_id):
                msg.sender_id = UUID(new_pid) if not isinstance(new_id, UUID) else new_id
                reassigned += 1
        return reassigned

    def change_exclusion_state(
        self, message_ids: list[UUID | str], state: ExclusionState
    ) -> int:
        """Change the exclusion state of messages.

        Args:
            message_ids: IDs of messages to update.
            state: New exclusion state.

        Returns:
            Number of messages updated.
        """
        updated = 0
        for msg_id in message_ids:
            msg = self._messages.get(str(msg_id))
            if msg:
                msg.exclusion_state = state
                updated += 1
        return updated

    def query(self, filters: QueryFilter | None = None, limit: int = 50, offset: int = 0) -> QueryResult:
        """Query messages with optional filters.

        Args:
            filters: Query filter criteria.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            QueryResult with filtered messages.
        """
        messages = list(self._messages.values())

        if filters:
            if filters.date_range_start:
                messages = [
                    m for m in messages if m.normalized_utc and m.normalized_utc >= filters.date_range_start
                ]
            if filters.date_range_end:
                messages = [
                    m for m in messages if m.normalized_utc and m.normalized_utc <= filters.date_range_end
                ]
            if filters.participant_id:
                messages = [m for m in messages if str(m.sender_id) == str(filters.participant_id)]
            if filters.conversation_id:
                messages = [m for m in messages if str(m.conversation_id) == str(filters.conversation_id)]
            if filters.message_type:
                messages = [m for m in messages if m.message_type == filters.message_type]
            if filters.attachment_present is not None:
                if filters.attachment_present:
                    messages = [m for m in messages if m.attachment_refs]
                else:
                    messages = [m for m in messages if not m.attachment_refs]
            if filters.user_authored_only is not None:
                if filters.user_authored_only:
                    messages = [m for m in messages if m.owner_authored]
                else:
                    messages = [m for m in messages if not m.owner_authored]
            if filters.episode_type:
                messages = [m for m in messages if m.user_classification == filters.episode_type]
            if filters.annotation_present is not None:
                if filters.annotation_present:
                    messages = [m for m in messages if m.user_annotation]
                else:
                    messages = [m for m in messages if not m.user_annotation]
            if filters.exclusion_state:
                messages = [m for m in messages if m.exclusion_state == filters.exclusion_state]

        total_count = len(messages)
        paginated = messages[offset : offset + limit]
        has_more = (offset + limit) < total_count

        return QueryResult(
            messages=paginated,
            total_count=total_count,
            has_more=has_more,
        )

    def get_content_hash(self, message_id: UUID | str) -> str | None:
        """Get the content hash for a message.

        Args:
            message_id: The message ID.

        Returns:
            Content hash or None.
        """
        return self._content_hashes.get(str(message_id))

    def get_or_create_content_hash(self, message: Message) -> str:
        """Get or create content hash for a message.

        Args:
            message: The message.

        Returns:
            Content hash string.
        """
        msg_id = str(message.id)
        if msg_id not in self._content_hashes:
            self._content_hashes[msg_id] = message.content_hash
        return self._content_hashes[msg_id]

    def get_all_participants(self) -> dict[str, UUID]:
        """Get all participant IDs.

        Returns:
            Mapping of participant IDs.
        """
        return dict(self._participants)

    def get_all_conversations(self) -> dict[str, UUID]:
        """Get all conversation IDs.

        Returns:
            Mapping of conversation IDs.
        """
        return dict(self._conversations)

    def get_updated_at(self) -> datetime:
        """Get the last update timestamp.

        Returns:
            Last update datetime.
        """
        return self._updated_at

    def to_dict(self) -> dict[str, Any]:
        """Serialize store state to dictionary."""
        return {
            "message_count": len(self._messages),
            "participant_count": len(self._participants),
            "conversation_count": len(self._conversations),
            "content_hash_count": len(self._content_hashes),
            "updated_at": self._updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"NormalizedStore(messages={len(self._messages)}, "
            f"participants={len(self._participants)}, "
            f"conversations={len(self._conversations)})"
        )
