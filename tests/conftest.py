"""Shared test fixtures for ClearThread tests."""

from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from clearthread.models.message import Message, MessageType
from clearthread.models.participant import Participant, RelationshipCategory
from clearthread.models.episode import Episode, EpisodeType, EpisodeStatus
from clearthread.models.finding import Finding, ConfidenceLevel
from clearthread.models.provenance import ProvenanceRecord
from clearthread.models.lora import LoRAAdapter, LoRAType, LoRATask, Persona
from clearthread.storage.source_vault import SourceDataVault
from clearthread.storage.normalized_store import NormalizedStore
from clearthread.storage.media_store import MediaStore
from clearthread.storage.encryption import EncryptionLayer
from clearthread.import_pipeline import ImportPipeline
from clearthread.analysis.episode_engine import EpisodeEngine
from clearthread.analysis.pattern_analyzer import PatternAnalyzer
from clearthread.analysis.growth_analyzer import GrowthAnalyzer
from clearthread.search.engine import SearchEngine
from clearthread.export.engine import ExportEngine


@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    messages = []
    for i in range(20):
        msg = Message(
            source_id=f"msg_{i}",
            conversation_id=uuid4(),
            sender_id=uuid4(),
            original_timestamp=base_time + timedelta(hours=i),
            normalized_utc=base_time + timedelta(hours=i),
            text=f"Sample message {i} about relationships and boundaries",
            message_type=MessageType.TEXT,
            owner_authored=(i % 2 == 0),
            deleted=False,
            unsent=False,
        )
        messages.append(msg)
    return messages


@pytest.fixture
def sample_participants():
    """Create sample participants for testing."""
    p1 = Participant(
        source_id="p1",
        display_name="Alice",
        is_user=True,
        category=RelationshipCategory.PARTNER,
        message_count=50,
    )
    p2 = Participant(
        source_id="p2",
        display_name="Bob",
        is_user=False,
        category=RelationshipCategory.FRIEND,
        message_count=30,
    )
    p3 = Participant(
        source_id="p3",
        display_name="Carol",
        is_user=False,
        category=RelationshipCategory.FAMILY,
        message_count=20,
    )
    return [p1, p2, p3]


@pytest.fixture
def sample_episodes():
    """Create sample episodes for testing."""
    episodes = []
    for i in range(5):
        episode = Episode(
            conversation_id=uuid4(),
            episode_type=EpisodeType.CONFLICT if i % 2 == 0 else EpisodeType.REPAIR_ATTEMPT,
            confidence=0.5 + (i * 0.1),
            status=EpisodeStatus.PROPOSED,
            title=f"Episode {i}",
        )
        episodes.append(episode)
    return episodes


@pytest.fixture
def sample_findings():
    """Create sample findings for testing."""
    findings = []
    for i in range(3):
        finding = Finding(
            title=f"Pattern {i}",
            explanation=f"Explanation for pattern {i}",
            confidence_level=ConfidenceLevel.MODERATE if i < 2 else ConfidenceLevel.PRELIMINARY,
            confidence_percentage=50.0 + (i * 15),
        )
        findings.append(finding)
    return findings


@pytest.fixture
def source_vault(tmp_path):
    """Create a SourceDataVault with temp directory."""
    return SourceDataVault(data_dir=tmp_path / "source_data")


@pytest.fixture
def normalized_store(tmp_path):
    """Create a NormalizedStore with temp directory."""
    return NormalizedStore(data_dir=tmp_path / "normalized")


@pytest.fixture
def media_store(tmp_path):
    """Create a MediaStore with temp directory."""
    return MediaStore(media_dir=tmp_path / "media")


@pytest.fixture
def encryption_layer(tmp_path):
    """Create an EncryptionLayer with temp directory."""
    return EncryptionLayer(key_path=tmp_path / "encryption.key")


@pytest.fixture
def import_pipeline(tmp_path):
    """Create an ImportPipeline with temp directory."""
    return ImportPipeline(data_dir=tmp_path)


@pytest.fixture
def episode_engine():
    """Create an EpisodeEngine."""
    return EpisodeEngine()


@pytest.fixture
def pattern_analyzer():
    """Create a PatternAnalyzer."""
    return PatternAnalyzer()


@pytest.fixture
def growth_analyzer():
    """Create a GrowthAnalyzer."""
    return GrowthAnalyzer()


@pytest.fixture
def search_engine():
    """Create a SearchEngine."""
    return SearchEngine()


@pytest.fixture
def export_engine(tmp_path):
    """Create an ExportEngine with temp directory."""
    return ExportEngine(output_dir=tmp_path / "exports")


@pytest.fixture
def sample_lora_adapter():
    """Create a sample LoRA adapter."""
    return LoRAAdapter(
        name="therapy_focused",
        adapter_type=LoRAType.TEXT,
        format="safetensors",
        weight=0.9,
        task=LoRATask.CLASSIFICATION,
        base_model="qwen2.5-7b",
        dimension=4096,
        rank=64,
    )


@pytest.fixture
def sample_persona():
    """Create a sample persona."""
    return Persona(
        name="Therapy Focused",
        description="Therapy-focused analysis persona",
        base_model="qwen2.5-7b",
        config={
            "temperature": 0.7,
            "context_length": 4096,
            "max_evidence_window": 50,
            "prompt_version": "v2.1",
        },
    )


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory path."""
    return tmp_path


@pytest.fixture
def sample_provenance():
    """Create a sample ProvenanceRecord."""
    return ProvenanceRecord(
        run_id="test_run_001",
        analysis_type="pattern_detection",
        model_name="qwen2.5",
        model_version="2.5.0",
        prompt_version="v2.1",
        parser_version="1.0.0",
        confidence_score=0.85,
    )
