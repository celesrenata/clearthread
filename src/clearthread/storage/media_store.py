"""MediaStore - Image/video attachment storage."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class MediaRecord:
    """A media attachment record."""

    id: UUID = field(default_factory=uuid4)
    uri: str = ""
    media_type: str = ""  # image, video, audio, gif, sticker
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    creation_timestamp: datetime | None = None
    title: str = ""
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
    local_path: str = ""
    is_blurred: bool = False
    is_sensitive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "uri": self.uri,
            "media_type": self.media_type,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "message_id": str(self.message_id) if self.message_id else None,
            "creation_timestamp": self.creation_timestamp.isoformat() if self.creation_timestamp else None,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
            "local_path": self.local_path,
            "is_blurred": self.is_blurred,
            "is_sensitive": self.is_sensitive,
        }


class MediaStore:
    """Storage for extracted images, videos, and other media.

    Manages media attachments with references to source messages.
    """

    def __init__(self, media_dir: Path | str = "./media"):
        """Initialize the media store.

        Args:
            media_dir: Directory for storing media files.
        """
        self.media_dir = Path(media_dir)
        self._media_records: dict[str, MediaRecord] = {}
        self._message_to_media: dict[str, list[str]] = {}  # message_id -> media_ids
        self._conversation_dirs: dict[str, Path] = {}  # conversation_id -> directory

        # Create subdirectories
        self.media_dir.mkdir(parents=True, exist_ok=True)
        (self.media_dir / "images").mkdir(exist_ok=True)
        (self.media_dir / "videos").mkdir(exist_ok=True)
        (self.media_dir / "audio").mkdir(exist_ok=True)
        (self.media_dir / "stickers").mkdir(exist_ok=True)

    def add_media(
        self,
        uri: str,
        media_type: str,
        conversation_id: UUID | None = None,
        message_id: UUID | None = None,
        local_path: str = "",
        title: str = "",
        is_sensitive: bool = False,
    ) -> MediaRecord:
        """Add a media record.

        Args:
            uri: URI of the media in the source export.
            media_type: Type of media (image, video, audio, gif, sticker).
            conversation_id: Associated conversation ID.
            message_id: Associated message ID.
            local_path: Local file path.
            title: Media title.
            is_sensitive: Whether the media is sensitive.

        Returns:
            The created MediaRecord.
        """
        record = MediaRecord(
            uri=uri,
            media_type=media_type,
            conversation_id=conversation_id,
            message_id=message_id,
            local_path=local_path,
            title=title,
            is_sensitive=is_sensitive,
            is_blurred=is_sensitive,  # Default: blur sensitive media (R17)
        )

        record_id = str(record.id)
        self._media_records[record_id] = record

        # Index by message
        if message_id:
            msg_key = str(message_id)
            if msg_key not in self._message_to_media:
                self._message_to_media[msg_key] = []
            self._message_to_media[msg_key].append(record_id)

        logger.debug("Added media %s (%s) for message %s", record_id, media_type, message_id)
        return record

    def get_media_by_message(self, message_id: UUID | str) -> list[MediaRecord]:
        """Get all media for a message.

        Args:
            message_id: The message ID.

        Returns:
            List of MediaRecords.
        """
        key = str(message_id) if not isinstance(message_id, UUID) else str(message_id)
        media_ids = self._message_to_media.get(key, [])
        return [self._media_records[mid] for mid in media_ids if mid in self._media_records]

    def get_media_by_conversation(self, conversation_id: UUID | str) -> list[MediaRecord]:
        """Get all media in a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            List of MediaRecords.
        """
        key = str(conversation_id) if not isinstance(conversation_id, UUID) else str(conversation_id)
        return [
            m for m in self._media_records.values()
            if str(m.conversation_id) == key
        ]

    def get_sensitive_media(self) -> list[MediaRecord]:
        """Get all sensitive media.

        Returns:
            List of sensitive MediaRecords.
        """
        return [m for m in self._media_records.values() if m.is_sensitive]

    def blur_sensitive_media(self) -> int:
        """Blur all sensitive media by default (R17).

        Returns:
            Number of media items blurred.
        """
        count = 0
        for media in self._media_records.values():
            if media.is_sensitive:
                if not media.is_blurred:
                    media.is_blurred = True
                    count += 1
                else:
                    # Already blurred (set at add time)
                    count += 1
        return count

    def unblur_media(self, media_id: UUID | str) -> bool:
        """Unblur a specific media item.

        Args:
            media_id: The media ID.

        Returns:
            True if media was unblurred.
        """
        key = str(media_id) if not isinstance(media_id, UUID) else str(media_id)
        media = self._media_records.get(key)
        if media:
            media.is_blurred = False
            return True
        return False

    def get_media_count(self) -> int:
        """Get total media count.

        Returns:
            Number of media records.
        """
        return len(self._media_records)

    def get_total_size(self) -> int | None:
        """Get total size of all media.

        Returns:
            Total size in bytes, or None if any size is unknown.
        """
        total = 0
        has_unknown = False
        for media in self._media_records.values():
            if media.size_bytes is None:
                has_unknown = True
            else:
                total += media.size_bytes
        return total if not has_unknown else None

    def to_dict(self) -> dict[str, Any]:
        """Serialize store state to dictionary."""
        return {
            "media_count": len(self._media_records),
            "message_media_mapping": len(self._message_to_media),
            "sensitive_count": sum(1 for m in self._media_records.values() if m.is_sensitive),
            "blurred_count": sum(1 for m in self._media_records.values() if m.is_blurred),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MediaStore(media={len(self._media_records)}, "
            f"sensitive={sum(1 for m in self._media_records.values() if m.is_sensitive)})"
        )
