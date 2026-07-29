# Getting Started with ClearThread

## Quick Start

### 1. Install ClearThread

Download the latest version for your platform:

- **macOS**: `clearthread-0.1.0.dmg`
- **Windows**: `clearthread-0.1.0.msi`
- **Linux**: `clearthread-0.1.0.deb`

Or install via package manager:

```bash
# macOS (Homebrew)
brew install clearthread

# Linux (apt)
sudo apt install clearthread

# Windows (winget)
winget install ClearThread
```

### 2. Export Your Facebook Data

1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=downloads)
2. Click "Download your information"
3. Select "Messages" (and any other data you want)
4. Choose "JSON" format
5. Click "Create File" and download

### 3. Import Your Data

1. Open ClearThread
2. Click "Import" in the sidebar
3. Click "Choose File" and select your Facebook export ZIP
4. Click "Start Import"
5. Wait for the import to complete

### 4. Explore Your Data

After import, you'll see:

- **Library**: All your conversations
- **Timeline**: Chronological view of messages
- **Episodes**: Detected conversation episodes
- **Patterns**: Interaction patterns
- **Growth**: Relationship growth analysis

## System Requirements

### Minimum
- **OS**: macOS 10.15+, Windows 10+, Ubuntu 20.04+
- **RAM**: 4 GB
- **Storage**: 500 MB
- **CPU**: Dual-core

### Recommended
- **OS**: macOS 12+, Windows 11+, Ubuntu 22.04+
- **RAM**: 8 GB
- **Storage**: 2 GB
- **CPU**: Quad-core

### For AI Features
- **GPU**: NVIDIA GPU with CUDA 12+ or Apple Silicon
- **RAM**: 16 GB for local model inference

## Next Steps

- Read the [User Guide](user-guide.md) for detailed instructions
- Check the [API Reference](api-reference.md) for developers
- Explore the [Architecture Overview](architecture-overview.md)

## Troubleshooting

### Import Fails
- Ensure your ZIP file is not corrupted
- Check that the JSON files are valid
- Try importing a smaller subset first

### AI Features Not Working
- Ensure Ollama is running: `ollama serve`
- Check GPU availability: `nvidia-smi` (NVIDIA) or check MPS (Apple)

### Performance Issues
- Close other applications
- Check disk space
- Try switching to CPU mode in Settings
