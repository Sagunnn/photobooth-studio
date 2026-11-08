// Photobooth Studio desktop app.
// The window shows ../web/index.html; these commands do the file work that the
// Python launcher (server.py) does in browser mode, inside the chosen templates folder.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::{json, Value};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use tauri::ipc::{InvokeBody, Request, Response};
use tauri::{AppHandle, Manager, State};

/// The templates folder (holds grids.json, Backgrounds/, Stickers/, Generated Templates/).
struct Workspace(Mutex<Option<PathBuf>>);

const FOLDERS: [&str; 2] = ["Backgrounds", "Stickers"];
const IMAGE_EXT: [&str; 6] = ["png", "jpg", "jpeg", "webp", "gif", "svg"];

/// Make a safe single file/folder name (no slashes, no "..").
fn clean(name: &str) -> String {
    let s: String = name
        .chars()
        .filter(|c| !matches!(c, '\\' | '/' | ':' | '*' | '?' | '"' | '<' | '>' | '|') && !c.is_control())
        .collect();
    s.trim().trim_matches('.').chars().take(120).collect()
}

/// Don't overwrite: add -2, -3, ... if the file already exists.
fn unique(path: PathBuf) -> PathBuf {
    if !path.exists() {
        return path;
    }
    let stem = path.file_stem().unwrap_or_default().to_string_lossy().into_owned();
    let ext = path.extension().map(|e| format!(".{}", e.to_string_lossy())).unwrap_or_default();
    (2..)
        .map(|n| path.with_file_name(format!("{stem}-{n}{ext}")))
        .find(|p| !p.exists())
        .unwrap()
}

fn is_image(name: &str) -> bool {
    Path::new(name)
        .extension()
        .map(|e| IMAGE_EXT.contains(&e.to_string_lossy().to_lowercase().as_str()))
        .unwrap_or(false)
}

fn err(e: impl std::fmt::Display) -> String {
    e.to_string()
}

fn settings_file(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app.path().app_config_dir().map_err(err)?;
    fs::create_dir_all(&dir).map_err(err)?;
    Ok(dir.join("settings.json"))
}

fn workspace(state: &State<Workspace>) -> Result<PathBuf, String> {
    state.0.lock().unwrap().clone().ok_or_else(|| "Choose a templates folder first".to_string())
}

fn folder_dir(state: &State<Workspace>, folder: &str) -> Result<PathBuf, String> {
    if !FOLDERS.contains(&folder) {
        return Err("unknown folder".into());
    }
    let dir = workspace(state)?.join(folder);
    fs::create_dir_all(&dir).map_err(err)?;
    Ok(dir)
}

/// Names travel URL-encoded in request headers (so non-English names are safe).
fn header(req: &Request, key: &str) -> String {
    req.headers()
        .get(key)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| urlencoding::decode(v).ok())
        .map(|s| s.into_owned())
        .unwrap_or_default()
}

fn body<'a>(req: &'a Request) -> Result<&'a [u8], String> {
    match req.body() {
        InvokeBody::Raw(bytes) => Ok(bytes),
        _ => Err("expected file bytes".into()),
    }
}

#[tauri::command]
fn get_workspace(state: State<Workspace>) -> Option<String> {
    state.0.lock().unwrap().as_ref().map(|p| p.to_string_lossy().into_owned())
}

#[tauri::command]
fn set_workspace(app: AppHandle, state: State<Workspace>, path: String) -> Result<(), String> {
    let dir = PathBuf::from(&path);
    if !dir.is_dir() {
        return Err("that is not a folder".into());
    }
    fs::write(settings_file(&app)?, json!({ "workspace": path }).to_string()).map_err(err)?;
    *state.0.lock().unwrap() = Some(dir);
    Ok(())
}

#[tauri::command]
fn read_grids(state: State<Workspace>) -> Result<Option<Value>, String> {
    let file = workspace(&state)?.join("grids.json");
    if !file.exists() {
        return Ok(None);
    }
    let text = fs::read_to_string(file).map_err(err)?;
    serde_json::from_str(&text).map(Some).map_err(|e| format!("grids.json: {e}"))
}

#[tauri::command]
fn save_preset(state: State<Workspace>, grid: Value) -> Result<Value, String> {
    let name = clean(grid.get("name").and_then(Value::as_str).unwrap_or(""));
    if name.is_empty() {
        return Err("layout needs a name".into());
    }
    for key in ["rows", "cols"] {
        let ok = grid.get(key).and_then(Value::as_i64).map(|n| (1..=20).contains(&n)).unwrap_or(false);
        if !ok {
            return Err(format!("bad {key}"));
        }
    }
    let mut grid = grid;
    grid["name"] = json!(name);
    let file = workspace(&state)?.join("grids.json");
    let mut cfg: Value = if file.exists() {
        serde_json::from_str(&fs::read_to_string(&file).map_err(err)?).map_err(err)?
    } else {
        json!({ "defaults": {}, "grids": [] })
    };
    let grids = cfg["grids"].as_array_mut().ok_or("grids.json has no grids list")?;
    let updated = match grids.iter().position(|g| g["name"] == json!(name)) {
        Some(i) => {
            grids[i] = grid;
            true
        }
        None => {
            grids.push(grid);
            false
        }
    };
    fs::write(&file, serde_json::to_string_pretty(&cfg).map_err(err)? + "\n").map_err(err)?;
    Ok(json!({ "ok": true, "updated": updated }))
}

