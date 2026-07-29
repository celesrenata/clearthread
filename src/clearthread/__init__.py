"""ClearThread - Local-first Facebook/Messenger relationship analysis."""

__version__ = "0.1.0"
__author__ = "ClearThread Contributors"

from clearthread.models import (
    Message,
    Participant,
    Episode,
    Finding,
    ProvenanceRecord,
    RelationshipChapter,
    TherapyBrief,
    ReflectionQuestion,
)
from clearthread.storage import (
    SourceDataVault,
    NormalizedStore,
    MediaStore,
    EncryptionLayer,
)
from clearthread.import_pipeline import ImportPipeline
from clearthread.analysis import (
    EpisodeEngine,
    PatternAnalyzer,
    GrowthAnalyzer,
    ReflectionQuestionGenerator,
)
from clearthread.search import SearchEngine
from clearthread.export import ExportEngine

__all__ = [
    # Models
    "Message",
    "Participant",
    "Episode",
    "Finding",
    "ProvenanceRecord",
    "RelationshipChapter",
    "TherapyBrief",
    "ReflectionQuestion",
    # Storage
    "SourceDataVault",
    "NormalizedStore",
    "MediaStore",
    "EncryptionLayer",
    # Import
    "ImportPipeline",
    # Analysis
    "EpisodeEngine",
    "PatternAnalyzer",
    "GrowthAnalyzer",
    "ReflectionQuestionGenerator",
    # Search
    "SearchEngine",
    # Export
    "ExportEngine",
]
