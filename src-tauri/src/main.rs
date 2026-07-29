//! ClearThread Tauri application entry point.

use clearthread_lib::{
    cmd::{
        import::ImportCommands,
        analyze::AnalyzeCommands,
        search::SearchCommands,
        export::ExportCommands,
        settings::SettingsCommands,
        update::UpdateCommands,
    },
    state::{AppState, TrayState},
};
use tauri::Manager;
use tauri_plugin_tray::TrayExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_tray::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            // Initialize application state
            let state = AppState::new(app.path().app_data_dir()?);
            app.manage(state);

            // Initialize tray
            let tray = app.tray_handle();
            tray.set_menu(
                tauri_plugin_tray::TrayMenu::new()
                    .item(&tauri_plugin_tray::TrayItem::new("show").build()?)
                    .item(&tauri_plugin_tray::TrayItem::new("hide").build()?)
                    .separator()
                    .item(&tauri_plugin_tray::TrayItem::new("import").build()?)
                    .item(&tauri_plugin_tray::TrayItem::new("analyze").build()?)
                    .separator()
                    .item(&tauri_plugin_tray::TrayItem::new("quit").build()?),
            )?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Import commands
            ImportCommands::import_from_zip,
            ImportCommands::import_from_directory,
            ImportCommands::get_import_status,
            ImportCommands::resume_import,
            // Analyze commands
            AnalyzeCommands::run_episode_detection,
            AnalyzeCommands::run_pattern_analysis,
            AnalyzeCommands::run_growth_analysis,
            AnalyzeCommands::get_analysis_status,
            // Search commands
            SearchCommands::search_fulltext,
            SearchCommands::search_semantic,
            SearchCommands::save_query,
            SearchCommands::get_saved_queries,
            // Export commands
            ExportCommands::export_markdown,
            ExportCommands::export_pdf,
            ExportCommands::export_json,
            ExportCommands::get_export_status,
            // Settings commands
            SettingsCommands::get_settings,
            SettingsCommands::update_settings,
            SettingsCommands::lock_encryption,
            SettingsCommands::unlock_encryption,
            // Update commands
            UpdateCommands::check_for_updates,
            UpdateCommands::install_update,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
