"""llama.cpp backend for ClearThread."""

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

logger = logging.getLogger("clearthread.llamacpp_backend")


class LlamaCppBackend(ModelProvider):
    """llama.cpp-based model provider.

    Uses llama-cpp-python for CPU-based inference.
    """

    def __init__(
        self,
        model_path: str | Path = "./models/base/qwen2.5-7b.Q4_K_M.gguf",
        n_ctx: int = 4096,
        n_gpu_layers: int = 35,
        n_threads: int = 8,
    ) -> None:
        self.model_path = Path(model_path)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self._model = None
        self._active_loras: dict[str, LoRAAdapter] = {}

    def _ensure_model(self) -> Any:
        """Ensure the model is loaded."""
        if self._model is None:
            from llama_cpp import Llama
            self._model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
            )
        return self._model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using llama.cpp.

        Args:
            prompt: Input prompt.
            **kwargs: temperature, max_tokens, top_p, repeat_penalty, etc.

        Returns:
            Generated text.
        """
        model = self._ensure_model()

        params = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 0.95),
            "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
        }

        output = model.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            **params,
        )

        return output["choices"][0]["message"]["content"]

    def generate_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Generate structured output using llama.cpp.

        Args:
            prompt: Input prompt.
            schema: JSON schema.
            **kwargs: Additional parameters.

        Returns:
            Parsed structured output.
        """
        model = self._ensure_model()

        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond with a JSON object matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        output = model.create_chat_completion(
            messages=[{"role": "user", "content": structured_prompt}],
            response_format={"type": "json_object"},
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2048),
        )

        result_str = output["choices"][0]["message"]["content"]

        try:
            result = json.loads(result_str)
        except json.JSONDecodeError as e:
            raise StructuredOutputError(
                f"Invalid JSON from llama.cpp: {e}",
                errors=[f"JSON decode error: {e}"],
            )

        return result

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embedding using llama.cpp.

        Args:
            text: Input text.
            **kwargs: Additional parameters.

        Returns:
            Embedding vector.
        """
        model = self._ensure_model()
        embedding = model.embed(text)

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
        logger.info("Applied LoRA adapter via llama.cpp: %s", adapter.name)

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
        """Check if llama.cpp is available.

        Returns:
            True if the model file exists and is loadable.
        """
        return self.model_path.exists()

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Model info dictionary.
        """
        return {
            "provider": "llamacpp",
            "model_path": str(self.model_path),
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "n_threads": self.n_threads,
            "active_loras": len(self._active_loras),
        }

    def health_check(self) -> dict[str, Any]:
        """Perform health check.

        Returns:
            Health check result.
        """
        return {
            "status": "healthy" if self.is_available() else "unhealthy",
            "provider": "llamacpp",
            "model_path": str(self.model_path),
            "available": self.is_available(),
        }
