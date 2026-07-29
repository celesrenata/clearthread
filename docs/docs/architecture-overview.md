# ClearThread Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph App["ClearThread Application"]
        subgraph TauriShell["Tauri Shell<br/>(Rust + React)"]
            Window["Window Mgmt"]
            Tray["Tray Icon"]
            Menu["Menu Bar"]
            Cmds["Commands"]
            State["State Mgmt"]
            FileIO["File I/O"]
        end
        subgraph PythonCore["Python Core"]
            Import["Import<br/>Pipeline"]
            Storage["Storage"]
            Analysis["Analysis"]
            Search["Search"]
            Export["Export"]
        end
        subgraph AILayer["AI Model Layer<br/>(Ollama/MLX/llama.cpp)"]
            ModelProvider["Model Provider"]
            QwenVL["Qwen Vision"]
            WAN["WAN Image"]
            LoRA["LoRA Adapters"]
            ModelReg["Model Registry"]
            ModelDL["Model Downloader"]
        end
    end
    subgraph StorageLayer["Data Storage Layer"]
        SourceVault["SourceVault<br/>(Immutable)"]
        NormStore["Normalized<br/>Store"]
        MediaStore["Media<br/>Store"]
        Encrypt["Encryption<br/>Layer"]
    end
    subgraph External["External Dependencies"]
        Ollama["Ollama<br/>(localhost)"]
        LlamaCpp["llama.cpp<br/>(CPU/GPU)"]
        MLX["MLX<br/>(Apple MPS)"]
        SQLite["SQLite/FS<br/>(Storage)"]
    end
    TauriShell --> PythonCore
    PythonCore --> AILayer
    PythonCore --> StorageLayer
    AILayer --> External
    StorageLayer --> External
```

## Component Diagram

```mermaid
graph TB
    CLI["CLI Entry"]
    subgraph Import["Import Pipeline"]
        Parser["ZIP/Dir Parser"]
        JSON["JSON Decoder"]
        Encoder["Encoder Fallback"]
    end
    subgraph Storage["Data Storage"]
        SourceVault["Source Data Vault<br/>(Immutable source data)"]
        NormStore["Normalized Store<br/>(Analytical storage)"]
    end
    subgraph Analysis["Analysis Engines"]
        Episode["Episode<br/>Engine"]
        Pattern["Pattern<br/>Analyzer"]
        Growth["Growth<br/>Analyzer"]
    end
    Search["Search Engine<br/>┌────────────────┐<br/>│ Full-Text      │<br/>│ Semantic       │<br/>└────────────────┘"]
    subgraph Export["Export Engine"]
        MD["Markdown"]
        PDF["PDF"]
        JSON["JSON"]
    end
    CLI --> Import
    Import --> SourceVault
    SourceVault --> NormStore
    NormStore --> Episode
    NormStore --> Pattern
    NormStore --> Growth
    Episode --> Search
    Pattern --> Search
    Growth --> Search
    Search --> Export
    Export --> MD
    Export --> PDF
    Export --> JSON
```

## Data Flow

```mermaid
graph LR
    subgraph ImportPhase["1. Import Phase"]
        FB["Facebook Export<br/>(ZIP)"]
        Extract["Extract & Parse"]
        Vault["Source Data Vault<br/>(immutable)"]
        Normalize["Normalize &<br/>Deduplicate"]
        Store["Normalized Store<br/>(SQLite)"]
    end
    subgraph AnalysisPhase["2. Analysis Phase"]
        NormStore["Normalized Store"]
        EpisodeDet["Episode Detection<br/>(time gaps, threads)"]
        PatternAn["Pattern Analysis<br/>(frequency, timing)"]
        GrowthAn["Growth Analysis<br/>(evolution, resilience)"]
        ReflQ["Reflection Questions<br/>(AI-generated)"]
    end
    subgraph AIProcessing["3. AI Processing"]
        Messages["Normalized Messages"]
        ModelProv["Model Provider<br/>(Ollama/MLX/llama.cpp)"]
        LoRAApp["LoRA Adapters<br/>applied"]
        Output["Structured Output<br/>(episodes, findings)"]
    end
    subgraph ExportPhase["4. Export Phase"]
        Results["Analysis Results"]
        Format["Format Selection<br/>(MD/PDF/JSON)"]
        ExportOut["Export Output"]
    end
    FB --> Extract
    Extract --> Vault
    Vault --> Normalize
    Normalize --> Store
    Store --> NormStore
    NormStore --> EpisodeDet
    EpisodeDet --> PatternAn
    PatternAn --> GrowthAn
    GrowthAn --> ReflQ
    Messages --> ModelProv
    ModelProv --> LoRAApp
    LoRAApp --> Output
    Results --> Format
    Format --> ExportOut
```

## Key Design Decisions

### Local-First

- All data stored locally in SQLite
- No cloud dependency for core functionality
- AI models can run locally (Ollama, MLX)

### Immutable Source

- Original Facebook exports preserved
- Source vault maintains raw data
- Re-imports are idempotent

### Modular AI

- Model provider abstraction allows swapping backends
- LoRA adapters for fine-tuning without retraining
- GPU acceleration optional

### Extensible Architecture

- Plugin-style command system in Tauri
- Python analysis pipeline is modular
- Storage backend can be swapped
