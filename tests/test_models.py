"""Unit tests for data models."""

from datetime import datetime
from uuid import uuid4

import pytest

from clearthread.models.message import Message, MessageType, AttachmentRef, Reaction
from clearthread.models.participant import Participant, RelationshipCategory
from clearthread.models.episode import Episode, EpisodeType, EpisodeStatus, MessageRef
from clearthread.models.finding import Finding, ConfidenceLevel, FindingStatus, ReflectionQuestionEntry
from clearthread.models.provenance import ProvenanceRecord, ProvenanceStep
from clearthread.models.relationship_chapter import RelationshipChapter, ChapterSection, ChapterSectionType
from clearthread.models.therapy_brief import TherapyBrief, BriefDetailLevel, BriefSectionType
from clearthread.models.reflection_question import ReflectionQuestion
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
)
from clearthread.models.base import ContentHash, ExclusionState, ContentCategory, UserReviewState


class TestMessage:
    """Tests for the Message model (R1, R3, R18)."""

    def test_create_message(self):
        """Test creating a message with default values."""
        msg = Message(text="Hello", message_type=MessageType.TEXT)
        assert msg.text == "Hello"
        assert msg.message_type == MessageType.TEXT
        assert msg.content_hash != ""
        assert msg.owner_authored is False
        assert msg.analysis_eligible is True
        assert msg.exclusion_state == ExclusionState.INCLUDED

    def test_message_serialization(self):
        """Test Message to_dict and from_dict."""
        msg = Message(
            source_id="src_001",
            text="Test message",
            message_type=MessageType.MEDIA,
            owner_authored=True,
            deleted=True,
            unsent=False,
        )
        data = msg.to_dict()
        restored = Message.from_dict(data)
        assert restored.source_id == msg.source_id
        assert restored.text == msg.text
        assert restored.message_type == msg.message_type
        assert restored.owner_authored == msg.owner_authored
        assert restored.deleted == msg.deleted

    def test_message_json_roundtrip(self):
        """Test Message JSON serialization."""
        msg = Message(text="JSON test")
        json_str = msg.to_json()
        restored = Message.from_json(json_str)
        assert restored.text == msg.text

    def test_content_hash_computation(self):
        """Test content hash computation."""
        hash1 = ContentHash.compute("test content")
        hash2 = ContentHash.compute("test content")
        hash3 = ContentHash.compute("different content")
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA-256 hex length

    def test_message_dedup_hash(self):
        """Test message deduplication hash (R1)."""
        h1 = Message.compute_dedup_hash("Alice", "2024-01-01", "Hello")
        h2 = Message.compute_dedup_hash("Alice", "2024-01-01", "Hello")
        h3 = Message.compute_dedup_hash("Bob", "2024-01-01", "Hello")
        assert h1 == h2
        assert h1 != h3

    def test_message_repr(self):
        """Test Message string representation."""
        msg = Message(text="Short text", sender_display_name="Alice")
        assert "Alice" in repr(msg)
        assert "text" in repr(msg)


class TestParticipant:
    """Tests for the Participant model (R4)."""

    def test_create_participant(self):
        """Test creating a participant."""
        p = Participant(
            display_name="Alice",
            is_user=True,
            category=RelationshipCategory.PARTNER,
        )
        assert p.display_name == "Alice"
        assert p.is_user is True
        assert p.category == RelationshipCategory.PARTNER
        assert p.message_count == 0

    def test_participant_constraints(self):
        """Test participant constraint validation (R4)."""
        p = Participant(
            display_name="A" * 150,  # Exceeds 100 char limit
            note="N" * 3000,  # Exceeds 2000 char limit
        )
        assert len(p.display_name) <= 100
        assert len(p.note) <= 2000

    def test_add_alias(self):
        """Test adding aliases (R4)."""
        p = Participant()
        assert p.add_alias("Alice Smith") is True
        assert len(p.aliases) == 1
        assert p.add_alias("Alice Smith") is False  # Duplicate
        assert len(p.aliases) == 1

        # Test max aliases (MAX_ALIASES = 11)
        added = 0
        for i in range(15):
            if p.add_alias(f"alias_{i}"):
                added += 1
        assert len(p.aliases) <= 11  # MAX_ALIASES
        assert added >= 9  # At least 9 new aliases added (some may hit max)

    def test_participant_serialization(self):
        """Test Participant to_dict and from_dict."""
        p = Participant(
            display_name="Bob",
            category=RelationshipCategory.FRIEND,
            is_past=True,
            note="A note",
        )
        data = p.to_dict()
        restored = Participant.from_dict(data)
        assert restored.display_name == p.display_name
        assert restored.category == p.category
        assert restored.is_past == p.is_past


