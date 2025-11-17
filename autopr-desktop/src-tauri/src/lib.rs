// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn get_status() -> Result<String, String> {
    let response = reqwest::get("http://localhost:8000/status")
        .await
        .map_err(|e| e.to_string())?
        .text()
        .await
        .map_err(|e| e.to_string())?;
    Ok(response)
}

#[tauri::command]
fn read_config() -> Result<String, String> {
    let home = std::env::var("HOME").map_err(|e| e.to_string())?;
    let config_path = std::path::Path::new(&home).join(".autopr.yaml");
    let config = std::fs::read_to_string(config_path).map_err(|e| e.to_string())?;
    Ok(config)
}

#[tauri::command]
fn write_config(config: String) -> Result<(), String> {
    let home = std::env::var("HOME").map_err(|e| e.to_string())?;
    let config_path = std::path::Path::new(&home).join(".autopr.yaml");
    std::fs::write(config_path, config).map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, get_status, read_config, write_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
