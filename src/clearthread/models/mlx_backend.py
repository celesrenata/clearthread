"""MLX backend for ClearThread (Apple Silicon)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from clearthread.models.model_provider import (
    ModelProvider,
    StructuredOutputError,
)
from clearthread.models.lora import LoRAAdapter

logger = logging.getLogger("clearthread.mlx_backend")


class MLXBackend(ModelProvider):
    """MLX-based model provider for Apple Silicon.

    Uses Apple's MLX framework for efficient inference on MPS.
    """

    def __init__(
        self,
        model_path: str | Path = "./models/base/qwen2.5-7b.mlx",
        max_tokens: int = 4096,
    ) -> None:
        self.model_path = Path(model_path)
        self.max_tokens = max_tokens
        self._model = None
        self._tokenizer = None
        self._active_loras: dict[str, LoRAAdapter] = {}

    def _ensure_model(self) -> tuple[Any, Any]:
        """Ensure the MLX model is loaded."""
        if self._model is None:
            try:
                import mlx.nn
                from mlx_lm import load, generate

                self._model, self._tokenizer = load(
                    str(self.model_path)
                )
            except ImportError:
                raise RuntimeError(
                    "MLX framework not available. "
                    "Install with: pip install mlx mlx-lm"
                )
        return self._model, self._tokenizer

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using MLX.

        Args:
            prompt: Input prompt.
            **kwargs: temperature, max_tokens, top_p, stream, etc.

        Returns:
            Generated text.
        """
        model, tokenizer = self._ensure_model()

        params = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", 0.95),
            "prompt": prompt,
        }

        # Apply active LoRA adapters
        if self._active_loras:
            params["lora_adapters"] = list(
                self._active_loras.keys()
            )

        # MLX generate call
        from mlx_lm import generate
        output = generate(model, tokenizer, **params)

        return output

    def generate_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Generate structured output using MLX.

        Args:
            prompt: Input prompt.
            schema: JSON schema.
            **kwargs: Additional parameters.

        Returns:
            Parsed structured output.
        """
        model, tokenizer = self._ensure_model()

        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond with a JSON object matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        from mlx_lm import generate
        output = generate(
            model, tokenizer,
            prompt=structured_prompt,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
        )

        try:
            result = json.loads(output)
        except json.JSONDecodeError as e:
            raise StructuredOutputError(
                f"Invalid JSON from MLX: {e}",
                errors=[f"JSON decode error: {e}"],
            )

        return result

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embedding using MLX.

        Args:
            text: Input text.
            **kwargs: Additional parameters.

        Returns:
            Embedding vector.
        """
        model, tokenizer = self._ensure_model()

        # MLX embedding
        from mlx_lm import tokenize
        tokens = tokenize(text)

        # Compute embedding (simplified)
        embedding = self._compute_embedding(model, tokens)

        # Normalize
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _compute_embedding(
        self, model: Any, tokens: list[int]
    ) -> list[float]:
        """Compute embedding from model.

        Args:
            model: MLX model.
            tokens: Tokenized input.

        Returns:
            Embedding vector.
        """
        import mlx.core as mx

        # Simplified embedding computation
        # In practice, use the model's embed layer
        x = mx.array(tokens).reshape(1, -1)
        embedding = model.embed(x)
        return embedding.tolist()[0]

    def apply_lora(self, adapter: LoRAAdapter) -> None:
        """Apply a LoRA adapter.

        Args:
            adapter: The LoRA adapter to apply.
        """
        self._active_loras[adapter.id] = adapter
        logger.info("Applied LoRA adapter via MLX: %s", adapter.name)

    def remove_lora(self, adapter_id: str) -> bool:
        """Remove a LoRA adapter.

        Args:
            adapter_id: ID of the adapter to remove.

        Returns:
            True if removed.
        """
        if adapter_id in self._active_loras:
            del self._active_loras[adapter_id]
            return True
        return False

    def get_active_loras(self) -> list[LoRAAdapter]:
        """Get active LoRA adapters.

        Returns:
            List of active adapters.
        """
        return list(self._active_loras.values())

    def is_available(self) -> bool:
        """Check if MLX is available.

        Returns:
            True if MLX is available on this device.
        """
        try:
            import mlx.core as mx
            return mx.metal.is_available()
        except (ImportError, AttributeError):
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Model info dictionary.
        """
        return {
            "provider": "mlx",
            "model_path": str(self.model_path),
            "max_tokens": self.max_tokens,
            "metal_available": self.is_available(),
            "active_loras": len(self._active_loras),
        }

    def health_check(self) -> dict[str, Any]:
        """Perform health check.

        Returns:
            Health check result.
        """
        return {
            "status": "healthy" if self.is_available() else "unhealthy",
            "provider": "mlx",
            "metal_available": self.is_available(),
            "available": self.is_available(),
        }
