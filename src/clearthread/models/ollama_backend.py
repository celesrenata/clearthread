"""Ollama backend for ClearThread."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from clearthread.models.model_provider import (
    ModelProvider,
    StructuredOutputError,
)
from clearthread.models.lora import LoRAAdapter

logger = logging.getLogger("clearthread.ollama_backend")


class OllamaBackend(ModelProvider):
    """Ollama-based model provider.

    Uses the Ollama REST API for model inference.
    """

    DEFAULT_URL = "http://localhost:11434"

    def __init__(
        self,
        url: str = DEFAULT_URL,
        model_name: str = "qwen2.5:7b",
        timeout: float = 60.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self._client = httpx.Client(base_url=url, timeout=timeout)
        self._active_loras: dict[str, LoRAAdapter] = {}

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Ollama API.

        Args:
            prompt: Input prompt.
            **kwargs: temperature, max_tokens, top_p, stream, etc.

        Returns:
            Generated text.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            **kwargs,
        }

        # Apply active LoRA adapters
        if self._active_loras:
            lora_ids = list(self._active_loras.keys())
            payload["lora"] = lora_ids

        response = self._client.post("/api/generate", json=payload)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "")

    def generate_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Generate structured output using Ollama.

        Args:
            prompt: Input prompt.
            schema: JSON schema for output validation.
            **kwargs: Additional parameters.

        Returns:
            Parsed structured output.

        Raises:
            StructuredOutputError: If output doesn't match schema.
        """
        # Build structured prompt with schema
        structured_prompt = self._build_structured_prompt(prompt, schema)

        payload = {
            "model": self.model_name,
            "prompt": structured_prompt,
            "format": schema,
            "stream": False,
            **kwargs,
        }

        response = self._client.post("/api/generate", json=payload)
        response.raise_for_status()

        result = response.json()
        output = result.get("response", "{}")

        # Validate against schema
        self._validate_structured_output(output, schema)

        return json.loads(output)

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embedding using Ollama.

        Args:
            text: Input text.
            **kwargs: Additional parameters.

        Returns:
            Embedding vector.
        """
        payload = {
            "model": self.model_name,
            "input": text,
            **kwargs,
        }

        response = self._client.post("/api/embed", json=payload)
        response.raise_for_status()

        result = response.json()
        embedding = result.get("embedding", [])

        # Normalize
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def apply_lora(self, adapter: LoRAAdapter) -> None:
        """Apply a LoRA adapter.

        Args:
            adapter: The LoRA adapter to apply.
        """
        self._active_loras[adapter.id] = adapter
        logger.info("Applied LoRA adapter: %s (weight=%.2f)",
                     adapter.name, adapter.weight)

    def remove_lora(self, adapter_id: str) -> bool:
        """Remove a LoRA adapter.

        Args:
            adapter_id: ID of the adapter to remove.

        Returns:
            True if removed.
        """
        if adapter_id in self._active_loras:
            del self._active_loras[adapter_id]
            logger.info("Removed LoRA adapter: %s", adapter_id)
            return True
        return False

    def get_active_loras(self) -> list[LoRAAdapter]:
        """Get active LoRA adapters.

        Returns:
            List of active adapters.
        """
        return list(self._active_loras.values())

    def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if Ollama is running and responsive.
        """
        try:
            response = self._client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Model info dictionary.
        """
        info = {
            "provider": "ollama",
            "model_name": self.model_name,
            "url": self.url,
            "active_loras": len(self._active_loras),
            "lora_list": [
                {"id": a.id, "name": a.name, "weight": a.weight}
                for a in self._active_loras.values()
            ],
        }
        return info

    def health_check(self) -> dict[str, Any]:
        """Perform health check.

        Returns:
            Health check result.
        """
        import time
        start = time.time()
        available = self.is_available()
        elapsed = time.time() - start

        return {
            "status": "healthy" if available else "unhealthy",
            "provider": "ollama",
            "model": self.model_name,
            "response_time_ms": round(elapsed * 1000, 2),
            "available": available,
        }

    def _build_structured_prompt(
        self, prompt: str, schema: dict[str, Any]
    ) -> str:
        """Build a prompt for structured output.

        Args:
            prompt: Original prompt.
            schema: JSON schema.

        Returns:
            Structured prompt string.
        """
        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond with a JSON object matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )
        return structured_prompt

    def _validate_structured_output(
        self, output: str, schema: dict[str, Any]
    ) -> None:
        """Validate output against schema.

        Args:
            output: Output string to validate.
            schema: JSON schema.

        Raises:
            StructuredOutputError: If validation fails.
        """
        try:
            data = json.loads(output)
            # Simple validation (can be extended with jsonschema)
            required = schema.get("required", [])
            properties = schema.get("properties", {})

            for field in required:
                if field not in data:
                    raise StructuredOutputError(
                        f"Missing required field: {field}",
                        errors=[f"{field} is required"],
                    )

            for field, field_schema in properties.items():
                if field in data:
                    expected_type = field_schema.get("type")
                    if expected_type:
                        type_map = {
                            "string": str,
                            "number": (int, float),
                            "integer": int,
                            "boolean": bool,
                            "array": list,
                            "object": dict,
                        }
                        expected = type_map.get(expected_type)
                        if expected and not isinstance(data[field], expected):
                            raise StructuredOutputError(
                                f"Field {field} has wrong type",
                                errors=[
                                    f"{field} expected {expected_type}, "
                                    f"got {type(data[field]).__name__}"
                                ],
                            )
        except json.JSONDecodeError as e:
            raise StructuredOutputError(
                f"Invalid JSON output: {e}",
                errors=[f"JSON decode error: {e}"],
            )
