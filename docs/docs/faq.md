# ClearThread FAQ

## General

### What is ClearThread?

ClearThread is a local-first desktop application that helps you analyze your Facebook and Messenger data exports. It reconstructs your relationship histories, identifies patterns, and generates insights you can use for personal reflection or therapy sessions.

### Is my data private?

Yes. ClearThread is designed to be local-first:
- Your Facebook data stays on your device
- Analysis happens locally (no cloud processing)
- AI models can run entirely offline
- Optional encryption for stored data

### What platforms are supported?

ClearThread supports:
- **macOS** 10.15+ (Intel and Apple Silicon)
- **Windows** 10+ (64-bit)
- **Linux** Ubuntu 20.04+ (and other distros with WebKitGTK)

## Data Import

### What data can I import?

You can import:
- Facebook Messenger messages (inbox and sent)
- Facebook posts and comments
- Images and media attachments
- Participant information

### How do I export my Facebook data?

1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=downloads)
2. Click "Download your information"
3. Select "Messages" and any other data
4. Choose "JSON" format
5. Click "Create File" and download when ready

### Can I import multiple exports?

Yes. ClearThread supports incremental imports. You can import multiple ZIP files and they will be merged intelligently.

## Analysis

### What kind of analysis does ClearThread provide?

- **Episode Detection**: Identifies conversation clusters and episodes
- **Pattern Analysis**: Finds communication patterns, response times, topic clusters
- **Growth Analysis**: Shows how relationships evolved over time
- **Reflection Questions**: AI-generated questions for deeper insight
- **Therapy Briefs**: Exportable summaries for therapy sessions

### How accurate is the AI analysis?

The accuracy depends on:
- The model used (Qwen2.5, custom models)
- The amount of data
- The quality of your export data

You can review and correct all AI-generated results.

### Can I use my own AI models?

Yes. ClearThread supports:
- Ollama (local models)
- llama.cpp (CPU/GPU)
- MLX (Apple Silicon)
- Custom LoRA adapters

## Usage

### How long does import take?

Import time depends on:
- Size of your data export
- Number of messages
- Whether you include media

Typical imports take 1-5 minutes for most users.

### Does ClearThread use a lot of disk space?

ClearThread is efficient:
- Source data is stored once (immutable)
- Normalized data is compact (SQLite)
- Media can be optionally stored externally
- Total usage is typically 2-3x your original export size

### Can I export my analysis?

Yes. You can export to:
- **Markdown**: Human-readable, editable
- **PDF**: Print-ready format
- **JSON**: Machine-readable

## Technical

### Do I need an internet connection?

No. Once installed, ClearThread works entirely offline:
- Data import and analysis are local
- AI models run locally
- Export is local

Internet is only needed for:
- Initial app updates
- Optional model downloads

### What AI models does ClearThread use?

- **Qwen2.5**: For text analysis and pattern detection
- **Qwen2.5-VL**: For vision tasks (participant recognition)
- **WAN 2.1**: For image style reconstruction

### Can I run ClearThread on a server?

Yes. ClearThread can run as:
- Desktop application (with UI)
- CLI tool (headless)
- Docker container
- Web service (via Tauri web view)

## Troubleshooting

### Import fails with "Invalid ZIP"

- Ensure the ZIP file is not corrupted
- Try extracting and re-zipping
- Check that JSON files are valid

### AI features not working

- Ensure Ollama is running: `ollama serve`
- Check GPU availability
- Verify model files are downloaded

### Slow performance

- Close other applications
- Check disk space
- Try switching to CPU mode in Settings
- Consider excluding media from import

### Data not showing up

- Check that the import completed successfully
- Verify the data directory is correct
- Try re-importing with verbose logging
