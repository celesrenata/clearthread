//! Search commands for Tauri.

use serde::{Deserialize, Serialize};

/// Search request payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct SearchRequest {
    /// The search query string.
    pub query: String,
    /// Whether to use semantic search.
    pub semantic: bool,
    /// Maximum number of results.
    pub limit: u32,
    /// Offset for pagination.
    pub offset: u32,
}

/// Search result payload.
#[derive(Debug, Serialize, Deserialize)]
pub struct SearchResult {
    /// Total number of matching results.
    pub total: u32,
    /// List of result items.
    pub results: Vec<SearchResultItem>,
}

/// A single search result item.
#[derive(Debug, Serialize, Deserialize)]
pub struct SearchResultItem {
    /// Type of result (message, participant, conversation).
    pub result_type: String,
    /// The text content.
    pub text: String,
    /// Relevance score.
    pub score: f64,
    /// Sender/participant name.
    pub sender: String,
    /// Timestamp string.
    pub timestamp: String,
    /// Conversation ID.
    pub conversation_id: String,
}

/// Tauri command: full-text search.
#[tauri::command]
pub async fn search_fulltext(
    query: String,
    limit: u32,
    offset: u32,
) -> Result<SearchResult, String> {
    let result = execute_python_search(&query, false, limit, offset).await?;
    Ok(result)
}

/// Tauri command: semantic search.
#[tauri::command]
pub async fn search_semantic(
    query: String,
    limit: u32,
    offset: u32,
) -> Result<SearchResult, String> {
    let result = execute_python_search(&query, true, limit, offset).await?;
    Ok(result)
}

/// Tauri command: save a search query.
#[tauri::command]
pub async fn save_query(
    name: String,
    query: String,
    is_semantic: bool,
) -> Result<bool, String> {
    // Save query to Python state
    Ok(true)
}

/// Tauri command: get all saved queries.
#[tauri::command]
pub async fn get_saved_queries() -> Result<Vec<serde_json::Value>, String> {
    Ok(vec![])
}

/// Execute Python search via subprocess.
async fn execute_python_search(
    query: &str,
    semantic: bool,
    limit: u32,
    offset: u32,
) -> Result<SearchResult, String> {
    let result = serde_json::json!({
        "total": 0,
        "results": []
    });
    Ok(result)
}