#[tauri::command]
fn list_folder(state: State<Workspace>, folder: String) -> Result<Vec<String>, String> {
    let mut names: Vec<String> = fs::read_dir(folder_dir(&state, &folder)?)
        .map_err(err)?
        .filter_map(Result::ok)
        .filter(|e| e.path().is_file())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .filter(|n| is_image(n) && !n.starts_with('.'))
        .collect();
    names.sort();
    Ok(names)
}

#[tauri::command]
fn read_file(state: State<Workspace>, folder: String, name: String) -> Result<Response, String> {
    let path = folder_dir(&state, &folder)?.join(clean(&name));
    fs::read(path).map(Response::new).map_err(err)
}

#[tauri::command]
fn upload_file(state: State<Workspace>, request: Request) -> Result<String, String> {
    let name = clean(&header(&request, "name"));
    if name.is_empty() || !is_image(&name) {
        return Err("not an image file".into());
    }
    let target = unique(folder_dir(&state, &header(&request, "folder"))?.join(&name));
    fs::write(&target, body(&request)?).map_err(err)?;
    Ok(target.file_name().unwrap().to_string_lossy().into_owned())
}

/// Moves to the Trash, so it can be put back.
#[tauri::command]
fn delete_file(state: State<Workspace>, folder: String, name: String) -> Result<String, String> {
    let path = folder_dir(&state, &folder)?.join(clean(&name));
    if !path.is_file() {
        return Err(format!("{name} not found"));
    }
    trash::delete(&path).map_err(err)?;
    Ok("Trash".into())
}

/// Saves into Generated Templates/<machine>/<layout>/<file>.png
#[tauri::command]
fn save_design(state: State<Workspace>, request: Request) -> Result<String, String> {
    let machine = clean(&header(&request, "machine"));
    let grid = clean(&header(&request, "grid"));
    let file = clean(&header(&request, "file"));
    if grid.is_empty() || file.is_empty() {
        return Err("missing layout or file name".into());
    }
    let data = body(&request)?;
    if !data.starts_with(b"\x89PNG") {
        return Err("not a PNG".into());
    }
    let root = workspace(&state)?;
    let mut dir = root.join("Generated Templates");
    if !machine.is_empty() {
        dir = dir.join(machine);
    }
    let dir = dir.join(grid);
    fs::create_dir_all(&dir).map_err(err)?;
    let target = unique(dir.join(format!("{file}.png")));
    fs::write(&target, data).map_err(err)?;
    Ok(target.strip_prefix(&root).unwrap_or(&target).to_string_lossy().into_owned())
}

/// Font family names installed on this computer.
#[tauri::command]
async fn list_fonts() -> Vec<String> {
    let mut db = fontdb::Database::new();
    db.load_system_fonts();
    let mut names: Vec<String> = db
        .faces()
        .filter_map(|face| face.families.first().map(|(name, _)| name.clone()))
        .filter(|name| !name.starts_with('.'))
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();
    names.sort_by_key(|n| n.to_lowercase());
    names
}

/// Writes the PNG to the place picked in the "Save as…" dialog.
#[tauri::command]
fn write_export(request: Request) -> Result<(), String> {
    let mut path = header(&request, "path");
    if path.is_empty() {
        return Err("no file chosen".into());
    }
    if !path.to_lowercase().ends_with(".png") {
        path.push_str(".png");
    }
    let data = body(&request)?;
    if !data.starts_with(b"\x89PNG") {
        return Err("not a PNG".into());
    }
    fs::write(path, data).map_err(err)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            // last folder used, else ~/Documents/Templates Washing Machine if it has a grids.json
            let saved = settings_file(app.handle())
                .ok()
                .and_then(|f| fs::read_to_string(f).ok())
                .and_then(|t| serde_json::from_str::<Value>(&t).ok())
                .and_then(|v| v["workspace"].as_str().map(PathBuf::from))
                .filter(|p| p.is_dir());
            let guess = app
                .path()
                .document_dir()
                .ok()
                .map(|d| d.join("Templates Washing Machine"))
                .filter(|p| p.join("grids.json").is_file());
            app.manage(Workspace(Mutex::new(saved.or(guess))));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_workspace,
            set_workspace,
            read_grids,
            save_preset,
            list_folder,
            read_file,
            upload_file,
            delete_file,
            save_design,
            write_export,
            list_fonts
        ])
        .run(tauri::generate_context!())
        .expect("error while running Photobooth Studio");
}
