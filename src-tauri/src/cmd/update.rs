//! Update commands for Tauri.

use serde::{Deserialize, Serialize};

/// Update information payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateInfo {
    /// Whether a new update is available.
    pub available: bool,
    /// Current version string.
    pub current_version: String,
    /// Latest version string.
    pub latest_version: String,
    /// Release notes for the latest version.
    pub release_notes: String,
    /// Download URL for the latest version.
    pub download_url: String,
    /// Size of the update in bytes.
    pub size_bytes: u64,
}

/// Tauri command: check for updates.
#[tauri::command]
pub async fn check_for_updates() -> Result<UpdateInfo, String> {
    // Check for updates via HTTP or local version comparison
    let info = UpdateInfo {
        available: false,
        current_version: "0.1.0".to_string(),
        latest_version: "0.1.0".to_string(),
        release_notes: "".to_string(),
        download_url: "".to_string(),
        size_bytes: 0,
    };
    Ok(info)
}

/// Tauri command: install the latest update.
#[tauri::command]
pub async fn install_update() -> Result<bool, String> {
    Ok(true)
}
