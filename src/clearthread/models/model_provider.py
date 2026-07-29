"""ModelProvider interface and base implementations."""

from __future__ import annotations

import abc
import json
import logging
from pathlib import Path
from typing import Any

from clearthread.models.lora import LoRAAdapter, LoRAComposition

logger = logging.getLogger("clearthread.model_provider")


class ModelProvider(abc.ABC):
    """Abstract base class for AI model providers."""

    @abc.abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text response from the model.

        Args:
            prompt: The input prompt text.
            **kwargs: Additional model-specific parameters
                (temperature, max_tokens, top_p, etc.).

        Returns:
            Generated text response.
        """
        ...

    @abc.abstractmethod
    def generate_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Generate a structured response validated against a JSON schema.

        Args:
            prompt: The input prompt text.
            schema: JSON schema to validate the output against.
            **kwargs: Additional model-specific parameters.

        Returns:
            Parsed structured response as a dictionary.

        Raises:
            StructuredOutputError: If the output doesn't match the schema.
        """
        ...

    @abc.abstractmethod
    def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.
            **kwargs: Additional parameters.

        Returns:
            Normalized embedding vector.
        """
        ...

    @abc.abstractmethod
    def apply_lora(self, adapter: LoRAAdapter) -> None:
        """Apply a LoRA adapter to the model.

        Args:
            adapter: The LoRA adapter to apply.
        """
        ...

    @abc.abstractmethod
    def remove_lora(self, adapter_id: str) -> bool:
        """Remove a LoRA adapter from the model.

        Args:
            adapter_id: The ID of the adapter to remove.

        Returns:
            True if the adapter was removed, False if not found.
        """
        ...

    @abc.abstractmethod
    def get_active_loras(self) -> list[LoRAAdapter]:
        """Get all currently active LoRA adapters.

        Returns:
            List of active LoRA adapters.
        """
        ...

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if the model backend is available and responsive.

        Returns:
            True if the backend is available.
        """
        ...

    @abc.abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model configuration.

        Returns:
            Dictionary with model information.
        """
        ...

    @abc.abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Perform a health check on the model backend.

        Returns:
            Health check result with status and timing information.
        """
        ...


class StructuredOutputError(Exception):
    """Raised when structured output doesn't match the schema."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class ModelRegistry:
    """Registry for discovered and available models."""

    def __init__(self) -> None:
        self._models: dict[str, dict[str, Any]] = {}
        self._active_model: str | None = None

    def register_model(
        self,
        name: str,
        model_type: str,
        provider: str,
        version: str,
        path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Register a model in the registry.

        Args:
            name: Unique model name.
            model_type: Type of model (text, vision, image).
            provider: Provider name (ollama, llamacpp, mlx).
            version: Model version string.
            path: Optional path to model files.
            **kwargs: Additional metadata.
        """
        self._models[name] = {
            "name": name,
            "type": model_type,
            "provider": provider,
            "version": version,
            "path": str(path) if path else None,
            "metadata": kwargs,
            "is_active": name == self._active_model,
        }

    def get_model(self, name: str) -> dict[str, Any] | None:
        """Get a model by name.

        Args:
            name: Model name.

        Returns:
            Model information or None if not found.
        """
        return self._models.get(name)

    def get_active_model(self) -> dict[str, Any] | None:
        """Get the currently active model.

        Returns:
            Active model information or None.
        """
        if self._active_model:
            return self._models.get(self._active_model)
        return None

    def set_active_model(self, name: str) -> bool:
        """Set the active model.

        Args:
            name: Model name to activate.

        Returns:
            True if the model was activated.
        """
        if name in self._models:
            self._active_model = name
            for model_name in self._models:
                self._models[model_name]["is_active"] = (
                    model_name == name
                )
            return True
        return False

    def get_models_by_type(self, model_type: str) -> list[dict[str, Any]]:
        """Get all models of a specific type.

        Args:
            model_type: Model type to filter by.

        Returns:
            List of matching models.
        """
        return [
            m for m in self._models.values()
            if m["type"] == model_type
        ]

    def get_models_by_provider(self, provider: str) -> list[dict[str, Any]]:
        """Get all models from a specific provider.

        Args:
            provider: Provider name to filter by.

        Returns:
            List of matching models.
        """
        return [
            m for m in self._models.values()
            if m["provider"] == provider
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the registry to a dictionary.

        Returns:
            Serialized registry.
        """
        return {
            "active_model": self._active_model,
            "models": self._models,
        }


class ModelDownloader:
    """Download and cache AI models."""

    def __init__(self, cache_dir: Path | str = "./models/base") -> None:
        self.cache_dir = Path(cache_dir)
        self._download_status: dict[str, str] = {}

    def download_model(
        self,
        name: str,
        source: str,
        model_type: str,
        provider: str,
    ) -> Path:
        """Download a model from the source.

        Args:
            name: Model name.
            source: Source URL or path.
            model_type: Type of model.
            provider: Target provider.

        Returns:
            Path to the downloaded model.
        """
        model_dir = self.cache_dir / model_type / provider / name
        model_dir.mkdir(parents=True, exist_ok=True)

        # Check if already downloaded
        if (model_dir / "model.safetensors").exists():
            return model_dir

        # Download logic here
        self._download_status[name] = "downloading"
        # ... actual download implementation ...
        self._download_status[name] = "downloaded"

        return model_dir

    def get_cached_models(self) -> list[dict[str, Any]]:
        """Get all cached models.

        Returns:
            List of cached model information.
        """
        models = []
        for model_type_dir in self.cache_dir.iterdir():
            if not model_type_dir.is_dir():
                continue
            for provider_dir in model_type_dir.iterdir():
                if not provider_dir.is_dir():
                    continue
                for name_dir in provider_dir.iterdir():
                    if name_dir.is_dir():
                        models.append({
                            "name": name_dir.name,
                            "type": model_type_dir.name,
                            "provider": provider_dir.name,
                            "path": str(name_dir),
                            "status": self._download_status.get(
                                name_dir.name, "cached"
                            ),
                        })
        return models

    def remove_model(self, name: str, model_type: str, provider: str) -> bool:
        """Remove a cached model.

        Args:
            name: Model name.
            model_type: Model type.
            provider: Provider.

        Returns:
            True if the model was removed.
        """
        model_dir = self.cache_dir / model_type / provider / name
        if model_dir.exists():
            import shutil
            shutil.rmtree(model_dir)
            return True
        return False