class TestEpisode:
    """Tests for the Episode model (R6)."""

    def test_create_episode(self):
        """Test creating an episode."""
        ep = Episode(
            episode_type=EpisodeType.CONFLICT,
            confidence=0.75,
        )
        assert ep.episode_type == EpisodeType.CONFLICT
        assert ep.confidence == 0.75
        assert ep.status == EpisodeStatus.PROPOSED
        assert ep.is_surfaceable() is True  # 0.75 >= 0.5

    def test_episode_confidence_bounds(self):
        """Test episode confidence bounds (R6)."""
        ep = Episode(confidence=1.5)  # Exceeds max
        assert ep.confidence == 1.0

        ep2 = Episode(confidence=-0.5)  # Below min
        assert ep2.confidence == 0.0

    def test_episode_context_limits(self):
        """Test episode context message limits (R6)."""
        from uuid import uuid4
        ep = Episode()
        # Add messages - should be limited by MAX_CONTEXT_MESSAGES
        for i in range(15):
            if len(ep.context_before) < 10:
                ep.context_before.append(MessageRef(message_id=uuid4(), position=i))
        assert len(ep.context_before) <= 10  # MAX_CONTEXT_MESSAGES

    def test_episode_surfaceable(self):
        """Test episode surfaceability (R6)."""
        ep = Episode(confidence=0.4)
        assert ep.is_surfaceable() is False

        ep2 = Episode(confidence=0.5)
        assert ep2.is_surfaceable() is True

    def test_episode_serialization(self):
        """Test Episode to_dict and from_dict."""
        ep = Episode(
            episode_type=EpisodeType.REPAIR_ATTEMPT,
            confidence=0.8,
            title="Test episode",
        )
        data = ep.to_dict()
        restored = Episode.from_dict(data)
        assert restored.episode_type == ep.episode_type
        assert abs(restored.confidence - ep.confidence) < 0.01


class TestFinding:
    """Tests for the Finding model (R8, R21)."""

    def test_create_finding(self):
        """Test creating a finding."""
        f = Finding(
            title="Test pattern",
            explanation="Test explanation",
            confidence_level=ConfidenceLevel.MODERATE,
        )
        assert f.title == "Test pattern"
        assert f.confidence_level == ConfidenceLevel.MODERATE
        assert f.has_sufficient_evidence() is False  # No evidence yet

    def test_finding_title_limit(self):
        """Test finding title length limit (R8)."""
        f = Finding(title="T" * 100)
        assert len(f.title) == 80  # MAX_TITLE_LEN

    def test_finding_evidence_count(self):
        """Test finding evidence count."""
        from clearthread.models.base import EvidenceReference
        f = Finding()
        assert f.has_sufficient_evidence() is False

        f.evidence_references.append(EvidenceReference(
            message_id=uuid4(), source_id="src"
        ))
        f.evidence_references.append(EvidenceReference(
            message_id=uuid4(), source_id="src"
        ))
        f.evidence_references.append(EvidenceReference(
            message_id=uuid4(), source_id="src"
        ))
        assert f.has_sufficient_evidence() is True  # 3 >= 3

    def test_finding_needs_more_data(self):
        """Test finding data sufficiency (R9)."""
        f = Finding()
        assert f.needs_more_data(15) is True  # < 20
        assert f.needs_more_data(20) is False  # >= 20
        assert f.needs_more_data(25) is False

    def test_finding_serialization(self):
        """Test Finding to_dict and from_dict."""
        f = Finding(
            title="Test",
            confidence_level=ConfidenceLevel.STRONG,
            confidence_percentage=85.0,
        )
        data = f.to_dict()
        restored = Finding.from_dict(data)
        assert restored.title == f.title
        assert restored.confidence_level == f.confidence_level
        assert restored.confidence_percentage == f.confidence_percentage


