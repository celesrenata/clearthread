"""ClearThread data models."""

from clearthread.models.base import (
    ContentCategory,
    EvidenceReference,
    ExclusionState,
    Model,
    ProvenanceRef,
    StorageBackend,
    UserReviewState,
)
from clearthread.models.episode import (
    Episode,
    EpisodeStatus,
    EpisodeType,
    MessageRef,
)
from clearthread.models.finding import (
    ConfidenceLevel,
    Finding,
    FindingStatus,
    ReflectionQuestionEntry,
)
from clearthread.models.lora import (
    LoRAAdapter,
    LoRAComposition,
    LoRAFormat,
    LoRAStore,
    LoRATask,
    LoRAType,
    Persona,
    get_image_lora_presets,
    get_text_lora_presets,
    get_vision_lora_presets,
)
from clearthread.models.message import (
    AttachmentRef,
    Message,
    MessageType,
    Reaction,
)
from clearthread.models.participant import (
    Participant,
    RelationshipCategory,
)
from clearthread.models.provenance import (
    ProvenanceRecord,
    ProvenanceStep,
    ProvenanceStepType,
)
from clearthread.models.reflection_question import (
    ReflectionQuestion,
)
from clearthread.models.relationship_chapter import (
    ChapterSection,
    ChapterSectionType,
    RelationshipChapter,
)
from clearthread.models.therapy_brief import (
    BriefDetailLevel,
    BriefSectionType,
    TherapyBrief,
)

# Model Provider
from clearthread.models.model_provider import (
    ModelDownloader,
    ModelProvider,
    ModelRegistry,
    StructuredOutputError,
)

# Backend implementations
from clearthread.models.ollama_backend import OllamaBackend
from clearthread.models.llamacpp_backend import LlamaCppBackend
from clearthread.models.mlx_backend import MLXBackend

# Vision and Image models
from clearthread.models.qwen_vision import QwenVisionModelProvider
from clearthread.models.wan_image import WANImageModelProvider
from clearthread.models.visual_persona import (
    VisualPersona,
    VisualPersonaComposer,
)

__all__ = [
    # Base models
    "ContentCategory",
    "EvidenceReference",
    "ExclusionState",
    "Model",
    "ProvenanceRef",
    "StorageBackend",
    "UserReviewState",
    # Episode models
    "Episode",
    "EpisodeStatus",
    "EpisodeType",
    "MessageRef",
    # Finding models
    "ConfidenceLevel",
    "Finding",
    "FindingStatus",
    "ReflectionQuestionEntry",
    # LoRA models
    "LoRAAdapter",
    "LoRAComposition",
    "LoRAFormat",
    "LoRAStore",
    "LoRATask",
    "LoRAType",
    "Persona",
    "get_image_lora_presets",
    "get_text_lora_presets",
    "get_vision_lora_presets",
    # Message models
    "AttachmentRef",
    "Message",
    "MessageType",
    "Reaction",
    # Participant models
    "Participant",
    "RelationshipCategory",
    # Provenance models
    "ProvenanceRecord",
    "ProvenanceStep",
    "ProvenanceStepType",
    # Reflection question models
    "ReflectionQuestion",
    # Relationship chapter models
    "ChapterSection",
    "ChapterSectionType",
    "RelationshipChapter",
    # Therapy brief models
    "BriefDetailLevel",
    "BriefSectionType",
    "TherapyBrief",
    # Model Provider
    "ModelDownloader",
    "ModelProvider",
    "ModelRegistry",
    "StructuredOutputError",
    # Backend implementations
    "OllamaBackend",
    "LlamaCppBackend",
    "MLXBackend",
    # Vision and Image models
    "QwenVisionModelProvider",
    "WANImageModelProvider",
    "VisualPersona",
    "VisualPersonaComposer",
]
