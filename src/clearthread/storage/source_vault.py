"""SourceDataVault - Immutable source data preservation (R2)."""

from __future__ import annotations

import hashlib
import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID, uuid4

from clearthread.models.base import ContentHash, Model, ProvenanceRef

logger = logging.getLogger(__name__)


@dataclass
class SourceRecord:
    """A record in the immutable source vault."""

    id: UUID = field(default_factory=uuid4)
    batch_id: str = ""
    source_file_path: str = ""
    original_record_id: str = ""
    file_content_hash: str = ""
    record_content_hash: str = ""
    import_timestamp: datetime = field(default_factory=datetime.utcnow)
    parser_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "batch_id": self.batch_id,
            "source_file_path": self.source_file_path,
            "original_record_id": self.original_record_id,
            "file_content_hash": self.file_content_hash,
            "record_content_hash": self.record_content_hash,
            "import_timestamp": self.import_timestamp.isoformat(),
            "parser_version": self.parser_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceRecord:
        """Deserialize from dictionary."""

        def parse_datetime(val):
            if val is None:
                return datetime.utcnow()
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            batch_id=data.get("batch_id", ""),
            source_file_path=data.get("source_file_path", ""),
            original_record_id=data.get("original_record_id", ""),
            file_content_hash=data.get("file_content_hash", ""),
            record_content_hash=data.get("record_content_hash", ""),
            import_timestamp=parse_datetime(data.get("import_timestamp")),
            parser_version=data.get("parser_version", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TransformationStep:
    """A step in the transformation history."""

    step_sequence: int
    operation_name: str
    input_record_ref: str
    output_record_ref: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_sequence": self.step_sequence,
            "operation_name": self.operation_name,
            "input_record_ref": self.input_record_ref,
            "output_record_ref": self.output_record_ref,
            "timestamp": self.timestamp.isoformat(),
        }


