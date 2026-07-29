"""Base model classes for ClearThread."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4


class ContentCategory(str, Enum):
    """Content type indicators for evidence distinction (R24)."""

    DOCUMENTED_FACT = "documented_fact"
    CALCULATED_PATTERN = "calculated_pattern"
    AI_GENERATED_SUMMARY = "ai_generated_summary"
    USER_SUPPLIED_CONTEXT = "user_supplied_context"
    UNCERTAIN_MISSING = "uncertain_missing"


class UserReviewState(str, Enum):
    """Review states for AI-generated content."""

    UNREVIEWED = "unreviewed"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CORRECTED = "corrected"


class ExclusionState(str, Enum):
    """Exclusion states for messages."""

    INCLUDED = "included"
    EXCLUDED = "excluded"


@dataclass
class ProvenanceRef:
    """Reference to a provenance record."""

    run_id: str
    analysis_type: str
    model_name: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None
    parser_version: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "analysis_type": self.analysis_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "parser_version": self.parser_version,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceRef:
        """Deserialize from dictionary."""
        return cls(
            run_id=data["run_id"],
            analysis_type=data["analysis_type"],
            model_name=data.get("model_name"),
            model_version=data.get("model_version"),
            prompt_version=data.get("prompt_version"),
            parser_version=data.get("parser_version"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("timestamp"), str)
            else data["timestamp"],
        )


@dataclass
class EvidenceReference:
    """A citation linking a Finding to specific source messages."""

    message_id: UUID
    source_id: str
    conversation_id: UUID | None = None
    context_before: list[UUID] = field(default_factory=list)
    context_after: list[UUID] = field(default_factory=list)
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "message_id": str(self.message_id),
            "source_id": self.source_id,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "context_before": [str(mid) for mid in self.context_before],
            "context_after": [str(mid) for mid in self.context_after],
            "excerpt": self.excerpt,
        }


@dataclass
class ContentHash:
    """Content hash tracking for deduplication and change detection."""

    content_hash: str
    source_hash: str
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def compute(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_message(sender: str, timestamp: str, message_text: str) -> str:
        """Compute deduplication hash for a message."""
        raw = f"{sender}:{timestamp}:{message_text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Model(ABC):
    """Base model with common functionality."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize model to dictionary."""
        ...

    @abstractmethod
    def to_json(self) -> str:
        """Serialize model to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Model:
        """Deserialize model from dictionary."""
        ...

    @classmethod
    def from_json(cls, json_str: str) -> Model:
        """Deserialize model from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __eq__(self, other: object) -> bool:
        """Check equality by comparing dictionary representations."""
        if not isinstance(other, type(self)):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        """Hash based on dictionary representation."""
        return hash(self.to_json())


T = TypeVar("T", bound=Model)


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def save(self, record: Model) -> bool:
        """Save a record to storage."""
        ...

    @abstractmethod
    def get(self, record_id: UUID) -> Model | None:
        """Retrieve a record by ID."""
        ...

    @abstractmethod
    def delete(self, record_id: UUID) -> bool:
        """Delete a record by ID."""
        ...

    @abstractmethod
    def exists(self, record_id: UUID) -> bool:
        """Check if a record exists."""
        ...

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> list[Model]:
        """List all records with pagination."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Count total records."""
        ...
