//! Analyze commands for Tauri.

use serde::{Deserialize, Serialize};
use tauri::State;
use crate::state::{AppState, AnalysisState};

/// Analysis request payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct AnalysisRequest {
    /// Phases to run (episodes, patterns, growth, reflection).
    pub phases: Vec<String>,
    /// Optional output directory.
    pub output_dir: Option<String>,
}

/// Analysis response payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct AnalysisResponse {
    /// Whether the analysis succeeded.
    pub success: bool,
    /// Number of episodes found.
    pub episodes_found: u32,
    /// Number of pattern findings.
    pub findings_count: u32,
    /// Number of growth findings.
    pub growth_findings_count: u32,
    /// Number of reflection questions generated.
    pub reflection_questions: u32,
    /// List of errors.
    pub errors: Vec<String>,
}

/// Tauri command: run episode detection.
#[tauri::command]
pub async fn run_episode_detection(
    state: State<AppState>,
) -> Result<u32, String> {
    let mut analysis_state = state.analysis_state.lock().await;
    analysis_state.is_analyzing = true;
    analysis_state.current_phase = "episodes".to_string();

    let count = execute_python_analyze("episodes", &state.data_dir).await?;

    analysis_state.episodes_found = count;
    analysis_state.is_analyzing = false;

    Ok(count)
}

/// Tauri command: run pattern analysis.
#[tauri::command]
pub async fn run_pattern_analysis(
    state: State<AppState>,
) -> Result<u32, String> {
    let mut analysis_state = state.analysis_state.lock().await;
    analysis_state.is_analyzing = true;
    analysis_state.current_phase = "patterns".to_string();

    let count = execute_python_analyze("patterns", &state.data_dir).await?;

    analysis_state.findings_count = count;
    analysis_state.is_analyzing = false;

    Ok(count)
}

/// Tauri command: run growth analysis.
#[tauri::command]
pub async fn run_growth_analysis(
    state: State<AppState>,
) -> Result<u32, String> {
    let mut analysis_state = state.analysis_state.lock().await;
    analysis_state.is_analyzing = true;
    analysis_state.current_phase = "growth".to_string();

    let count = execute_python_analyze("growth", &state.data_dir).await?;

    analysis_state.growth_findings_count = count;
    analysis_state.is_analyzing = false;

    Ok(count)
}

/// Tauri command: get current analysis status.
#[tauri::command]
pub async fn get_analysis_status(
    state: State<AppState>,
) -> Result<AnalysisState, String> {
    let analysis_state = state.analysis_state.lock().await;
    Ok(analysis_state.clone())
}

/// Execute Python analyze command via subprocess.
async fn execute_python_analyze(
    phase: &str,
    data_dir: &std::path::Path,
) -> Result<u32, String> {
    let output = tokio::process::Command::new("python")
        .arg("-m")
        .arg("clearthread.cli")
        .arg("analyze")
        .arg("--phase")
        .arg(phase)
        .arg("--output-dir")
        .arg(data_dir.to_string_lossy().to_string())
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python analyze: {}", e))?;

    let count: u32 = serde_json::from_str(
        &String::from_utf8_lossy(&output.stdout)
    ).unwrap_or(0);

    Ok(count)
}
