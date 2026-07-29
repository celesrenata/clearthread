//! Utility functions for Tauri application.

use std::path::PathBuf;

/// Get the application's data directory.
pub fn get_data_dir() -> Result<PathBuf, String> {
    let dir = dirs::data_dir()
        .ok_or("Could not determine data directory")?
        .join("clearthread");

    std::fs::create_dir_all(&dir)
        .map_err(|e| format!("Failed to create data directory: {}", e))?;

    Ok(dir)
}

/// Get the application's models directory.
pub fn get_models_dir() -> Result<PathBuf, String> {
    Ok(get_data_dir()?.join("models"))
}

/// Get the application's normalized storage directory.
pub fn get_normalized_dir() -> Result<PathBuf, String> {
    Ok(get_data_dir()?.join("normalized"))
}

/// Get the application's export directory.
pub fn get_export_dir() -> Result<PathBuf, String> {
    Ok(get_data_dir()?.join("exports"))
}

/// Get the application's log directory.
pub fn get_log_dir() -> Result<PathBuf, String> {
    let dir = get_data_dir()?.join("logs");
    std::fs::create_dir_all(&dir)
        .map_err(|e| format!("Failed to create log directory: {}", e))?;
    Ok(dir)
}

/// Ensure all required directories exist.
pub fn ensure_directories() -> Result<(), String> {
    let data_dir = get_data_dir()?;
    let dirs = vec![
        data_dir.join("models"),
        data_dir.join("normalized"),
        data_dir.join("exports"),
        data_dir.join("logs"),
        data_dir.join("data"),
    ];

    for dir in dirs {
        std::fs::create_dir_all(&dir)
            .map_err(|e| format!("Failed to create directory {}: {}", dir.display(), e))?;
    }

    Ok(())
}
