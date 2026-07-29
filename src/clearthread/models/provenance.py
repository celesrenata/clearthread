"""ProvenanceRecord model for ClearThread (R13)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from clearthread.models.base import Model


class ProvenanceStepType(str, Enum):
    """Types of processing steps in provenance chain."""

    IMPORT = "import"
    NORMALIZE = "normalize"
    VALIDATE = "validate"
    EMBED = "embed"
    ANALYZE = "analyze"
    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    USER_EDIT = "user_edit"
    RE_ANALYZE = "re_analyze"


@dataclass
class ProvenanceStep:
    """A single step in the provenance chain."""

    step_sequence: int
    operation_name: str
    input_record_ref: str
    output_record_ref: str
    timestamp: datetime
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_sequence": self.step_sequence,
            "operation_name": self.operation_name,
            "input_record_ref": self.input_record_ref,
            "output_record_ref": self.output_record_ref,
            "timestamp": self.timestamp.isoformat(),
            "parameters": self.parameters,
        }


@dataclass
class ProvenanceRecord(Model):
    """Provenance tracking record (R13).

    Tracks the origin, transformation, and derivation of every piece of data.
    """

    # Core identity
    id: UUID = field(default_factory=uuid4)
    run_id: str = ""
    analysis_type: str = ""

    # Model info
    model_name: str = ""
    model_version: str = ""
    prompt_version: str = ""
    parser_version: str = ""

    # Source references
    source_record_references: list[str] = field(default_factory=list)

    # Retrieval
    retrieval_query: str = ""
    retrieved_evidence_ids: list[str] = field(default_factory=list)

    # Generation
    generation_timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0  # 0.0 to 1.0

    # User review
    user_review_state: str = "unreviewed"  # unreviewed, confirmed, disputed, corrected
    user_corrections: list[str] = field(default_factory=list)

    # Versioning
    superseded_by: UUID | None = None
    superseded_versions: list[UUID] = field(default_factory=list)

    # Validation
    validation_status: str = "pass"  # pass, fail
    validation_attempts: int = 1
    schema_version: str = "v1"
    validation_failures: list[str] = field(default_factory=list)

    # Processing chain
    processing_steps: list[ProvenanceStep] = field(default_factory=list)

    def add_step(self, step: ProvenanceStep) -> None:
        """Add a processing step to the chain."""
        self.processing_steps.append(step)
        self.processing_steps.sort(key=lambda s: s.step_sequence)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "run_id": self.run_id,
            "analysis_type": self.analysis_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "parser_version": self.parser_version,
            "source_record_references": self.source_record_references,
            "retrieval_query": self.retrieval_query,
            "retrieved_evidence_ids": self.retrieved_evidence_ids,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "confidence_score": self.confidence_score,
            "user_review_state": self.user_review_state,
            "user_corrections": self.user_corrections,
            "superseded_by": str(self.superseded_by) if self.superseded_by else None,
            "superseded_versions": [str(v) for v in self.superseded_versions],
            "validation_status": self.validation_status,
            "validation_attempts": self.validation_attempts,
            "schema_version": self.schema_version,
            "validation_failures": self.validation_failures,
            "processing_steps": [step.to_dict() for step in self.processing_steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceRecord:
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

        def parse_step(step_data):
            return ProvenanceStep(
                step_sequence=step_data["step_sequence"],
                operation_name=step_data["operation_name"],
                input_record_ref=step_data["input_record_ref"],
                output_record_ref=step_data["output_record_ref"],
                timestamp=parse_datetime(step_data["timestamp"]),
                parameters=step_data.get("parameters", {}),
            )

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            run_id=data.get("run_id", ""),
            analysis_type=data.get("analysis_type", ""),
            model_name=data.get("model_name", ""),
            model_version=data.get("model_version", ""),
            prompt_version=data.get("prompt_version", ""),
            parser_version=data.get("parser_version", ""),
            source_record_references=data.get("source_record_references", []),
            retrieval_query=data.get("retrieval_query", ""),
            retrieved_evidence_ids=data.get("retrieved_evidence_ids", []),
            generation_timestamp=parse_datetime(data.get("generation_timestamp")) or datetime.utcnow(),
            confidence_score=data.get("confidence_score", 0.0),
            user_review_state=data.get("user_review_state", "unreviewed"),
            user_corrections=data.get("user_corrections", []),
            superseded_by=parse_uuid(data.get("superseded_by")),
            superseded_versions=[parse_uuid(v) for v in data.get("superseded_versions", [])],
            validation_status=data.get("validation_status", "pass"),
            validation_attempts=data.get("validation_attempts", 1),
            schema_version=data.get("schema_version", "v1"),
            validation_failures=data.get("validation_failures", []),
            processing_steps=[parse_step(s) for s in data.get("processing_steps", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "run_id": self.run_id,
            "analysis_type": self.analysis_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "parser_version": self.parser_version,
            "source_record_references": self.source_record_references,
            "retrieval_query": self.retrieval_query,
            "retrieved_evidence_ids": self.retrieved_evidence_ids,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "confidence_score": self.confidence_score,
            "user_review_state": self.user_review_state,
            "user_corrections": self.user_corrections,
            "superseded_by": str(self.superseded_by) if self.superseded_by else None,
            "superseded_versions": [str(v) for v in self.superseded_versions],
            "validation_status": self.validation_status,
            "validation_attempts": self.validation_attempts,
            "schema_version": self.schema_version,
            "validation_failures": self.validation_failures,
            "processing_steps": [step.to_dict() for step in self.processing_steps],
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProvenanceRecord(id={self.id}, run={self.run_id}, "
            f"type={self.analysis_type}, validation={self.validation_status})"
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
