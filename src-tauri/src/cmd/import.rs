//! Import commands for Tauri.

use serde::{Deserialize, Serialize};
use tauri::State;
use crate::state::{AppState, ImportState};

/// Import request payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct ImportRequest {
    /// Path to the input ZIP or directory.
    pub input_path: String,
    /// Whether the input is a ZIP file.
    pub is_zip: bool,
    /// Optional output directory.
    pub output_dir: Option<String>,
}

/// Import response payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct ImportResponse {
    /// Whether the import succeeded.
    pub success: bool,
    /// Batch ID for this import.
    pub batch_id: String,
    /// Number of messages imported.
    pub messages: u32,
    /// Number of conversations found.
    pub conversations: u32,
    /// Number of participants found.
    pub participants: u32,
    /// Number of attachments processed.
    pub attachments: u32,
    /// Number of duplicates removed.
    pub duplicates: u32,
    /// Number of encoding fixes applied.
    pub encoding_fixes: u32,
    /// List of errors encountered.
    pub errors: Vec<String>,
}

/// Tauri command: import from a ZIP file.
#[tauri::command]
pub async fn import_from_zip(
    state: State<AppState>,
    request: ImportRequest,
) -> Result<ImportResponse, String> {
    let output_dir = request.output_dir.unwrap_or_else(|| {
        state.data_dir.to_string_lossy().to_string()
    });

    let result = execute_python_import(
        &request.input_path,
        &output_dir,
        true,
    ).await?;

    Ok(result)
}

/// Tauri command: import from a directory.
#[tauri::command]
pub async fn import_from_directory(
    state: State<AppState>,
    request: ImportRequest,
) -> Result<ImportResponse, String> {
    let output_dir = request.output_dir.unwrap_or_else(|| {
        state.data_dir.to_string_lossy().to_string()
    });

    let result = execute_python_import(
        &request.input_path,
        &output_dir,
        false,
    ).await?;

    Ok(result)
}

/// Tauri command: get current import status.
#[tauri::command]
pub async fn get_import_status(
    state: State<AppState>,
) -> Result<ImportState, String> {
    let import_state = state.import_state.lock().await;
    Ok(import_state.clone())
}

/// Tauri command: resume import from last checkpoint.
#[tauri::command]
pub async fn resume_import(
    state: State<AppState>,
) -> Result<ImportResponse, String> {
    let result = execute_python_import_resume(&state.data_dir).await?;
    Ok(result)
}

/// Execute Python import pipeline via subprocess.
async fn execute_python_import(
    input_path: &str,
    output_dir: &str,
    is_zip: bool,
) -> Result<ImportResponse, String> {
    // Update state
    let mut import_state = tokio::task::spawn_blocking({
        let state = state.clone();
        async move { state.import_state.clone() }
    })
    .await
    .map_err(|e| format!("Failed to get import state: {}", e))?;

    // Execute Python CLI
    let output = tokio::process::Command::new("python")
        .arg("-m")
        .arg("clearthread.cli")
        .arg("import")
        .arg(input_path)
        .arg("--output-dir")
        .arg(output_dir)
        .arg(if is_zip { "--zip" } else { "" })
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python: {}", e))?;

    // Parse JSON output
    let response: ImportResponse = serde_json::from_str(
        &String::from_utf8_lossy(&output.stdout)
    ).map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}

/// Resume import from checkpoint.
async fn execute_python_import_resume(
    data_dir: &std::path::Path,
) -> Result<ImportResponse, String> {
    let output = tokio::process::Command::new("python")
        .arg("-m")
        .arg("clearthread.cli")
        .arg("import-resume")
        .arg("--output-dir")
        .arg(data_dir.to_string_lossy().to_string())
        .output()
        .await
        .map_err(|e| format!("Failed to resume import: {}", e))?;

    let response: ImportResponse = serde_json::from_str(
        &String::from_utf8_lossy(&output.stdout)
    ).map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(response)
}
