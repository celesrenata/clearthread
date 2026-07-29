# ClearThread API Reference

## Core Modules

### Import Pipeline

[`ImportPipeline`](src/clearthread/import_pipeline.py:69)

```mermaid
classDiagram
    class ImportPipeline {
        +import_from_zip(zip_path) DataHealthReport
        +import_from_directory(dir_path) DataHealthReport
        +resume_from_checkpoint() bool
        +interrupt_import() void
        +get_health_report() DataHealthReport
    }
    class DataHealthReport {
        +summary str
        +warnings list
        +stats dict
    }
    class Message {
        +id UUID
        +sender_id UUID
        +text str
        +timestamp datetime
    }
    ImportPipeline --> DataHealthReport
    ImportPipeline --> Message
```

```python
class ImportPipeline:
    def import_from_zip(self, zip_path: Path) -> DataHealthReport
    def import_from_directory(self, dir_path: Path) -> DataHealthReport
    def resume_from_checkpoint(self) -> bool
    def interrupt_import(self) -> None
    def get_health_report(self) -> DataHealthReport
```

### Storage

[`SourceDataVault`](src/clearthread/storage/source_vault.py:70)

```mermaid
classDiagram
    class SourceDataVault {
        +import_record(source_file) SourceRecord
        +get_record(record_id) SourceRecord|None
        +get_records_by_batch(batch_id) list[SourceRecord]
    }
    class NormalizedStore {
        +save_message(message) bool
        +get_message(message_id) Message|None
        +query(filters) QueryResult
    }
    class MediaStore {
        +add_media(media) UUID
        +get_media_by_message(message_id) list[MediaRecord]
        +get_sensitive_media() list[MediaRecord]
    }
    class EncryptionLayer {
        +derive_key(passphrase) KeyMaterial
        +encrypt(data) bytes
        +decrypt(data) bytes
        +authenticate(passphrase) bool
    }
    SourceDataVault <|-- NormalizedStore
    SourceDataVault <|-- MediaStore
    SourceDataVault <|-- EncryptionLayer
```

```python
class SourceDataVault:
    def import_record(self, source_file: Path) -> SourceRecord
    def get_record(self, record_id: UUID) -> SourceRecord | None
    def get_records_by_batch(self, batch_id: str) -> list[SourceRecord]

class NormalizedStore:
    def save_message(self, message: Message) -> bool
    def get_message(self, message_id: UUID) -> Message | None
    def query(self, filters: QueryFilter) -> QueryResult

class MediaStore:
    def add_media(self, media: MediaRecord) -> UUID
    def get_media_by_message(self, message_id: UUID) -> list[MediaRecord]
    def get_sensitive_media(self) -> list[MediaRecord]

class EncryptionLayer:
    def derive_key(self, passphrase: str) -> KeyMaterial
    def encrypt(self, data: bytes) -> bytes
    def decrypt(self, data: bytes) -> bytes
    def authenticate(self, passphrase: str) -> bool
```

### Analysis

[`EpisodeEngine`](src/clearthread/analysis/episode_engine.py:47)

```mermaid
graph TB
    subgraph Analysis["Analysis Engine"]
        EpisodeEngine["EpisodeEngine"]
        PatternAnalyzer["PatternAnalyzer"]
        GrowthAnalyzer["GrowthAnalyzer"]
        ReflectionQ["ReflectionQuestionGenerator"]
    end
    subgraph Input["Input"]
        Messages["list[Message]"]
    end
    subgraph Output["Output"]
        Episodes["list[Episode]"]
        Patterns["list[PatternResult]"]
        Growth["list[GrowthFinding]"]
        Questions["list[ReflectionQuestion]"]
    end
    Messages --> EpisodeEngine
    Messages --> PatternAnalyzer
    Messages --> GrowthAnalyzer
    EpisodeEngine --> Episodes
    PatternAnalyzer --> Patterns
    GrowthAnalyzer --> Growth
    ReflectionQ --> Questions
```

```python
class EpisodeEngine:
    def propose_episodes(self, messages: list[Message]) -> list[EpisodeProposal]
    def accept_episode(self, episode_id: UUID) -> bool
    def reject_episode(self, episode_id: UUID) -> bool
    def get_review_inbox(self, limit: int) -> list[Episode]

class PatternAnalyzer:
    def analyze(self, messages: list[Message]) -> list[PatternResult]
    def get_patterns_by_type(self, pattern_type: PatternType) -> list[PatternResult]

class GrowthAnalyzer:
    def analyze(self, messages: list[Message]) -> list[GrowthFinding]
    def get_growth_indicators(self) -> list[GrowthIndicator]
```

### Search

[`SearchEngine`](src/clearthread/search/engine.py:42)

```mermaid
classDiagram
    class SearchEngine {
        +search(query, semantic) list[SearchResult]
        +save_query(name, query) bool
        +get_saved_queries() list[dict]
    }
    class FullTextSearchEngine {
        +index_message(message_id, text) bool
        +search(query) list[SearchResult]
    }
    class SemanticSearchEngine {
        +compute_embedding(text) list[float]
        +search_semantic(query) list[SearchResult]
    }
    SearchEngine <|-- FullTextSearchEngine
    SearchEngine <|-- SemanticSearchEngine
```

```python
class SearchEngine:
    def search(self, query: str, semantic: bool = False) -> list[SearchResult]
    def save_query(self, name: str, query: SearchQuery) -> bool
    def get_saved_queries(self) -> list[dict]
```

### Export

[`ExportEngine`](src/clearthread/export/engine.py:66)

