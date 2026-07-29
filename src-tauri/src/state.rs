//! Application state management.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tokio::sync::Mutex;

/// Application state with directory paths.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppState {
    /// Base data directory.
    pub data_dir: PathBuf,
    /// Models directory for AI models.
    pub models_dir: PathBuf,
    /// Normalized storage directory.
    pub normalized_dir: PathBuf,
    /// Export output directory.
    pub export_dir: PathBuf,
    /// Log directory.
    pub log_dir: PathBuf,
    /// Current import state.
    #[serde(skip)]
    pub import_state: std::sync::Arc<Mutex<ImportState>>,
    /// Current analysis state.
    #[serde(skip)]
    pub analysis_state: std::sync::Arc<Mutex<AnalysisState>>,
    /// Current settings.
    #[serde(skip)]
    pub settings: std::sync::Arc<Mutex<Settings>>,
}

impl AppState {
    /// Create a new AppState with the given base directory.
    pub fn new(base_dir: PathBuf) -> Self {
        Self {
            data_dir: base_dir.join("data"),
            models_dir: base_dir.join("models"),
            normalized_dir: base_dir.join("normalized"),
            export_dir: base_dir.join("exports"),
            log_dir: base_dir.join("logs"),
            import_state: std::sync::Arc::new(Mutex::new(ImportState::default())),
            analysis_state: std::sync::Arc::new(Mutex::new(AnalysisState::default())),
            settings: std::sync::Arc::new(Mutex::new(Settings::default())),
        }
    }
}

/// State of an ongoing import operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportState {
    /// Whether an import is currently in progress.
    pub is_importing: bool,
    /// Progress percentage (0.0 to 1.0).
    pub progress: f64,
    /// Current file being processed.
    pub current_file: String,
    /// Total number of files to process.
    pub total_files: u32,
    /// Number of messages processed so far.
    pub messages_processed: u32,
    /// List of errors encountered.
    pub errors: Vec<String>,
}

impl Default for ImportState {
    fn default() -> Self {
        Self {
            is_importing: false,
            progress: 0.0,
            current_file: String::new(),
            total_files: 0,
            messages_processed: 0,
            errors: Vec::new(),
        }
    }
}

/// State of an ongoing analysis operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisState {
    /// Whether an analysis is currently in progress.
    pub is_analyzing: bool,
    /// Current phase name.
    pub current_phase: String,
    /// Number of episodes found.
    pub episodes_found: u32,
    /// Number of pattern findings.
    pub findings_count: u32,
    /// Number of growth findings.
    pub growth_findings_count: u32,
}

impl Default for AnalysisState {
    fn default() -> Self {
        Self {
            is_analyzing: false,
            current_phase: String::new(),
            episodes_found: 0,
            findings_count: 0,
            growth_findings_count: 0,
        }
    }
}

/// Application settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    /// GPU backend type (cuda, rocm, metal, cpu).
    pub gpu_backend: String,
    /// Model provider (ollama, llamacpp, mlx).
    pub model_provider: String,
    /// Whether encryption is enabled.
    pub encryption_enabled: bool,
    /// Whether auto-lock is enabled.
    pub auto_lock: bool,
    /// Auto-lock timeout in seconds.
    pub auto_lock_timeout: u64,
    /// UI theme (light, dark).
    pub theme: String,
    /// UI language.
    pub language: String,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            gpu_backend: "cpu".to_string(),
            model_provider: "ollama".to_string(),
            encryption_enabled: false,
            auto_lock: false,
            auto_lock_timeout: 300,
            theme: "light".to_string(),
            language: "en".to_string(),
        }
    }
}

/// Tray icon state.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrayState {
    /// Whether the main window is visible.
    pub is_visible: bool,
    /// Whether an import is in progress.
    pub is_importing: bool,
    /// Whether a new update is available.
    pub has_updates: bool,
}
