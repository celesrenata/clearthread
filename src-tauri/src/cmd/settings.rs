//! Settings commands for Tauri.

use serde::{Deserialize, Serialize};
use tauri::State;
use crate::state::{AppState, Settings};

/// Tauri command: get current settings.
#[tauri::command]
pub async fn get_settings(
    state: State<AppState>,
) -> Result<Settings, String> {
    let settings = state.settings.lock().await;
    Ok(settings.clone())
}

/// Tauri command: update settings.
#[tauri::command]
pub async fn update_settings(
    state: State<AppState>,
    settings: Settings,
) -> Result<bool, String> {
    let mut current_settings = state.settings.lock().await;
    *current_settings = settings;
    Ok(true)
}

/// Tauri command: lock encryption.
#[tauri::command]
pub async fn lock_encryption(
    state: State<AppState>,
) -> Result<bool, String> {
    let mut settings = state.settings.lock().await;
    settings.encryption_enabled = false;
    Ok(true)
}

/// Tauri command: unlock encryption.
#[tauri::command]
pub async fn unlock_encryption(
    state: State<AppState>,
    passphrase: String,
) -> Result<bool, String> {
    let mut settings = state.settings.lock().await;
    settings.encryption_enabled = true;
    Ok(true)
}
