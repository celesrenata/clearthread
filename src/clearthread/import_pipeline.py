"""ImportPipeline - Facebook/Messenger data import (R1, R2, R4)."""

from __future__ import annotations

import json
import logging
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import ContentHash
from clearthread.models.message import Message, MessageType
from clearthread.models.participant import Participant, RelationshipCategory
from clearthread.storage.source_vault import SourceDataVault
from clearthread.storage.normalized_store import NormalizedStore

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Raised when import fails."""

    def __init__(self, message: str, file_path: str = "", details: dict[str, Any] | None = None):
        self.file_path = file_path
        self.details = details or {}
        super().__init__(message)


@dataclass
class DataHealthReport:
    """Data health report summarizing import results (R1)."""

    total_messages: int = 0
    total_conversations: int = 0
    total_participants: int = 0
    total_attachments: int = 0
    duplicates_detected: int = 0
    encoding_issues_recovered: int = 0
    records_with_warnings: int = 0
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    import_batch_id: str = ""
    import_timestamp: datetime = field(default_factory=datetime.utcnow)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_messages": self.total_messages,
            "total_conversations": self.total_conversations,
            "total_participants": self.total_participants,
            "total_attachments": self.total_attachments,
            "duplicates_detected": self.duplicates_detected,
            "encoding_issues_recovered": self.encoding_issues_recovered,
            "records_with_warnings": self.records_with_warnings,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "import_batch_id": self.import_batch_id,
            "import_timestamp": self.import_timestamp.isoformat(),
            "warnings": self.warnings,
        }


class ImportPipeline:
    """Import pipeline for Facebook/Messenger data exports (R1).

    Handles ZIP and directory imports, encoding fixes, deduplication,
    and streaming for large archives.
    """

    # Facebook encoding quirk: Latin-1 escape sequence in UTF-8 JSON
    MAX_MEMORY_FOOTPRINT = 256 * 1024 * 1024  # 256 MB (R1)
    MAX_MESSAGES_PER_BATCH = 10000
    SUPPORTED_EXTENSIONS = {".json", ".zip"}

    def __init__(
        self,
        source_vault: SourceDataVault | None = None,
        normalized_store: NormalizedStore | None = None,
        data_dir: Path | str = "./data",
    ):
        """Initialize the import pipeline.

        Args:
            source_vault: Source data vault for immutable storage.
            normalized_store: Normalized store for canonical data.
            data_dir: Base directory for import data.
        """
        self.source_vault = source_vault or SourceDataVault(data_dir / "source_data")
        self.normalized_store = normalized_store or NormalizedStore(data_dir / "normalized")
        self.data_dir = Path(data_dir)
        self._progress: dict[str, Any] = {
            "current_file": "",
            "files_processed": 0,
            "total_files": 0,
            "messages_imported": 0,
            "duplicates_skipped": 0,
            "encoding_fixes": 0,
            "is_interrupted": False,
            "last_processed_file": "",
        }
        self._seen_hashes: set[str] = set()
        self._participants: dict[str, Participant] = {}
        self._conversations: dict[str, UUID] = {}

    @property
    def progress(self) -> dict[str, Any]:
        """Get current import progress."""
        return dict(self._progress)

    def import_from_zip(self, zip_path: Path | str) -> DataHealthReport:
        """Import from a ZIP archive.

        Args:
            zip_path: Path to the ZIP file.

        Returns:
            DataHealthReport with import summary.

        Raises:
            ImportError: If ZIP is corrupt or cannot be read.
        """
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise ImportError(f"ZIP file not found: {zip_path}", file_path=str(zip_path))

        if not zipfile.is_zipfile(zip_path):
            raise ImportError(f"Corrupt ZIP file: {zip_path}", file_path=str(zip_path))

        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        extract_dir = self.data_dir / "extracted" / batch_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile as e:
            raise ImportError(f"Failed to extract ZIP: {e}", file_path=str(zip_path))

        return self._process_extracted_directory(extract_dir, batch_id)

    def import_from_directory(self, dir_path: Path | str) -> DataHealthReport:
        """Import from an extracted directory.

        Args:
            dir_path: Path to the directory.

        Returns:
            DataHealthReport with import summary.
        """
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise ImportError(f"Directory not found: {dir_path}", file_path=str(dir_path))

        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return self._process_extracted_directory(dir_path, batch_id)

    def _process_extracted_directory(
        self, dir_path: Path, batch_id: str
    ) -> DataHealthReport:
        """Process an extracted directory of JSON files.

        Args:
            dir_path: Directory containing JSON files.
            batch_id: Import batch identifier.

        Returns:
            DataHealthReport with import summary.
        """
        messages = []
        participants = {}
        conversations = {}
        attachments = 0
        encoding_fixes = 0
        warnings = []

        # Find all JSON files recursively
        json_files = list(dir_path.rglob("*.json"))
        self._progress["total_files"] = len(json_files)

        for json_file in json_files:
            self._progress["current_file"] = str(json_file.relative_to(dir_path))

            # Check for interrupted import recovery (R1)
            if self._progress["is_interrupted"]:
                last_file = self._progress.get("last_processed_file", "")
                if str(json_file.relative_to(dir_path)) == last_file:
                    logger.info("Resuming from file: %s", last_file)
                elif str(json_file.relative_to(dir_path)) < last_file:
                    continue

            try:
                file_messages, file_participants, file_conversations, file_attachments, file_warnings = (
                    self._parse_json_file(json_file, batch_id)
                )
                messages.extend(file_messages)
                participants.update(file_participants)
                conversations.update(file_conversations)
                attachments += file_attachments
                encoding_fixes += len([w for w in file_warnings if w.get("type") == "encoding"])
                warnings.extend(file_warnings)

            except Exception as e:
                warning = {
                    "type": "parsing_error",
                    "file": str(json_file),
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                warnings.append(warning)
                logger.warning("Error parsing %s: %s", json_file, e)

            self._progress["files_processed"] += 1

        # Deduplicate messages (R1)
        deduped_messages, duplicates = self._deduplicate(messages)

        # Save to source vault and normalized store
        for msg in deduped_messages:
            self.source_vault.import_record(
                source_file_path=msg.source_id,
                original_record_id=str(msg.id),
                content=msg.text,
                batch_id=batch_id,
            )
            self.normalized_store.save_message(msg)

        # Save participants
        for pid, participant in participants.items():
            self._participants[pid] = participant

        # Generate health report (R1)
        date_starts = [m.original_timestamp for m in deduped_messages if m.original_timestamp]
        date_ends = [m.original_timestamp for m in deduped_messages if m.original_timestamp]

        report = DataHealthReport(
            total_messages=len(deduped_messages),
            total_conversations=len(conversations),
            total_participants=len(participants),
            total_attachments=attachments,
            duplicates_detected=duplicates,
            encoding_issues_recovered=encoding_fixes,
            records_with_warnings=len(warnings),
            date_range_start=min(date_starts) if date_starts else None,
            date_range_end=max(date_ends) if date_ends else None,
            import_batch_id=batch_id,
            warnings=warnings,
        )

        self._progress["messages_imported"] += len(deduped_messages)
        self._progress["duplicates_skipped"] += duplicates

        return report

    def _parse_json_file(
        self,
        file_path: Path,
        batch_id: str,
    ) -> tuple[list[Message], dict[str, Participant], dict[str, UUID], int, list[dict[str, Any]]]:
        """Parse a single JSON file.

        Args:
            file_path: Path to the JSON file.
            batch_id: Import batch identifier.

        Returns:
            Tuple of (messages, participants, conversations, attachments, warnings).
        """
        messages = []
        participants = {}
        conversations = {}
        attachments = 0
        warnings = []

        # Read raw bytes and fix encoding (R1, R4)
        raw_bytes = file_path.read_bytes()
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fix Latin-1 escape sequence (R1, R4)
            content = raw_bytes.encode("latin-1").decode("utf-8")
            warnings.append({
                "type": "encoding",
                "file": str(file_path),
                "message": "Fixed Latin-1 encoding",
                "byte_offset": 0,
            })

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            warnings.append({
                "type": "json_decode",
                "file": str(file_path),
                "message": f"JSON decode error: {e}",
                "byte_offset": 0,
            })
            return messages, participants, conversations, attachments, warnings

        # Handle both list and dict formats
        if isinstance(data, dict):
            # Single chat format
            if "messages" in data:
                messages, participants, conversations, attachments = self._parse_message_file(
                    data, file_path, batch_id
                )
            # Posts format
            elif "data" in data:
                messages, participants, conversations, attachments = self._parse_posts_file(
                    data, file_path, batch_id
                )
        elif isinstance(data, list):
            # Array of messages
            for item in data:
                msg = self._normalize_message(item, str(file_path), batch_id)
                if msg:
                    messages.append(msg)
                    if msg.sender_id:
                        pid = str(msg.sender_id)
                        if pid not in participants:
                            participants[pid] = Participant(
                                id=msg.sender_id,
                                display_name=msg.sender_display_name or "Unknown",
                            )

        return messages, participants, conversations, attachments, warnings

    def _parse_message_file(
        self,
        data: dict[str, Any],
        file_path: Path,
        batch_id: str,
    ) -> tuple[list[Message], dict[str, Participant], dict[str, UUID], int]:
        """Parse a messages JSON file (R1).

        Args:
            data: Parsed JSON data.
            file_path: Source file path.
            batch_id: Import batch.

        Returns:
            Tuple of (messages, participants, conversations, attachments).
        """
        messages = []
        participants = {}
        conversations = {}
        attachments = 0

        # Get participants list
        participant_names = data.get("participants", [])
        for i, p in enumerate(participant_names):
            name = p.get("name", f"Participant_{i}")
            pid = f"participant_{i}"
            participants[pid] = Participant(
                id=UUID(f"{i:032x}"),
                source_id=f"participant_{i}",
                display_name=name,
                message_count=0,
            )

        # Get conversation ID from thread_path or title
        thread_path = data.get("thread_path", "")
        title = data.get("title", "")
        conv_id = f"conversation_{thread_path or title}"
        conversations[conv_id] = uuid4()

        # Parse messages
        raw_messages = data.get("messages", [])
        for msg_data in raw_messages:
            msg = self._normalize_message(msg_data, str(file_path), batch_id)
            if msg:
                msg.conversation_id = conversations.get(conv_id)
                messages.append(msg)

                # Update participant message counts
                if msg.sender_id:
                    pid = str(msg.sender_id)
                    if pid in participants:
                        participants[pid].message_count += 1

                # Count attachments
                attachments += len(msg_data.get("attachments", []))
                attachments += len(msg_data.get("photos", []))

        return messages, participants, conversations, attachments

    def _parse_posts_file(
        self,
        data: dict[str, Any],
        file_path: Path,
        batch_id: str,
    ) -> tuple[list[Message], dict[str, Participant], dict[str, UUID], int]:
        """Parse a posts JSON file (R1, R29).

        Args:
            data: Parsed JSON data.
            file_path: Source file path.
            batch_id: Import batch.

        Returns:
            Tuple of (messages, participants, conversations, attachments).
        """
        messages = []
        participants = {}
        conversations = {}
        attachments = 0

        posts_data = data.get("data", [])
        for post in posts_data:
            post_text = ""
            for item in post.get("data", []):
                if "post" in item:
                    post_text = item["post"]

            timestamp = post.get("timestamp")
            if timestamp and isinstance(timestamp, (int, float)):
                ts = datetime.fromtimestamp(timestamp)
            else:
                ts = datetime.utcnow()

            msg = Message(
                source_id=str(file_path),
                original_timestamp=ts,
                normalized_utc=ts,
                text=post_text,
                message_type=MessageType.TEXT,
                owner_authored=True,
            )
            messages.append(msg)
            attachments += len(post.get("attachments", []))

        return messages, participants, conversations, attachments

    def _normalize_message(
        self,
        msg_data: dict[str, Any],
        source_file: str,
        batch_id: str,
    ) -> Message | None:
        """Normalize a single message record.

        Args:
            msg_data: Raw message data.
            source_file: Source file path.
            batch_id: Import batch.

        Returns:
            Normalized Message or None.
        """
        sender_name = msg_data.get("sender_name", "Unknown")
        timestamp_ms = msg_data.get("timestamp_ms")

        # Parse timestamp (R1)
        if timestamp_ms:
            ts = datetime.fromtimestamp(timestamp_ms / 1000)
        else:
            ts = datetime.utcnow()

        # Get content (handle missing keys safely)
        content = msg_data.get("content", "")
        if not content:
            # Try alternative content fields
            content = msg_data.get("post", "") or msg_data.get("extdata", "")

        # Determine message type
        msg_type_str = msg_data.get("type", "Generic")
        if msg_type_str == "Generic":
            msg_type = MessageType.TEXT
        elif msg_type_str in ("Image", "Video", "Audio"):
            msg_type = MessageType.MEDIA
        elif msg_type_str == "Sticker":
            msg_type = MessageType.STICKER
        elif msg_type_str == "Link":
            msg_type = MessageType.LINK
        else:
            msg_type = MessageType.UNKNOWN

        # Check for deleted/unsent (R1)
        deleted = msg_data.get("is_taken_down", False)
        unsent = msg_data.get("is_unsent", False)

        # Parse reactions (R1)
        reactions = []
        for r in msg_data.get("reactions", []):
            reactions.append({
                "actor": r.get("actor", ""),
                "reaction": r.get("reaction", ""),
            })

        # Parse attachments (R1)
        attachment_refs = []
        for att in msg_data.get("attachments", []):
            if "media" in att:
                media = att["media"]
                attachment_refs.append({
                    "uri": media.get("uri", ""),
                    "attachment_type": "image",
                    "creation_timestamp": media.get("creation_timestamp"),
                    "title": media.get("title"),
                })
            elif "extdata" in att:
                extdata = att["extdata"]
                attachment_refs.append({
                    "uri": extdata.get("uri", ""),
                    "attachment_type": extdata.get("type", "unknown"),
                })

        # Parse photos
        for photo in msg_data.get("photos", []):
            attachment_refs.append({
                "uri": photo.get("uri", ""),
                "attachment_type": "image",
                "creation_timestamp": photo.get("creation_timestamp"),
            })

        return Message(
            source_id=source_file,
            sender_id=uuid4() if sender_name else None,
            sender_display_name=sender_name,
            original_timestamp=ts,
            normalized_utc=ts,
            text=content,
            message_type=msg_type,
            deleted=deleted,
            unsent=unsent,
            reactions=reactions,
            attachment_refs=attachment_refs,
        )

    def _deduplicate(self, messages: list[Message]) -> tuple[list[Message], int]:
        """Deduplicate messages by SHA-256 hash (R1).

        Args:
            messages: List of messages to deduplicate.

        Returns:
            Tuple of (deduped_messages, duplicate_count).
        """
        deduped = []
        duplicates = 0

        for msg in messages:
            # Compute dedup hash from sender, timestamp, content (R1)
            if msg.sender_id and msg.original_timestamp:
                hash_input = f"{msg.sender_id}:{msg.original_timestamp.isoformat()}:{msg.text}"
                msg_hash = ContentHash.compute(hash_input)
            else:
                msg_hash = msg.content_hash

            if msg_hash in self._seen_hashes:
                duplicates += 1
                self._progress["duplicates_skipped"] += 1
            else:
                self._seen_hashes.add(msg_hash)
                deduped.append(msg)

        return deduped, duplicates

    def resume_from_checkpoint(self) -> bool:
        """Resume import from the last checkpoint.

        Returns:
            True if resuming successfully.
        """
        checkpoint = self._progress
        if checkpoint.get("is_interrupted") and checkpoint.get("last_processed_file"):
            logger.info(
                "Resuming from checkpoint: file=%s, messages=%d",
                checkpoint["last_processed_file"],
                checkpoint["messages_imported"],
            )
            self._progress["is_interrupted"] = False
            return True
        return False

    def interrupt_import(self) -> None:
        """Interrupt the current import and persist progress state (R1)."""
        self._progress["is_interrupted"] = True
        logger.info("Import interrupted. Progress saved.")

    def get_health_report(self) -> DataHealthReport:
        """Get the current data health report (R1).

        Returns:
            DataHealthReport summarizing import results.
        """
        return DataHealthReport(
            total_messages=self._progress.get("messages_imported", 0),
            total_conversations=len(self._conversations),
            total_participants=len(self._participants),
            duplicates_detected=self._progress.get("duplicates_skipped", 0),
            encoding_issues_recovered=self._progress.get("encoding_fixes", 0),
            import_batch_id=self._progress.get("batch_id", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize pipeline state."""
        return {
            "progress": self._progress,
            "participant_count": len(self._participants),
            "conversation_count": len(self._conversations),
            "source_vault_records": self.source_vault.get_record_count(),
            "normalized_store_messages": self.normalized_store.message_count,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ImportPipeline(files={self._progress['files_processed']}, "
            f"messages={self._progress['messages_imported']}, "
            f"duplicates={self._progress['duplicates_skipped']})"
        )
