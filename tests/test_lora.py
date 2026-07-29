"""Unit tests for LoRA implementation (R37)."""

from pathlib import Path
from datetime import datetime
from uuid import uuid4

import pytest

from clearthread.models.lora import (
    LoRAAdapter,
    LoRAComposition,
    Persona,
    LoRAStore,
    LoRAFormat,
    LoRAType,
    LoRATask,
    TEXT_LORA_PRESETS,
    VISION_LORA_PRESETS,
    IMAGE_LORA_PRESETS,
    get_text_lora_presets,
    get_vision_lora_presets,
    get_image_lora_presets,
)


class TestLoRAAdapter:
    """Tests for LoRAAdapter."""

    def test_create_adapter(self):
        """Test creating a LoRA adapter."""
        adapter = LoRAAdapter(
            name="test",
            adapter_type=LoRAType.TEXT,
            format=LoRAFormat.SAFETENSORS,
            weight=0.8,
            task=LoRATask.CLASSIFICATION,
        )
        assert adapter.name == "test"
        assert adapter.adapter_type == LoRAType.TEXT
        assert adapter.format == LoRAFormat.SAFETENSORS
        assert adapter.weight == 0.8
        assert adapter.is_active is True

    def test_adapter_weight_bounds(self):
        """Test weight bounds."""
        a1 = LoRAAdapter(weight=1.5)
        assert a1.weight == 1.0

        a2 = LoRAAdapter(weight=-0.5)
        assert a2.weight == 0.0

    def test_adapter_inactive(self):
        """Test inactive adapter."""
        adapter = LoRAAdapter(weight=0.0)
        assert adapter.is_active is False

    def test_apply_weight(self):
        """Test applying new weight."""
        adapter = LoRAAdapter(weight=0.5)
        adapter.apply_weight(0.9)
        assert adapter.weight == 0.9

    def test_to_dict(self):
        """Test serialization."""
        adapter = LoRAAdapter(
            name="test",
            weight=0.75,
            dimension=4096,
            rank=64,
            base_model="qwen2.5-7b",
        )
        data = adapter.to_dict()
        assert data["name"] == "test"
        assert data["weight"] == 0.75
        assert data["dimension"] == 4096

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "test",
            "adapter_type": "text",
            "format": "safetensors",
            "weight": 0.8,
            "task": "classification",
            "dimension": 4096,
            "rank": 64,
            "base_model": "qwen2.5-7b",
        }
        adapter = LoRAAdapter.from_dict(data)
        assert adapter.name == "test"
        assert adapter.adapter_type == LoRAType.TEXT
        assert adapter.format == LoRAFormat.SAFETENSORS
        assert adapter.weight == 0.8

    def test_repr(self):
        """Test string representation."""
        adapter = LoRAAdapter(name="test", weight=0.5)
        assert "test" in repr(adapter)
        assert "0.5" in repr(adapter)


class TestLoRAComposition:
    """Tests for LoRAComposition."""

    def test_create_composition(self):
        """Test creating a composition."""
        comp = LoRAComposition(name="test_comp")
        assert comp.name == "test_comp"
        assert len(comp.adapters) == 0
        assert comp.total_weight == 0.0
        assert comp.effective_weight == 0.0

    def test_add_adapter(self):
        """Test adding adapter to composition."""
        comp = LoRAComposition()
        a1 = LoRAAdapter(name="a1", weight=0.8)
        comp.add_adapter(a1)
        assert len(comp.adapters) == 1
        assert comp.total_weight == 0.8

    def test_add_duplicate_adapter(self):
        """Test adding duplicate adapter."""
        comp = LoRAComposition()
        a1 = LoRAAdapter(name="a1")
        comp.add_adapter(a1)
        comp.add_adapter(a1)  # Should not duplicate
        assert len(comp.adapters) == 1

    def test_remove_adapter(self):
        """Test removing adapter."""
        comp = LoRAComposition()
        a1 = LoRAAdapter(name="a1")
        comp.add_adapter(a1)
        result = comp.remove_adapter(a1.id)
        assert result is True
        assert len(comp.adapters) == 0

    def test_remove_nonexistent_adapter(self):
        """Test removing non-existent adapter."""
        comp = LoRAComposition()
        result = comp.remove_adapter(uuid4())
        assert result is False

    def test_get_adapters_by_type(self):
        """Test filtering by type."""
        comp = LoRAComposition()
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.VISION))
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))

        text = comp.get_adapters_by_type(LoRAType.TEXT)
        assert len(text) == 2

    def test_total_weight(self):
        """Test total weight calculation."""
        comp = LoRAComposition()
        comp.add_adapter(LoRAAdapter(weight=0.5))
        comp.add_adapter(LoRAAdapter(weight=0.3))
        assert comp.total_weight == 0.8

    def test_effective_weight(self):
        """Test effective weight calculation."""
        comp = LoRAComposition()
        comp.add_adapter(LoRAAdapter(weight=0.5))
        comp.add_adapter(LoRAAdapter(weight=0.5))
        assert comp.effective_weight == 0.5

    def test_to_dict(self):
        """Test serialization."""
        comp = LoRAComposition(name="test")
        comp.add_adapter(LoRAAdapter(name="a1", weight=0.8))
        data = comp.to_dict()
        assert data["name"] == "test"
        assert len(data["adapters"]) == 1


