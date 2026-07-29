# ClearThread Developer Guide

## Project Structure

```mermaid
graph TB
    subgraph ClearThread["clearthread/"]
        subgraph Src["src/"]
            subgraph PythonPkg["clearthread/<br/>(Python package)"]
                Analysis["analysis/<br/>Analysis engine"]
                Export["export/<br/>Export functionality"]
                Models["models/<br/>Data models"]
                Search["search/<br/>Search engine"]
                Storage["storage/<br/>Storage backends"]
                CLI["cli.py<br/>CLI entry point"]
                Import["import_pipeline.py"]
                Update["update.py<br/>Update manager"]
            end
            subgraph Tauri["tauri/<br/>(Tauri Rust layer)"]
                Cmds["cmd/<br/>Tauri commands"]
                Styles["styles/<br/>CSS styles"]
                MainRS["main.rs<br/>Entry point"]
                LibRS["lib.rs<br/>Library"]
                StateRS["state.rs<br/>State management"]
                UtilsRS["utils.rs<br/>Utilities"]
            end
        end
        Tests["tests/<br/>Test suite"]
        Docs["docs/<br/>Documentation"]
        ModelsDir["models/<br/>AI model storage"]
        PyProject["pyproject.toml"]
        Dockerfile["Dockerfile"]
    end
    PythonPkg --> Analysis
    PythonPkg --> Export
    PythonPkg --> Models
    PythonPkg --> Search
    PythonPkg --> Storage
    Tauri --> Cmds
    Tauri --> Styles
    Tauri --> MainRS
    Tauri --> LibRS
```

## Building

### Prerequisites

- Python 3.10+
- Rust 1.77+
- Node.js 18+ (for frontend)

### Python Package

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/clearthread

# Linting
ruff check src/clearthread
```

### Tauri Desktop

```bash
# Enter Tauri directory
cd src-tauri

# Install dependencies
cargo build

# Run in dev mode
cargo tauri dev

# Build for production
cargo tauri build
```

### Full Build

```bash
# Build Python package
pip install build
python -m build

# Build Tauri app
cd src-tauri && cargo tauri build && cd ..

# Build Docker image
docker build -t clearthread:latest .
```

## Development Workflow

### Running the App

```mermaid
graph LR
    subgraph PythonCLI["Python CLI"]
        CLI["python -m<br/>clearthread.cli"]
    end
    subgraph TauriDev["Tauri Dev Mode"]
        Tauri["cd src-tauri<br/>&& cargo tauri dev"]
    end
    subgraph GPU["GPU Support"]
        CUDA["CUDA_VISIBLE<br/>_DEVICES=0"]
    end
    CLI --> GPU
    Tauri --> GPU
```

```bash
# Run Python CLI
python -m clearthread.cli

# Run Tauri dev mode
cd src-tauri && cargo tauri dev

# Run with GPU support
CUDA_VISIBLE_DEVICES=0 python -m clearthread.cli
```

### Testing

```mermaid
graph TB
    subgraph Testing["Test Suite"]
        All["pytest tests/<br/>-v"]
        Coverage["--cov=clearthread<br/>--cov-report=html"]
        Specific["pytest tests/<br/>test_models.py"]
    end
    All --> Coverage
    All --> Specific
```

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=clearthread --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

### Code Style

```bash
# Format code
ruff format src/clearthread

# Check types
mypy src/clearthread

# Fix imports
ruff check --fix src/clearthread
```

## Architecture

### Data Flow

```mermaid
graph LR
    FB["Facebook Export"]
    Import["Import<br/>Pipeline"]
    Vault["Source<br/>Vault"]
    NormStore["Normalized<br/>Store"]
    Analysis["Analysis"]
    Export["Export"]
    Storage["Storage<br/>Backend"]
    
    FB --> Import
    Import --> Vault
    Vault --> NormStore
    NormStore --> Analysis
    Analysis --> Export
    Export -.-> Storage
    Vault -.-> Storage
```

### Model Provider

```mermaid
classDiagram
    class ModelProvider {
        <<ABC>>
        +generate()
        +generate_structured()
        +embed()
        +apply_lora()
        +health_check()
    }
    class OllamaBackend {
        +Local model server
        +HTTP API
    }
    class LlamaCppBackend {
        +CPU/GPU support
        +Direct inference
    }
    class MLXBackend {
        +Apple Silicon
        +MPS acceleration
    }
    ModelProvider <|-- OllamaBackend
    ModelProvider <|-- LlamaCppBackend
    ModelProvider <|-- MLXBackend
```

### Tauri Commands

```mermaid
graph TB
    subgraph RustCmds["Rust Commands"]
        ImportCmd["ImportCommands<br/>import_from_zip"]
        AnalyzeCmd["AnalyzeCommands<br/>run_episode_detection"]
        SearchCmd["SearchCommands<br/>search_fulltext"]
        ExportCmd["ExportCommands<br/>export_markdown"]
    end
    subgraph PythonExec["Python Execution"]
        PyImport["import_pipeline.py"]
        PyAnalyze["analysis/"]
        PySearch["search/"]
        PyExport["export/"]
    end
    ImportCmd --> PyImport
    AnalyzeCmd --> PyAnalyze
    SearchCmd --> PySearch
    ExportCmd --> PyExport
```

## Adding New Features

### New Tauri Command

1. Add function to `src-tauri/src/cmd/your_module.rs`
2. Register in `src-tauri/src/main.rs`
3. Add frontend component in `src-tauri/src/components/`
4. Connect via `invoke` in React

### New Python Model

1. Create model class in `src/clearthread/models/`
2. Add to `__init__.py` exports
3. Add tests in `tests/`
4. Update schema if needed

```mermaid
graph TB
    subgraph NewModel["New Python Model Flow"]
        ModelClass["Model class<br/>src/clearthread/models/"]
        InitExport["__init__.py<br/>exports"]
        Tests["tests/<br/>test cases"]
        Schema["Schema<br/>if needed"]
    end
    ModelClass --> InitExport
    ModelClass --> Tests
    ModelClass --> Schema
```

## Docker Development

```mermaid
graph TB
    subgraph Docker["Docker Environment"]
        Compose["docker-compose<br/>up"]
        Tests["pytest<br/>in container"]
        Shell["Interactive<br/>bash shell"]
    end
    Compose --> Tests
    Compose --> Shell
```

```bash
# Build and run
docker-compose up

# Run tests in container
docker-compose run app pytest

# Interactive shell
docker-compose run app bash
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
