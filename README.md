# ClearThread

Local-first desktop application for analyzing Facebook/Messenger data exports with AI-powered pattern detection, episode reconstruction, and therapy brief generation.

## Features

```mermaid
graph TB
    subgraph Core["Core Features"]
        Vault["Immutable Source<br/>Data Vault"]
        Storage["Normalized<br/>Storage"]
        Episodes["Episode<br/>Detection"]
        Patterns["Pattern<br/>Analysis"]
        Growth["Growth<br/>Analysis"]
        Reflection["Reflection<br/>Questions"]
    end
    subgraph SearchExport["Search & Export"]
        FullText["Full-Text<br/>Search"]
        Semantic["Semantic<br/>Search"]
        Markdown["Markdown<br/>Export"]
        PDF["PDF<br/>Export"]
        JSON["JSON<br/>Export"]
    end
    subgraph AI["AI & Models"]
        LoRA["LoRA<br/>Adapters"]
        Encryption["AES-256-GCM<br/>Encryption"]
        Docker["Docker<br/>Support"]
    end
    Vault --> Storage
    Storage --> Episodes
    Storage --> Patterns
    Patterns --> Growth
    Episodes --> FullText
    Patterns --> Semantic
    FullText --> Markdown
    Semantic --> PDF
    Growth --> JSON
    LoRA --> AI
    Encryption --> AI
    Docker --> AI
```

- **Immutable Source Data Vault**: Original data never modified
- **Normalized Storage**: Source-independent canonical storage with referential integrity
- **Episode Detection**: Time-gap analysis, semantic clustering, entity/topic continuity
- **Pattern Analysis**: 12+ communication patterns with counterexample search
- **Growth Analysis**: Patterns That Protected Me, People Who Showed Up, Growth Across Time
- **Reflection Questions**: Non-directive, data-element referencing
- **Full-Text and Semantic Search**: TF/recency ranking, cosine similarity
- **Export**: Markdown, PDF (A4/Letter), JSON
- **LoRA Adapters**: Modular AI for text, vision, and image analysis
- **Encryption**: AES-256-GCM at-rest encryption
- **Docker Support**: CUDA/MPS/ROCm GPU support

## Installation

```bash
pip install clearthread
```

## Usage

```bash
# Import Facebook data export
clearthread import path/to/export.zip

# Run analysis
clearthread analyze

# Search
clearthread search "keyword"

# Export
clearthread export --format markdown
```

```mermaid
graph LR
    FB["Facebook Export<br/>(ZIP)"]
    Import["Import"]
    Vault["Source Vault"]
    Analysis["Analysis"]
    Export["Export"]
    FB --> Import
    Import --> Vault
    Vault --> Analysis
    Analysis --> Export
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check
mypy src/
```

## Docker

```bash
docker-compose up -d
```

```mermaid
graph TB
    subgraph Container["ClearThread Container"]
        subgraph Tauri["Tauri UI"]
            UI["React Frontend"]
            Rust["Rust Backend"]
        end
        subgraph Python["Python Core"]
            Import["Import Pipeline"]
            Analysis["Analysis Engine"]
            Search["Search Engine"]
            Export["Export Engine"]
        end
        subgraph Models["AI Models"]
            Ollama["Ollama"]
            MLX["MLX"]
            LlamaCpp["llama.cpp"]
        end
        subgraph GPU["GPU Acceleration"]
            CUDA["CUDA (NVIDIA)"]
            MPS["MPS (Apple)"]
            ROCm["ROCm (AMD)"]
        end
    end
    Tauri --> Python
    Python --> Models
    Models --> GPU
```

## Documentation

- [Architecture Overview](docs/docs/architecture-overview.md)
- [Developer Guide](docs/docs/developer-guide.md)
- [User Guide](docs/docs/user-guide.md)
- [API Reference](docs/docs/api-reference.md)
- [Getting Started](docs/docs/getting-started.md)
- [FAQ](docs/docs/faq.md)
- [Contributing](docs/docs/contributing.md)
- [Tasks & Roadmap](docs/tasks.md)
- [Design Specifications](docs/design.md)