class TestPersona:
    """Tests for Persona."""

    def test_create_persona(self):
        """Test creating a persona."""
        persona = Persona(
            name="Test Persona",
            description="Test description",
            base_model="qwen2.5-7b",
        )
        assert persona.name == "Test Persona"
        assert persona.base_model == "qwen2.5-7b"
        assert len(persona.text_adapters) == 0

    def test_persona_name_limit(self):
        """Test name length limit."""
        persona = Persona(name="N" * 200)
        assert len(persona.name) == 120

    def test_default_config(self):
        """Test default configuration."""
        persona = Persona()
        config = persona.get_effective_config()
        assert config["temperature"] == 0.7
        assert config["context_length"] == 4096
        assert config["max_evidence_window"] == 50
        assert config["prompt_version"] == "v2.1"

    def test_custom_config(self):
        """Test custom configuration."""
        persona = Persona(config={"temperature": 0.9, "custom_key": "value"})
        config = persona.get_effective_config()
        assert config["temperature"] == 0.9
        assert config["custom_key"] == "value"

    def test_add_text_adapter(self):
        """Test adding text adapter."""
        persona = Persona()
        adapter = LoRAAdapter(name="test", adapter_type=LoRAType.TEXT)
        persona.add_text_adapter(adapter)
        assert len(persona.text_adapters) == 1

    def test_set_vision_adapter(self):
        """Test setting vision adapter."""
        persona = Persona()
        adapter = LoRAAdapter(adapter_type=LoRAType.VISION)
        persona.set_vision_adapter(adapter)
        assert persona.vision_adapter is not None

    def test_set_image_adapter(self):
        """Test setting image adapter."""
        persona = Persona()
        adapter = LoRAAdapter(adapter_type=LoRAType.IMAGE)
        persona.set_image_adapter(adapter)
        assert persona.image_adapter is not None

    def test_to_dict(self):
        """Test serialization."""
        persona = Persona(
            name="Test",
            base_model="qwen2.5-7b",
            config={"temperature": 0.8},
        )
        data = persona.to_dict()
        assert data["name"] == "Test"
        assert data["base_model"] == "qwen2.5-7b"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "name": "Test",
            "base_model": "qwen2.5-7b",
            "config": {"temperature": 0.8},
            "text_adapters": [],
        }
        persona = Persona.from_dict(data)
        assert persona.name == "Test"
        assert persona.base_model == "qwen2.5-7b"

    def test_repr(self):
        """Test string representation."""
        persona = Persona(name="Test")
        assert "Test" in repr(persona)


