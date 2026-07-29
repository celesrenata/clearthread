"""Visual persona composition for ClearThread."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from clearthread.models.lora import (
    LoRAAdapter,
    LoRAComposition,
    Persona,
    LoRAType,
)
from clearthread.models.qwen_vision import QwenVisionModelProvider
from clearthread.models.wan_image import WANImageModelProvider

logger = logging.getLogger("clearthread.visual_persona")


class VisualPersona:
    """A composed visual persona combining Qwen vision + WAN image.

    Attributes:
        id: Unique persona ID.
        name: Persona name.
        description: Persona description.
        text_adapters: Text LoRA adapters.
        vision_adapter: Qwen vision LoRA adapter.
        image_adapter: WAN image LoRA adapter.
        config: Configuration dictionary.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        text_adapters: list[LoRAAdapter] | None = None,
        vision_adapter: LoRAAdapter | None = None,
        image_adapter: LoRAAdapter | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.text_adapters = text_adapters or []
        self.vision_adapter = vision_adapter
        self.image_adapter = image_adapter
        self.config = config or {
            "temperature": 0.7,
            "context_length": 4096,
            "max_evidence_window": 50,
            "prompt_version": "v2.1",
        }

    def get_effective_config(self) -> dict[str, Any]:
        """Get the effective configuration for this persona.

        Returns:
            Effective configuration dictionary.
        """
        config = dict(self.config)

        # Add LoRA weights
        if self.vision_adapter:
            config["vision_weight"] = self.vision_adapter.weight
        if self.image_adapter:
            config["image_weight"] = self.image_adapter.weight

        return config

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Serialized dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "text_adapters": [
                a.to_dict() for a in self.text_adapters
            ],
            "vision_adapter": (
                self.vision_adapter.to_dict() if self.vision_adapter
                else None
            ),
            "image_adapter": (
                self.image_adapter.to_dict() if self.image_adapter
                else None
            ),
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VisualPersona:
        """Deserialize from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            VisualPersona instance.
        """
        def parse_adapter(data_dict: dict[str, Any]) -> LoRAAdapter:
            return LoRAAdapter.from_dict(data_dict)

        text_adapters = [
            parse_adapter(a) for a in data.get("text_adapters", [])
        ]

        vision_adapter = None
        if data.get("vision_adapter"):
            vision_adapter = parse_adapter(data["vision_adapter"])

        image_adapter = None
        if data.get("image_adapter"):
            image_adapter = parse_adapter(data["image_adapter"])

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            text_adapters=text_adapters,
            vision_adapter=vision_adapter,
            image_adapter=image_adapter,
            config=data.get("config", {}),
        )


class VisualPersonaComposer:
    """Compose visual personas from Qwen + WAN components.

    Attributes:
        qwen_provider: Qwen vision model provider.
        wan_provider: WAN image model provider.
        personas: Dictionary of composed personas.
    """

    def __init__(
        self,
        qwen_provider: QwenVisionModelProvider | None = None,
        wan_provider: WANImageModelProvider | None = None,
    ) -> None:
        self.qwen_provider = qwen_provider or QwenVisionModelProvider()
        self.wan_provider = wan_provider or WANImageModelProvider()
        self.personas: dict[str, VisualPersona] = {}

    def compose(
        self,
        name: str,
        text_adapters: list[LoRAAdapter],
        vision_adapter: LoRAAdapter,
        image_adapter: LoRAAdapter,
        config: dict[str, Any] | None = None,
    ) -> VisualPersona:
        """Compose a new visual persona.

        Args:
            name: Persona name.
            text_adapters: Text LoRA adapters.
            vision_adapter: Qwen vision adapter.
            image_adapter: WAN image adapter.
            config: Optional configuration.

        Returns:
            Composed VisualPersona.
        """
        persona = VisualPersona(
            id=name.lower().replace(" ", "_"),
            name=name,
            text_adapters=text_adapters,
            vision_adapter=vision_adapter,
            image_adapter=image_adapter,
            config=config,
        )
        self.personas[persona.id] = persona
        return persona

    def get_persona(self, persona_id: str) -> VisualPersona | None:
        """Get a persona by ID.

        Args:
            persona_id: Persona ID.

        Returns:
            VisualPersona or None.
        """
        return self.personas.get(persona_id)

    def get_all_personas(self) -> list[VisualPersona]:
        """Get all personas.

        Returns:
            List of all personas.
        """
        return list(self.personas.values())

    def blend_personas(
        self,
        persona_ids: list[str],
        weights: list[float] | None = None,
    ) -> VisualPersona:
        """Blend multiple personas into one.

        Args:
            persona_ids: IDs of personas to blend.
            weights: Optional weights for each persona.

        Returns:
            Blended VisualPersona.
        """
        if not persona_ids:
            raise ValueError("At least one persona ID required")

        personas = [
            self.personas[pid] for pid in persona_ids
            if pid in self.personas
        ]

        if not personas:
            raise ValueError("No valid personas to blend")

        if weights is None:
            weights = [1.0 / len(personas)] * len(personas)

        # Blend text adapters
        blended_text = self._blend_adapters(
            [p.text_adapters for p in personas], weights
        )

        # Blend vision adapters
        blended_vision = self._blend_single_adapter(
            [p.vision_adapter for p in personas if p.vision_adapter],
            weights,
        )

        # Blend image adapters
        blended_image = self._blend_single_adapter(
            [p.image_adapter for p in personas if p.image_adapter],
            weights,
        )

        return VisualPersona(
            id=f"blend_{'_'.join(persona_ids)}",
            name=f"Blend of {', '.join(persona_ids)}",
            text_adapters=blended_text,
            vision_adapter=blended_vision,
            image_adapter=blended_image,
        )

    def _blend_adapters(
        self,
        adapter_lists: list[list[LoRAAdapter]],
        weights: list[float],
    ) -> list[LoRAAdapter]:
        """Blend adapter lists.

        Args:
            adapter_lists: Lists of adapters to blend.
            weights: Weights for each list.

        Returns:
            Blended adapter list.
        """
        # Simplified blending
        result = []
        for adapters, weight in zip(adapter_lists, weights):
            for adapter in adapters:
                result.append(LoRAAdapter(
                    id=adapter.id,
                    name=adapter.name,
                    adapter_type=adapter.adapter_type,
                    weight=adapter.weight * weight,
                ))
        return result

    def _blend_single_adapter(
        self,
        adapters: list[LoRAAdapter | None],
        weights: list[float],
    ) -> LoRAAdapter | None:
        """Blend single adapters.

        Args:
            adapters: Adapters to blend.
            weights: Weights.

        Returns:
            Blended adapter or None.
        """
        valid = [a for a in adapters if a is not None]
        if not valid:
            return None

        total_weight = sum(weights[:len(valid)])
        if total_weight == 0:
            return valid[0]

        blended = valid[0].copy()
        blended.weight = valid[0].weight * (weights[0] / total_weight)
        return blended