```mermaid
graph TB
    subgraph Export["Export Engine"]
        ExportEngine["ExportEngine"]
        subgraph Formats["Export Formats"]
            Markdown["MarkdownExporter"]
            PDF["PDFExporter"]
            JSON["JSONExporter"]
        end
    end
    ExportEngine --> Markdown
    ExportEngine --> PDF
    ExportEngine --> JSON
```

```python
class ExportEngine:
    def export(self, items: list[ExportItem], format: ExportFormat) -> Path
    def export_markdown(self, items: list[ExportItem]) -> Path
    def export_pdf(self, items: list[ExportItem]) -> Path
    def export_json(self, items: list[ExportItem]) -> Path
```

### Models

[`ModelProvider`](src/clearthread/models/model_provider.py:57)

```mermaid
classDiagram
    class ModelProvider {
        <<ABC>>
        +generate(prompt, kwargs) str
        +generate_structured(prompt, schema) dict
        +embed(text, kwargs) list[float]
        +apply_lora(adapter) void
        +health_check() dict
    }
    class OllamaBackend {
        +DEFAULT_URL = "http://localhost:11434"
    }
    class LlamaCppBackend {
        +__init__(model_path, n_ctx)
    }
    class MLXBackend {
        +__init__(model_path, max_tokens)
    }
    ModelProvider <|-- OllamaBackend
    ModelProvider <|-- LlamaCppBackend
    ModelProvider <|-- MLXBackend
```

```python
class ModelProvider(ABC):
    def generate(self, prompt: str, **kwargs) -> str
    def generate_structured(self, prompt: str, schema: dict) -> dict
    def embed(self, text: str, **kwargs) -> list[float]
    def apply_lora(self, adapter: LoRAAdapter) -> None
    def health_check(self) -> dict

class OllamaBackend(ModelProvider):
    DEFAULT_URL = "http://localhost:11434"

class LlamaCppBackend(ModelProvider):
    def __init__(self, model_path: Path, n_ctx: int = 4096)

class MLXBackend(ModelProvider):
    def __init__(self, model_path: Path, max_tokens: int = 4096)
```

### LoRA

[`LoRAAdapter`](src/clearthread/models/lora.py:45)

```mermaid
classDiagram
    class LoRAAdapter {
        +id UUID
        +name str
        +adapter_type LoRAType
        +weight float
        +file_path Path
    }
    class Persona {
        +add_text_adapter(adapter) void
        +set_vision_adapter(adapter) void
        +get_effective_config() dict
    }
    class LoRAStore {
        +add_adapter(adapter) str
        +add_persona(persona) str
        +switch_persona(persona_id) bool
        +blend_personas(persona_ids) Persona
    }
    LoRAStore --> LoRAAdapter
    LoRAStore --> Persona
```

```python
class LoRAAdapter:
    id: UUID
    name: str
    adapter_type: LoRAType
    weight: float
    file_path: Path

class Persona:
    def add_text_adapter(self, adapter: LoRAAdapter)
    def set_vision_adapter(self, adapter: LoRAAdapter)
    def get_effective_config(self) -> dict

class LoRAStore:
    def add_adapter(self, adapter: LoRAAdapter) -> str
    def add_persona(self, persona: Persona) -> str
    def switch_persona(self, persona_id: UUID) -> bool
    def blend_personas(self, persona_ids: list[UUID]) -> Persona
```

## CLI Commands

```mermaid
graph LR
    subgraph CLI["ClearThread CLI"]
        Import["import INPUT_PATH"]
        Analyze["analyze [--phase PHASE]"]
        Search["search QUERY"]
        Export["export [--format FORMAT]"]
        Serve["serve"]
    end
    Import --> Storage["Storage"]
    Analyze --> Analysis["Analysis"]
    Search --> SearchEng["Search Engine"]
    Export --> ExportEng["Export Engine"]
    Serve --> API["API Server"]
```

```bash
# Import data
clearthread import INPUT_PATH [--output-dir DIR] [--zip]

# Run analysis
clearthread analyze [--phase PHASE] [--output-dir DIR]

# Search
clearthread search QUERY [--semantic]

# Export
clearthread export [--format FORMAT] [--output-dir DIR]

# Start server
clearthread serve
```

## Data Models

### Message

```mermaid
classDiagram
    class Message {
        +id UUID
        +sender_id UUID
        +conversation_id UUID
        +text str
        +timestamp datetime
        +message_type MessageType
        +content_hash str
    }
```

```python
@dataclass
class Message:
    id: UUID
    sender_id: UUID
    conversation_id: UUID
    text: str
    timestamp: datetime
    message_type: MessageType
    content_hash: str
```

### Participant

```mermaid
classDiagram
    class Participant {
        +id UUID
        +name str
        +aliases list[str]
        +relationship_category RelationshipCategory
    }
```

```python
@dataclass
class Participant:
    id: UUID
    name: str
    aliases: list[str]
    relationship_category: RelationshipCategory
```

### Episode

```mermaid
classDiagram
    class Episode {
        +id UUID
        +type EpisodeType
        +status EpisodeStatus
        +messages list[MessageRef]
        +context str
        +confidence float
    }
```

```python
@dataclass
class Episode:
    id: UUID
    type: EpisodeType
    status: EpisodeStatus
    messages: list[MessageRef]
    context: str
    confidence: float
```

### Finding

```mermaid
classDiagram
    class Finding {
        +id UUID
        +title str
        +description str
        +confidence ConfidenceLevel
        +evidence list[EvidenceReference]
        +reflection_questions list[ReflectionQuestion]
    }
```

```python
@dataclass
class Finding:
    id: UUID
    title: str
    description: str
    confidence: ConfidenceLevel
    evidence: list[EvidenceReference]
    reflection_questions: list[ReflectionQuestion]
```