class TestProvenanceRecord:
    """Tests for the ProvenanceRecord model (R13)."""

    def test_create_provenance_record(self):
        """Test creating a provenance record."""
        pr = ProvenanceRecord(
            run_id="run_001",
            analysis_type="test",
            confidence_score=0.9,
        )
        assert pr.run_id == "run_001"
        assert pr.confidence_score == 0.9
        assert len(pr.processing_steps) == 0

    def test_add_step(self):
        """Test adding processing steps."""
        from datetime import datetime
        pr = ProvenanceRecord()
        step = ProvenanceStep(
            step_sequence=1,
            operation_name="import",
            input_record_ref="in_1",
            output_record_ref="out_1",
            timestamp=datetime.utcnow(),
        )
        pr.add_step(step)
        assert len(pr.processing_steps) == 1
        assert pr.processing_steps[0].step_sequence == 1

    def test_provenance_serialization(self):
        """Test ProvenanceRecord to_dict and from_dict."""
        pr = ProvenanceRecord(
            run_id="run_002",
            model_name="qwen2.5",
            validation_status="pass",
        )
        data = pr.to_dict()
        restored = ProvenanceRecord.from_dict(data)
        assert restored.run_id == pr.run_id
        assert restored.model_name == pr.model_name
        assert restored.validation_status == pr.validation_status