class TestLoRAStore:
    """Tests for LoRAStore."""

    def test_add_adapter(self):
        """Test adding adapter to store."""
        store = LoRAStore()
        adapter = LoRAAdapter(name="test")
        key = store.add_adapter(adapter)
        assert store.get_adapter(key) is not None

    def test_get_adapter(self):
        """Test getting adapter."""
        store = LoRAStore()
        adapter = LoRAAdapter(name="test")
        store.add_adapter(adapter)
        retrieved = store.get_adapter(adapter.id)
        assert retrieved is not None
        assert retrieved.name == "test"

    def test_get_adapter_not_found(self):
        """Test getting non-existent adapter."""
        store = LoRAStore()
        assert store.get_adapter(uuid4()) is None

    def test_get_adapters_by_type(self):
        """Test getting adapters by type."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.VISION))
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))

        text = store.get_adapters_by_type(LoRAType.TEXT)
        assert len(text) == 2

    def test_get_active_adapters(self):
        """Test getting active adapters."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter(weight=0.0))  # Inactive
        store.add_adapter(LoRAAdapter(weight=0.5))  # Active
        store.add_adapter(LoRAAdapter(weight=1.0))  # Active

        active = store.get_active_adapters()
        assert len(active) == 2

    def test_compose_adapters(self):
        """Test composing adapters."""
        store = LoRAStore()
        a1 = LoRAAdapter(name="a1")
        a2 = LoRAAdapter(name="a2")
        store.add_adapter(a1)
        store.add_adapter(a2)

        comp = store.compose_adapters([a1.id, a2.id])
        assert len(comp.adapters) == 2

    def test_add_persona(self):
        """Test adding persona."""
        store = LoRAStore()
        persona = Persona(name="Test")
        key = store.add_persona(persona)
        assert store.get_persona(key) is not None
        assert store.get_persona_count() == 1

    def test_get_persona(self):
        """Test getting persona."""
        store = LoRAStore()
        persona = Persona(name="Test")
        store.add_persona(persona)
        retrieved = store.get_persona(persona.id)
        assert retrieved is not None

    def test_switch_persona(self):
        """Test switching personas."""
        store = LoRAStore()
        persona = Persona(name="Test")
        adapter = LoRAAdapter(name="a1", weight=0.5)
        persona.add_text_adapter(adapter)
        store.add_adapter(adapter)
        store.add_persona(persona)

        result = store.switch_persona(persona.id)
        assert result is True

    def test_blend_personas(self):
        """Test blending personas."""
        store = LoRAStore()
        p1 = Persona(name="P1")
        p2 = Persona(name="P2")
        a1 = LoRAAdapter(name="a1")
        p1.add_text_adapter(a1)
        store.add_adapter(a1)
        store.add_persona(p1)
        store.add_persona(p2)

        blended = store.blend_personas([p1.id, p2.id])
        assert len(blended.text_adapters) >= 1

    def test_save_persona_to_file(self, temp_dir):
        """Test saving persona to file."""
        store = LoRAStore(models_dir=temp_dir)
        persona = Persona(name="Test")
        path = store.save_persona_to_file(persona)
        assert path.exists()
        assert path.suffix == ".json"

    def test_load_persona_from_file(self, temp_dir):
        """Test loading persona from file."""
        store = LoRAStore(models_dir=temp_dir)
        persona = Persona(name="Test")
        path = store.save_persona_to_file(persona)
        loaded = store.load_persona_from_file(path)
        assert loaded.name == "Test"

    def test_get_adapter_count(self):
        """Test adapter count."""
        store = LoRAStore()
        assert store.get_adapter_count() == 0
        store.add_adapter(LoRAAdapter())
        assert store.get_adapter_count() == 1

    def test_get_persona_count(self):
        """Test persona count."""
        store = LoRAStore()
        assert store.get_persona_count() == 0
        store.add_persona(Persona())
        assert store.get_persona_count() == 1

    def test_to_dict(self):
        """Test serialization."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter())
        store.add_persona(Persona())
        data = store.to_dict()
        assert data["adapter_count"] == 1
        assert data["persona_count"] == 1

    def test_repr(self):
        """Test string representation."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter())
        assert "adapters=" in repr(store)


class TestLoRAPresets:
    """Tests for LoRA presets."""

    def test_text_presets(self):
        """Test text LoRA presets."""
        presets = get_text_lora_presets()
        assert "therapy_focused" in presets
        assert "neutral_tone" in presets
        assert "growth_bias" in presets
        assert len(presets) == 7

    def test_vision_presets(self):
        """Test vision LoRA presets."""
        presets = get_vision_lora_presets()
        assert "participant_recognition" in presets

    def test_image_presets(self):
        """Test image LoRA presets."""
        presets = get_image_lora_presets()
        assert "style_reconstruction" in presets

    def test_preset_values(self):
        """Test preset values match design.md."""
        assert TEXT_LORA_PRESETS["therapy_focused"]["weight"] == 0.9
        assert TEXT_LORA_PRESETS["neutral_tone"]["weight"] == 0.8
        assert TEXT_LORA_PRESETS["growth_bias"]["weight"] == 0.85
        assert VISION_LORA_PRESETS["participant_recognition"]["weight"] == 0.9
        assert IMAGE_LORA_PRESETS["style_reconstruction"]["weight"] == 0.85
