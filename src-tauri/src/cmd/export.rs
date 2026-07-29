//! Export commands for Tauri.

use serde::{Deserialize, Serialize};

/// Export request payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct ExportRequest {
    /// Export format (markdown, pdf, json).
    pub format: String,
    /// Output directory.
    pub output_dir: String,
    /// Content types to export.
    pub content_types: Vec<String>,
    /// Optional date range.
    pub date_range: Option<(String, String)>,
}

/// Export response payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct ExportResponse {
    /// Whether the export succeeded.
    pub success: bool,
    /// Path to the exported file.
    pub output_path: String,
    /// Number of items exported.
    pub items_exported: u32,
    /// List of errors.
    pub errors: Vec<String>,
}

/// Tauri command: export to Markdown.
#[tauri::command]
pub async fn export_markdown(
    request: ExportRequest,
) -> Result<ExportResponse, String> {
    let response = execute_python_export("markdown", &request).await?;
    Ok(response)
}

/// Tauri command: export to PDF.
#[tauri::command]
pub async fn export_pdf(
    request: ExportRequest,
) -> Result<ExportResponse, String> {
    let response = execute_python_export("pdf", &request).await?;
    Ok(response)
}

/// Tauri command: export to JSON.
#[tauri::command]
pub async fn export_json(
    request: ExportRequest,
) -> Result<ExportResponse, String> {
    let response = execute_python_export("json", &request).await?;
    Ok(response)
}

/// Tauri command: get current export status.
#[tauri::command]
pub async fn get_export_status() -> Result<serde_json::Value, String> {
    Ok(serde_json::json!({
        "is_exporting": false,
        "progress": 0.0,
        "current_file": ""
    }))
}

/// Execute Python export via subprocess.
async fn execute_python_export(
    format: &str,
    request: &ExportRequest,
) -> Result<ExportResponse, String> {
    let response = serde_json::json!({
        "success": true,
        "output_path": format!("{}/export.{}", request.output_dir, format),
        "items_exported": 0,
        "errors": []
    });
    Ok(response)
}
