# ClearThread User Guide

## Getting Started

### Installation

ClearThread is available for Windows, macOS, and Linux. Download the latest version from the [releases page](https://github.com/celesrenata/clearthread/releases).

### First Launch

When you first launch ClearThread, you'll see:

1. **Import Dashboard** - Where you start by importing your Facebook data
2. **Sidebar Navigation** - Access all views from the left sidebar
3. **Status Bar** - Shows current import/analysis progress

## Importing Your Data

### Step 1: Export from Facebook

1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=downloads)
2. Click "Download your information"
3. Select "Messages" and any other data you want
4. Choose "ZIP" format
5. Click "Create File" and download when ready

### Step 2: Import to ClearThread

1. Click "Import" in the sidebar
2. Click "Choose File" and select your ZIP export
3. Click "Start Import"
4. Wait for the import to complete (progress shown in status bar)

### Step 3: Review Your Data

After import:

1. **Library** - View all your conversations
2. **Timeline** - See messages chronologically
3. **Episodes** - Review detected conversation episodes
4. **Patterns** - See interaction patterns identified

## Using the Analysis Features

### Episode Detection

Episodes are detected conversation clusters. You can:

- **Accept** episodes you want to keep
- **Reject** episodes that don't match
- **Merge** related episodes
- **Split** episodes that cover multiple topics

### Pattern Analysis

The pattern analyzer identifies:

- Communication frequency patterns
- Response time patterns
- Topic clustering
- Emotional tone patterns

### Growth Analysis

Growth findings show:

- How your relationship evolved
- Positive changes over time
- Areas of strength
- Areas for reflection

## Exporting Your Analysis

### Export Options

1. **Markdown** - Human-readable, editable
2. **PDF** - Print-ready format
3. **JSON** - Machine-readable, for further processing

### Exporting a Therapy Brief

1. Go to "Brief Builder"
2. Select the episodes and patterns to include
3. Add your notes
4. Click "Export Brief"

## Settings

### Model Settings

- **Model Provider** - Choose Ollama, llama.cpp, or MLX
- **GPU Backend** - Auto-detected, can be overridden
- **Encryption** - Enable at-rest encryption

### Appearance

- **Theme** - Light or Dark mode
- **Language** - Select your language

## Tips

- Use the tray icon for quick access
- Analysis runs in the background
- Your data stays local - nothing is uploaded
- You can re-run analysis at any time
