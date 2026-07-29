"""LoRA adapter implementation for ClearThread (R37).

Implements LoRA adapter loading, weight configuration, composition,
and persona management for text, vision, and image analysis.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class LoRAFormat(str, Enum):
    """LoRA adapter file formats."""

    SAFETENSORS = "safetensors"
    GGUF = "gguf"


class LoRAType(str, Enum):
    """Types of LoRA adapters."""

    TEXT = "text"
    VISION = "vision"
    IMAGE = "image"


class LoRATask(str, Enum):
    """LoRA task types."""

    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"


@dataclass
class LoRAAdapter:
    """A single LoRA adapter."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    adapter_type: LoRAType = LoRAType.TEXT
    format: LoRAFormat = LoRAFormat.SAFETENSORS
    file_path: str = ""
    base_model: str = ""
    weight: float = 1.0  # Range [0.0, 1.0]
    task: LoRATask = LoRATask.CLASSIFICATION
    dimension: int = 0
    rank: int = 0
    training_data_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    model_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # Constraints
    MIN_WEIGHT = 0.0
    MAX_WEIGHT = 1.0

    def __post_init__(self):
        """Validate constraints."""
        if self.weight < self.MIN_WEIGHT:
            self.weight = self.MIN_WEIGHT
        if self.weight > self.MAX_WEIGHT:
            self.weight = self.MAX_WEIGHT

    @property
    def is_active(self) -> bool:
        """Check if adapter is active (weight > 0)."""
        return self.weight > 0

    def apply_weight(self, new_weight: float) -> None:
        """Apply a new weight to the adapter.

        Args:
            new_weight: New weight value (0.0 to 1.0).
        """
        self.weight = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, new_weight))
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "adapter_type": self.adapter_type.value,
            "format": self.format.value,
            "file_path": self.file_path,
            "base_model": self.base_model,
            "weight": self.weight,
            "task": self.task.value,
            "dimension": self.dimension,
            "rank": self.rank,
            "training_data_count": self.training_data_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model_version": self.model_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoRAAdapter:
        """Deserialize from dictionary."""

        def parse_datetime(val):
            if val is None:
                return datetime.utcnow()
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        adapter_type_val = data.get("adapter_type", "text")
        if isinstance(adapter_type_val, str):
            try:
                adapter_type = LoRAType(adapter_type_val)
            except ValueError:
                adapter_type = LoRAType.TEXT
        else:
            adapter_type = adapter_type_val

        format_val = data.get("format", "safetensors")
        if isinstance(format_val, str):
            try:
                fmt = LoRAFormat(format_val)
            except ValueError:
                fmt = LoRAFormat.SAFETENSORS
        else:
            fmt = fmt

        task_val = data.get("task", "classification")
        if isinstance(task_val, str):
            try:
                task = LoRATask(task_val)
            except ValueError:
                task = LoRATask.CLASSIFICATION
        else:
            task = task_val

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            name=data.get("name", ""),
            adapter_type=adapter_type,
            format=fmt,
            file_path=data.get("file_path", ""),
            base_model=data.get("base_model", ""),
            weight=data.get("weight", 1.0),
            task=task,
            dimension=data.get("dimension", 0),
            rank=data.get("rank", 0),
            training_data_count=data.get("training_data_count", 0),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
            model_version=data.get("model_version", ""),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LoRAAdapter(id={self.id}, name={self.name}, "
            f"type={self.adapter_type.value}, weight={self.weight})"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality by ID."""
        if not isinstance(other, LoRAAdapter):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)


@dataclass
class LoRAComposition:
    """A composition of multiple LoRA adapters."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    adapters: list[LoRAAdapter] = field(default_factory=list)
    composition_formula: str = "base_output + sum(weight_i * lora_i_output)"
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_weight(self) -> float:
        """Calculate total weight of all adapters."""
        return sum(a.weight for a in self.adapters)

    @property
    def effective_weight(self) -> float:
        """Calculate effective weight (average)."""
        if not self.adapters:
            return 0.0
        return self.total_weight / len(self.adapters)

    def add_adapter(self, adapter: LoRAAdapter) -> None:
        """Add an adapter to the composition.

        Args:
            adapter: The LoRA adapter to add.
        """
        if adapter not in self.adapters:
            self.adapters.append(adapter)

    def remove_adapter(self, adapter_id: UUID) -> bool:
        """Remove an adapter from the composition.

        Args:
            adapter_id: The adapter ID to remove.

        Returns:
            True if removed.
        """
        for i, adapter in enumerate(self.adapters):
            if adapter.id == adapter_id:
                self.adapters.pop(i)
                return True
        return False

    def get_adapters_by_type(self, adapter_type: LoRAType) -> list[LoRAAdapter]:
        """Get adapters filtered by type.

        Args:
            adapter_type: The type to filter by.

        Returns:
            List of matching adapters.
        """
        return [a for a in self.adapters if a.adapter_type == adapter_type]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "adapters": [a.to_dict() for a in self.adapters],
            "composition_formula": self.composition_formula,
            "total_weight": self.total_weight,
            "effective_weight": self.effective_weight,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Persona:
    """A saved persona configuration."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""  # Max 120 characters
    description: str = ""
    base_model: str = "qwen2.5-7b"
    text_adapters: list[LoRAAdapter] = field(default_factory=list)
    vision_adapter: LoRAAdapter | None = None
    image_adapter: LoRAAdapter | None = None
    config: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Constraints
    MAX_NAME_LEN = 120
    DEFAULT_CONFIG = {
        "temperature": 0.7,
        "context_length": 4096,
        "max_evidence_window": 50,
        "prompt_version": "v2.1",
    }

    def __post_init__(self):
        """Validate constraints."""
        if len(self.name) > self.MAX_NAME_LEN:
            self.name = self.name[: self.MAX_NAME_LEN]
        if not self.config:
            self.config = dict(self.DEFAULT_CONFIG)

    def add_text_adapter(self, adapter: LoRAAdapter) -> None:
        """Add a text adapter to the persona.

        Args:
            adapter: The text LoRA adapter.
        """
        if adapter not in self.text_adapters:
            self.text_adapters.append(adapter)
            self.updated_at = datetime.utcnow()

    def set_vision_adapter(self, adapter: LoRAAdapter) -> None:
        """Set the vision adapter for the persona.

        Args:
            adapter: The vision LoRA adapter.
        """
        self.vision_adapter = adapter
        self.updated_at = datetime.utcnow()

    def set_image_adapter(self, adapter: LoRAAdapter) -> None:
        """Set the image adapter for the persona.

        Args:
            adapter: The image LoRA adapter.
        """
        self.image_adapter = adapter
        self.updated_at = datetime.utcnow()

    def get_effective_config(self) -> dict[str, Any]:
        """Get the effective configuration with defaults.

        Returns:
            Configuration dictionary.
        """
        config = dict(self.DEFAULT_CONFIG)
        config.update(self.config)
        return config

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "base_model": self.base_model,
            "text_adapters": [a.to_dict() for a in self.text_adapters],
            "vision_adapter": self.vision_adapter.to_dict() if self.vision_adapter else None,
            "image_adapter": self.image_adapter.to_dict() if self.image_adapter else None,
            "config": self.config,
            "provenance": self.provenance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Persona:
        """Deserialize from dictionary."""

        def parse_datetime(val):
            if val is None:
                return datetime.utcnow()
            if isinstance(val, datetime):
                return val
            return datetime.fromisoformat(val)

        def parse_adapter(data_dict):
            if data_dict is None:
                return None
            return LoRAAdapter.from_dict(data_dict)

        text_adapters = [LoRAAdapter.from_dict(a) for a in data.get("text_adapters", [])]
        vision_adapter = parse_adapter(data.get("vision_adapter"))
        image_adapter = parse_adapter(data.get("image_adapter"))

        return cls(
            id=data.get("id", UUID(data["id"]) if isinstance(data.get("id"), str) else uuid4()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            base_model=data.get("base_model", "qwen2.5-7b"),
            text_adapters=text_adapters,
            vision_adapter=vision_adapter,
            image_adapter=image_adapter,
            config=data.get("config", {}),
            provenance=data.get("provenance", {}),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Persona(id={self.id}, name={self.name}, "
            f"base={self.base_model}, text_adapters={len(self.text_adapters)})"
        )


class LoRAStore:
    """Storage and management for LoRA adapters and personas."""

    def __init__(self, models_dir: Path | str = "./models"):
        """Initialize the LoRA store.

        Args:
            models_dir: Directory for storing LoRA models.
        """
        self.models_dir = Path(models_dir)
        self._adapters: dict[str, LoRAAdapter] = {}
        self._compositions: dict[str, LoRAComposition] = {}
        self._personas: dict[str, Persona] = {}
        self._adapter_paths: dict[str, str] = {}  # adapter_id -> file_path

        # Create subdirectories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        (self.models_dir / "text").mkdir(exist_ok=True)
        (self.models_dir / "vision").mkdir(exist_ok=True)
        (self.models_dir / "image").mkdir(exist_ok=True)
        (self.models_dir / "personas").mkdir(exist_ok=True)

    def add_adapter(self, adapter: LoRAAdapter) -> str:
        """Add an adapter to the store.

        Args:
            adapter: The LoRA adapter to add.

        Returns:
            The adapter ID as string.
        """
        key = str(adapter.id)
        self._adapters[key] = adapter
        self._adapter_paths[key] = adapter.file_path
        logger.info("Added LoRA adapter: %s (%s)", adapter.name, adapter.adapter_type.value)
        return key

    def get_adapter(self, adapter_id: UUID | str) -> LoRAAdapter | None:
        """Get an adapter by ID.

        Args:
            adapter_id: The adapter ID.

        Returns:
            The LoRAAdapter or None.
        """
        key = str(adapter_id) if not isinstance(adapter_id, UUID) else str(adapter_id)
        return self._adapters.get(key)

    def get_adapters_by_type(self, adapter_type: LoRAType) -> list[LoRAAdapter]:
        """Get all adapters of a specific type.

        Args:
            adapter_type: The type to filter by.

        Returns:
            List of matching adapters.
        """
        return [a for a in self._adapters.values() if a.adapter_type == adapter_type]

    def get_active_adapters(self) -> list[LoRAAdapter]:
        """Get all active adapters (weight > 0).

        Returns:
            List of active adapters.
        """
        return [a for a in self._adapters.values() if a.is_active]

    def compose_adapters(
        self,
        adapter_ids: list[UUID | str],
        name: str = "Custom Composition",
    ) -> LoRAComposition:
        """Compose multiple adapters into a single composition.

        Args:
            adapter_ids: IDs of adapters to compose.
            name: Composition name.

        Returns:
            The LoRAComposition.
        """
        composition = LoRAComposition(name=name)

        for aid in adapter_ids:
            adapter = self.get_adapter(aid)
            if adapter:
                composition.add_adapter(adapter)

        self._compositions[str(composition.id)] = composition
        return composition

    def add_persona(self, persona: Persona) -> str:
        """Add a persona to the store.

        Args:
            persona: The persona to add.

        Returns:
            The persona ID as string.
        """
        key = str(persona.id)
        self._personas[key] = persona
        logger.info("Added persona: %s", persona.name)
        return key

    def get_persona(self, persona_id: UUID | str) -> Persona | None:
        """Get a persona by ID.

        Args:
            persona_id: The persona ID.

        Returns:
            The Persona or None.
        """
        key = str(persona_id) if not isinstance(persona_id, UUID) else str(persona_id)
        return self._personas.get(key)

    def get_all_personas(self) -> list[Persona]:
        """Get all personas.

        Returns:
            List of all personas.
        """
        return list(self._personas.values())

    def switch_persona(self, persona_id: UUID | str) -> bool:
        """Switch to a specific persona (activate its adapters).

        Args:
            persona_id: The persona ID to switch to.

        Returns:
            True if switched.
        """
        persona = self.get_persona(persona_id)
        if persona:
            # Activate all text adapters
            for adapter in persona.text_adapters:
                if adapter in self._adapters:
                    self._adapters[str(adapter.id)].weight = 1.0
            return True
        return False

    def blend_personas(
        self,
        persona_ids: list[UUID | str],
        weights: dict[str, float] | None = None,
    ) -> Persona:
        """Blend multiple personas into a new one.

        Args:
            persona_ids: IDs of personas to blend.
            weights: Optional weights for each persona.

        Returns:
            The blended Persona.
        """
        if weights is None:
            weights = {str(pid): 1.0 / len(persona_ids) for pid in persona_ids}

        blended = Persona(
            name="Blended Persona",
            base_model="qwen2.5-7b",
            config=dict(Persona.DEFAULT_CONFIG),
        )

        for pid in persona_ids:
            persona = self.get_persona(pid)
            if persona:
                for adapter in persona.text_adapters:
                    new_adapter = LoRAAdapter(
                        name=f"{adapter.name}_blended",
                        adapter_type=adapter.adapter_type,
                        weight=weights.get(str(pid), 0.5) * adapter.weight,
                        task=adapter.task,
                        base_model=adapter.base_model,
                    )
                    blended.add_text_adapter(new_adapter)

        return blended

    def save_persona_to_file(self, persona: Persona, path: Path | str | None = None) -> Path:
        """Save a persona configuration to a JSON file.

        Args:
            persona: The persona to save.
            path: Optional output path.

        Returns:
            Path to the saved file.
        """
        if path is None:
            path = self.models_dir / "personas" / f"{persona.name}.json"

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = persona.to_dict()
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

        logger.info("Saved persona to %s", path)
        return path

    def load_persona_from_file(self, path: Path | str) -> Persona:
        """Load a persona configuration from a JSON file.

        Args:
            path: Path to the persona file.

        Returns:
            The loaded Persona.
        """
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        persona = Persona.from_dict(data)
        self.add_persona(persona)
        return persona

    def get_adapter_count(self) -> int:
        """Get total adapter count.

        Returns:
            Number of adapters.
        """
        return len(self._adapters)

    def get_persona_count(self) -> int:
        """Get total persona count.

        Returns:
            Number of personas.
        """
        return len(self._personas)

    def to_dict(self) -> dict[str, Any]:
        """Serialize store state."""
        return {
            "adapter_count": len(self._adapters),
            "composition_count": len(self._compositions),
            "persona_count": len(self._personas),
            "active_adapters": len(self.get_active_adapters()),
            "models_dir": str(self.models_dir),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LoRAStore(adapters={len(self._adapters)}, "
            f"personas={len(self._personas)}, "
            f"active={len(self.get_active_adapters())})"
        )


# Predefined Text LoRA adapters (from design.md)
TEXT_LORA_PRESETS = {
    "therapy_focused": {
        "name": "therapy_focused",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.CLASSIFICATION,
        "weight": 0.9,
        "description": "Therapy-focused analysis with reflection emphasis",
    },
    "neutral_tone": {
        "name": "neutral_tone",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.CLASSIFICATION,
        "weight": 0.8,
        "description": "Neutral tone analysis without bias",
    },
    "growth_bias": {
        "name": "growth_bias",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.CLASSIFICATION,
        "weight": 0.85,
        "description": "Growth-oriented analysis emphasizing positive patterns",
    },
    "positive_framing": {
        "name": "positive_framing",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.SUMMARIZATION,
        "weight": 0.75,
        "description": "Positive framing for summaries",
    },
    "detail_oriented": {
        "name": "detail_oriented",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.CLASSIFICATION,
        "weight": 0.9,
        "description": "Detail-oriented deep analysis",
    },
    "wider_context": {
        "name": "wider_context",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.EMBEDDING,
        "weight": 0.6,
        "description": "Wider context window for deep analysis",
    },
    "reflection_questions": {
        "name": "reflection_questions",
        "adapter_type": LoRAType.TEXT,
        "task": LoRATask.REASONING,
        "weight": 0.7,
        "description": "Optimized for reflection question generation",
    },
}

# Predefined Vision LoRA adapters
VISION_LORA_PRESETS = {
    "participant_recognition": {
        "name": "participant_recognition",
        "adapter_type": LoRAType.VISION,
        "task": LoRATask.CLASSIFICATION,
        "weight": 0.9,
        "description": "Participant recognition in images",
    },
}

# Predefined Image LoRA adapters
IMAGE_LORA_PRESETS = {
    "style_reconstruction": {
        "name": "style_reconstruction",
        "adapter_type": LoRAType.IMAGE,
        "task": LoRATask.SUMMARIZATION,
        "weight": 0.85,
        "description": "Visual style reconstruction",
    },
}


def get_text_lora_presets() -> dict[str, dict[str, Any]]:
    """Get all text LoRA presets.

    Returns:
        Dictionary of preset name to config.
    """
    return dict(TEXT_LORA_PRESETS)


def get_vision_lora_presets() -> dict[str, dict[str, Any]]:
    """Get all vision LoRA presets.

    Returns:
        Dictionary of preset name to config.
    """
    return dict(VISION_LORA_PRESETS)


def get_image_lora_presets() -> dict[str, dict[str, Any]]:
    """Get all image LoRA presets.

    Returns:
        Dictionary of preset name to config.
    """
    return dict(IMAGE_LORA_PRESETS)