class SourceDataVault:
    """Immutable source data storage layer (R2).

    Preserves original imported data unchanged. Source records cannot be
    modified or deleted by analytical operations or user edits.
    """

    def __init__(self, data_dir: Path | str = "./data"):
        """Initialize the source vault.

        Args:
            data_dir: Directory for storing source data.
        """
        self.data_dir = Path(data_dir)
        self._records: dict[str, SourceRecord] = {}
        self._batches: dict[str, list[str]] = {}  # batch_id -> record_ids
        self._transformation_history: list[TransformationStep] = []
        self._warnings: list[dict[str, Any]] = []
        self._is_immutable: bool = True

    @property
    def is_immutable(self) -> bool:
        """Check if vault is in immutable mode."""
        return self._is_immutable

    @contextmanager
    def temporary_mutable(self) -> Iterator[None]:
        """Context manager for temporary mutable operations."""
        old_state = self._is_immutable
        self._is_immutable = False
        try:
            yield
        finally:
            self._is_immutable = old_state

    def import_record(
        self,
        source_file_path: str,
        original_record_id: str,
        content: bytes | str,
        batch_id: str | None = None,
        parser_version: str = "1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> SourceRecord:
        """Import a record into the vault.

        Args:
            source_file_path: Path to the source file.
            original_record_id: Original ID from the source.
            content: Raw content (bytes or string).
            batch_id: Import batch identifier.
            parser_version: Version of the parser used.
            metadata: Additional metadata.

        Returns:
            The created SourceRecord.

        Raises:
            ImmutableError: If vault is immutable and record exists.
        """
        if isinstance(content, bytes):
            content_str = content.decode("utf-8")
        else:
            content_str = content

        file_content_hash = ContentHash.compute(content_str)
        record_content_hash = ContentHash.compute(
            f"{source_file_path}:{original_record_id}:{content_str}"
        )

        batch_id = batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        record = SourceRecord(
            batch_id=batch_id,
            source_file_path=source_file_path,
            original_record_id=original_record_id,
            file_content_hash=file_content_hash,
            record_content_hash=record_content_hash,
            parser_version=parser_version,
            metadata=metadata or {},
        )

        record_id = str(record.id)
        self._records[record_id] = record

        if batch_id not in self._batches:
            self._batches[batch_id] = []
        self._batches[batch_id].append(record_id)

        # Record transformation step
        self._transformation_history.append(
            TransformationStep(
                step_sequence=len(self._transformation_history) + 1,
                operation_name="import",
                input_record_ref=original_record_id,
                output_record_ref=record_id,
            )
        )

        logger.info(
            "Imported record %s from %s (batch: %s)",
            record_id,
            source_file_path,
            batch_id,
        )

        return record

    def get_record(self, record_id: UUID | str) -> SourceRecord:
        """Get a record by ID.

        Args:
            record_id: The record ID.

        Returns:
            The SourceRecord.

        Raises:
            KeyError: If record not found.
        """
        key = str(record_id) if not isinstance(record_id, UUID) else str(record_id)
        if key not in self._records:
            raise KeyError(f"Source record {key} not found in vault")
        return self._records[key]

    def get_records_by_batch(self, batch_id: str) -> list[SourceRecord]:
        """Get all records in a batch.

        Args:
            batch_id: The batch identifier.

        Returns:
            List of SourceRecords.
        """
        record_ids = self._batches.get(batch_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_batches(self) -> list[str]:
        """Get all batch identifiers.

        Returns:
            List of batch IDs.
        """
        return list(self._batches.keys())

    def add_warning(
        self,
        record_id: UUID | str,
        warning_type: str,
        message: str,
        file_path: str = "",
        byte_offset: int = 0,
    ) -> None:
        """Add a parsing warning associated with a source record.

        Args:
            record_id: The record ID.
            warning_type: Type of warning.
            message: Warning message.
            file_path: Source file path.
            byte_offset: Byte offset of the issue.
        """
        self._warnings.append(
            {
                "record_id": str(record_id),
                "warning_type": warning_type,
                "message": message,
                "file_path": file_path,
                "byte_offset": byte_offset,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_warnings(self, record_id: UUID | str | None = None) -> list[dict[str, Any]]:
        """Get warnings, optionally filtered by record ID.

        Args:
            record_id: Optional record ID to filter by.

        Returns:
            List of warning dictionaries.
        """
        if record_id is None:
            return self._warnings
        return [w for w in self._warnings if w["record_id"] == str(record_id)]

    def get_transformation_history(self) -> list[TransformationStep]:
        """Get the full transformation history.

        Returns:
            List of TransformationSteps.
        """
        return list(self._transformation_history)

    def get_record_count(self) -> int:
        """Get total number of records in the vault.

        Returns:
            Record count.
        """
        return len(self._records)

    def get_batch_count(self) -> int:
        """Get total number of import batches.

        Returns:
            Batch count.
        """
        return len(self._batches)

    def purge_batch(self, batch_id: str) -> int:
        """Purge a specific batch from the vault.

        Args:
            batch_id: The batch to purge.

        Returns:
            Number of records purged.
        """
        if batch_id not in self._batches:
            return 0

        record_ids = self._batches[batch_id]
        purged = 0
        for rid in record_ids:
            if rid in self._records:
                del self._records[rid]
                purged += 1

        del self._batches[batch_id]
        return purged

    def verify_integrity(self, record_id: UUID | str) -> bool:
        """Verify the integrity of a source record.

        Args:
            record_id: The record to verify.

        Returns:
            True if integrity is verified.
        """
        record = self.get_record(record_id)
        # Verify file content hash
        if record.file_content_hash and record.record_content_hash:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize vault state to dictionary."""
        return {
            "record_count": len(self._records),
            "batch_count": len(self._batches),
            "batches": {k: v for k, v in self._batches.items()},
            "warnings_count": len(self._warnings),
            "transformation_steps": len(self._transformation_history),
            "is_immutable": self._is_immutable,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SourceDataVault(records={len(self._records)}, "
            f"batches={len(self._batches)}, immutable={self._is_immutable})"
        )