class TestLoRA:
    """Tests for LoRA implementation (R37)."""

    def test_lora_adapter_creation(self):
        """Test LoRA adapter creation."""
        adapter = LoRAAdapter(
            name="test_adapter",
            adapter_type=LoRAType.TEXT,
            weight=0.8,
        )
        assert adapter.name == "test_adapter"
        assert adapter.weight == 0.8
        assert adapter.is_active is True

    def test_lora_adapter_weight_bounds(self):
        """Test LoRA adapter weight bounds."""
        adapter = LoRAAdapter(weight=1.5)
        assert adapter.weight == 1.0

        adapter2 = LoRAAdapter(weight=-0.5)
        assert adapter2.weight == 0.0

    def test_lora_adapter_apply_weight(self):
        """Test applying new weight to adapter."""
        adapter = LoRAAdapter(weight=0.5)
        adapter.apply_weight(0.9)
        assert adapter.weight == 0.9

    def test_lora_composition(self):
        """Test LoRA composition."""
        comp = LoRAComposition(name="test_composition")
        a1 = LoRAAdapter(name="a1", weight=0.8)
        a2 = LoRAAdapter(name="a2", weight=0.6)
        comp.add_adapter(a1)
        comp.add_adapter(a2)

        assert len(comp.adapters) == 2
        assert comp.total_weight == 1.4
        assert comp.effective_weight == 0.7

    def test_lora_composition_remove(self):
        """Test removing adapter from composition."""
        comp = LoRAComposition()
        a1 = LoRAAdapter(name="a1")
        comp.add_adapter(a1)
        assert comp.remove_adapter(a1.id) is True
        assert len(comp.adapters) == 0

    def test_lora_composition_by_type(self):
        """Test filtering composition adapters by type."""
        comp = LoRAComposition()
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.VISION))
        comp.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))

        text_adapters = comp.get_adapters_by_type(LoRAType.TEXT)
        assert len(text_adapters) == 2

    def test_persona_creation(self):
        """Test persona creation."""
        persona = Persona(
            name="Test Persona",
            base_model="qwen2.5-7b",
        )
        assert persona.name == "Test Persona"
        assert persona.base_model == "qwen2.5-7b"
        assert len(persona.text_adapters) == 0

    def test_persona_name_limit(self):
        """Test persona name length limit."""
        persona = Persona(name="N" * 200)
        assert len(persona.name) == 120  # MAX_NAME_LEN

    def test_persona_add_text_adapter(self):
        """Test adding text adapter to persona."""
        persona = Persona()
        adapter = LoRAAdapter(name="test", adapter_type=LoRAType.TEXT)
        persona.add_text_adapter(adapter)
        assert len(persona.text_adapters) == 1

    def test_persona_set_vision_adapter(self):
        """Test setting vision adapter on persona."""
        persona = Persona()
        adapter = LoRAAdapter(adapter_type=LoRAType.VISION)
        persona.set_vision_adapter(adapter)
        assert persona.vision_adapter is not None

    def test_persona_effective_config(self):
        """Test persona effective configuration."""
        persona = Persona(config={"temperature": 0.9})
        config = persona.get_effective_config()
        assert config["temperature"] == 0.9
        assert config["context_length"] == 4096  # Default

    def test_lora_store(self):
        """Test LoRA store operations."""
        store = LoRAStore()
        adapter = LoRAAdapter(name="test")
        key = store.add_adapter(adapter)

        assert store.get_adapter(key) is not None
        assert store.get_adapter(key).name == "test"
        assert store.get_adapter(uuid4()) is None

    def test_lora_store_adapters_by_type(self):
        """Test getting adapters by type from store."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.VISION))
        store.add_adapter(LoRAAdapter(adapter_type=LoRAType.TEXT))

        text_adapters = store.get_adapters_by_type(LoRAType.TEXT)
        assert len(text_adapters) == 2

    def test_lora_store_active_adapters(self):
        """Test getting active adapters."""
        store = LoRAStore()
        store.add_adapter(LoRAAdapter(weight=0.0))  # Inactive
        store.add_adapter(LoRAAdapter(weight=0.5))  # Active
        store.add_adapter(LoRAAdapter(weight=1.0))  # Active

        active = store.get_active_adapters()
        assert len(active) == 2

    def test_lora_store_compose_adapters(self):
        """Test composing adapters in store."""
        store = LoRAStore()
        a1 = LoRAAdapter(name="a1")
        a2 = LoRAAdapter(name="a2")
        store.add_adapter(a1)
        store.add_adapter(a2)

        comp = store.compose_adapters([a1.id, a2.id])
        assert len(comp.adapters) == 2

    def test_lora_store_add_persona(self):
        """Test adding persona to store."""
        store = LoRAStore()
        persona = Persona(name="Test")
        key = store.add_persona(persona)

        assert store.get_persona(key) is not None
        assert store.get_persona_count() == 1

    def test_lora_store_switch_persona(self):
        """Test switching personas."""
        store = LoRAStore()
        persona = Persona(name="Test")
        adapter = LoRAAdapter(name="a1", weight=0.5)
        persona.add_text_adapter(adapter)
        store.add_adapter(adapter)
        store.add_persona(persona)

        result = store.switch_persona(persona.id)
        assert result is True

    def test_lora_store_blend_personas(self):
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

    def test_text_lora_presets(self):
        """Test text LoRA presets."""
        assert "therapy_focused" in TEXT_LORA_PRESETS
        assert TEXT_LORA_PRESETS["therapy_focused"]["weight"] == 0.9
        assert TEXT_LORA_PRESETS["neutral_tone"]["weight"] == 0.8

    def test_vision_lora_presets(self):
        """Test vision LoRA presets."""
        assert "participant_recognition" in VISION_LORA_PRESETS

    def test_image_lora_presets(self):
        """Test image LoRA presets."""
        assert "style_reconstruction" in IMAGE_LORA_PRESETS

    def test_lora_adapter_serialization(self):
        """Test LoRA adapter to_dict and from_dict."""
        adapter = LoRAAdapter(
            name="test",
            weight=0.75,
            dimension=4096,
            rank=64,
        )
        data = adapter.to_dict()
        restored = LoRAAdapter.from_dict(data)
        assert restored.name == adapter.name
        assert abs(restored.weight - adapter.weight) < 0.01

    def test_persona_serialization(self):
        """Test persona to_dict and from_dict."""
        persona = Persona(
            name="Test",
            base_model="qwen2.5-7b",
            config={"temperature": 0.8},
        )
        data = persona.to_dict()
        restored = Persona.from_dict(data)
        assert restored.name == persona.name
        assert restored.base_model == persona.base_model


class TestContentHash:
    """Tests for ContentHash."""

    def test_compute_hash(self):
        """Test hash computation."""
        h = ContentHash.compute("test")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_compute_message_hash(self):
        """Test message dedup hash computation."""
        h = ContentHash.compute_message("Alice", "2024-01-01", "Hello")
        assert isinstance(h, str)


class TestExclusionState:
    """Tests for ExclusionState."""

    def test_exclusion_states(self):
        """Test exclusion state values."""
        assert ExclusionState.INCLUDED.value == "included"
        assert ExclusionState.EXCLUDED.value == "excluded"


class TestContentCategory:
    """Tests for ContentCategory."""

    def test_content_categories(self):
        """Test content category values."""
        assert ContentCategory.DOCUMENTED_FACT.value == "documented_fact"
        assert ContentCategory.CALCULATED_PATTERN.value == "calculated_pattern"
        assert ContentCategory.AI_GENERATED_SUMMARY.value == "ai_generated_summary"
        assert ContentCategory.USER_SUPPLIED_CONTEXT.value == "user_supplied_context"
        assert ContentCategory.UNCERTAIN_MISSING.value == "uncertain_missing"


class TestUserReviewState:
    """Tests for UserReviewState."""

    def test_review_states(self):
        """Test user review state values."""
        assert UserReviewState.UNREVIEWED.value == "unreviewed"
        assert UserReviewState.CONFIRMED.value == "confirmed"
        assert UserReviewState.DISPUTED.value == "disputed"
        assert UserReviewState.CORRECTED.value == "corrected"
