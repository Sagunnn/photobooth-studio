// Photobooth Studio desktop app.
// The window shows ../web/index.html; these commands do the file work that the
// Python launcher (server.py) does in browser mode, inside the chosen templates folder.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::{json, Value};
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use tauri::ipc::{InvokeBody, Request, Response};
use tauri::{AppHandle, Manager, State};

/// When this copy of the app started: if the app file is replaced (an update) while it runs, macOS can no longer
/// show Save / Open dialogs for it, so the page is told to restart instead of trying.
struct Started(Option<std::time::SystemTime>);
fn exe_time() -> Option<std::time::SystemTime> {
    std::env::current_exe().ok().and_then(|p| fs::metadata(p).ok()).and_then(|m| m.modified().ok())
}

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

/// Removes a layout from grids.json. A copy goes to Deleted Files/Layouts/ so it can be put back.
#[tauri::command]
fn delete_preset(state: State<Workspace>, name: String) -> Result<Value, String> {
    let root = workspace(&state)?;
    let file = root.join("grids.json");
    let mut cfg: Value = serde_json::from_str(&fs::read_to_string(&file).map_err(err)?).map_err(err)?;
    let grids = cfg["grids"].as_array_mut().ok_or("grids.json has no grids list")?;
    let i = grids
        .iter()
        .position(|g| g["name"] == json!(name))
        .ok_or_else(|| format!("{name} not found"))?;
    if grids.len() <= 1 {
        return Err("can't delete the last template".into());
    }
    let removed = grids.remove(i);
    let dir = root.join("Deleted Files").join("Layouts");
    fs::create_dir_all(&dir).map_err(err)?;
    let stem = Some(clean(&name)).filter(|n| !n.is_empty()).unwrap_or_else(|| "layout".into());
    let backup = unique(dir.join(format!("{stem}.json")));
    fs::write(&backup, serde_json::to_string_pretty(&removed).map_err(err)? + "\n").map_err(err)?;
    fs::write(&file, serde_json::to_string_pretty(&cfg).map_err(err)? + "\n").map_err(err)?;
    let shown = backup.strip_prefix(&root).unwrap_or(&backup).to_string_lossy().into_owned();
    Ok(json!({ "ok": true, "backup": shown }))
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

/// Downloads an image from a web link (for graphics pasted from Canva or a web page). At most 300 MB.
#[tauri::command]
async fn fetch_url(url: String) -> Result<Response, String> {
    if !(url.starts_with("http://") || url.starts_with("https://")) {
        return Err("only web links can be fetched".into());
    }
    let resp = ureq::get(&url)
        .set("User-Agent", "Mozilla/5.0 (Macintosh) PhotoboothStudio/1.0")
        .set("Accept", "image/*,*/*;q=0.8")
        .timeout(std::time::Duration::from_secs(25))
        .call()
        .map_err(err)?;
    let mut bytes = Vec::new();
    resp.into_reader().take(300 * 1024 * 1024).read_to_end(&mut bytes).map_err(err)?;
    Ok(Response::new(bytes))
}

/// Puts a PNG on the macOS clipboard as a picture (Copy image in the print preview).
#[tauri::command]
fn copy_png(request: Request) -> Result<(), String> {
    let data = body(&request)?;
    if !data.starts_with(b"\x89PNG") {
        return Err("not a PNG".into());
    }
    let path = std::env::temp_dir().join("photobooth-studio-copy.png");
    fs::write(&path, data).map_err(err)?;
    let script = format!(
        "set the clipboard to (read (POSIX file \"{}\") as «class PNGf»)",
        path.display()
    );
    let out = std::process::Command::new("osascript").arg("-e").arg(script).output().map_err(err)?;
    if !out.status.success() {
        return Err(String::from_utf8_lossy(&out.stderr).trim().to_string());
    }
    Ok(())
}

/* ---------- picking up where you left off: each window's design is saved, and the windows come back ---------- */
fn sessions_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let d = app.path().app_config_dir().map_err(err)?.join("sessions");
    fs::create_dir_all(&d).map_err(err)?;
    Ok(d)
}
fn session_file(app: &AppHandle, label: &str) -> Result<PathBuf, String> {
    let name: String = label.chars().filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_').collect();
    Ok(sessions_dir(app)?.join(format!("{name}.json")))
}
fn studio_window<'a>(app: &'a AppHandle, label: &str) -> tauri::WebviewWindowBuilder<'a, tauri::Wry, AppHandle> {
    tauri::WebviewWindowBuilder::new(app, label, tauri::WebviewUrl::App("index.html".into()))
        .title("Photobooth Studio")
        .inner_size(1440.0, 900.0)
        .min_inner_size(1000.0, 640.0)
        .disable_drag_drop_handler()
}

/// Saves this window's design (JSON from the page).
#[tauri::command]
fn save_session(app: AppHandle, window: tauri::WebviewWindow, request: Request) -> Result<(), String> {
    let file = session_file(&app, window.label())?;
    let tmp = file.with_extension("tmp");
    fs::write(&tmp, body(&request)?).map_err(err)?;
    fs::rename(&tmp, &file).map_err(err)
}

/// This window's saved design, or nothing.
#[tauri::command]
fn load_session(app: AppHandle, window: tauri::WebviewWindow) -> Result<Response, String> {
    let file = session_file(&app, window.label())?;
    Ok(Response::new(fs::read(file).unwrap_or_default()))
}

/// Opens another app window (a second design), a little below and right of the one asking.
#[tauri::command]
async fn new_window(app: AppHandle, window: tauri::WebviewWindow) -> Result<(), String> {
    let mut n = app.webview_windows().len() + 1;
    let mut label = format!("studio-{n}");
    while app.get_webview_window(&label).is_some() {
        n += 1;
        label = format!("studio-{n}");
    }
    if let Ok(f) = session_file(&app, &label) {
        let _ = fs::remove_file(f);   // a new window starts empty
    }
    let mut b = studio_window(&app, &label);
    if let (Ok(p), Ok(k)) = (window.outer_position(), window.scale_factor()) {
        b = b.position(p.x as f64 / k + 32.0, p.y as f64 / k + 32.0);
    }
    b.build().map_err(err)?;
    Ok(())
}

/// Shows the design's name in the window's title bar.
#[tauri::command]
fn set_title(window: tauri::WebviewWindow, title: String) -> Result<(), String> {
    window.set_title(&title).map_err(err)
}

/// True when the app on disk is no longer the one that is running (it was updated or moved).
#[tauri::command]
fn app_updated(started: State<Started>) -> bool {
    match (started.0, exe_time()) {
        (Some(a), Some(b)) => a != b,
        (Some(_), None) => true,
        _ => false,
    }
}

/// Starts the app again (the new version); the open designs come back from their saved sessions.
#[tauri::command]
fn restart_app(app: AppHandle) {
    app.restart();
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
        .manage(Started(exe_time()))
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
            // the extra windows that were open last time come back (each one reloads its own design)
            if let Ok(dir) = sessions_dir(app.handle()) {
                let mut labels: Vec<String> = fs::read_dir(dir)
                    .map(|rd| {
                        rd.filter_map(Result::ok)
                            .filter_map(|e| e.file_name().to_string_lossy().strip_suffix(".json").map(String::from))
                            .filter(|l| l.starts_with("studio-"))
                            .collect()
                    })
                    .unwrap_or_default();
                labels.sort();
                for (i, label) in labels.iter().enumerate() {
                    let _ = studio_window(app.handle(), label).position(80.0 + 32.0 * (i as f64 + 1.0), 60.0 + 32.0 * (i as f64 + 1.0)).build();
                }
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            // closing one window while others stay open forgets its design. Quitting keeps them all: the app is
            // gone before this delayed clean-up runs.
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle().clone();
                if app.webview_windows().len() > 1 {
                    if let Ok(f) = session_file(&app, window.label()) {
                        std::thread::spawn(move || {
                            std::thread::sleep(std::time::Duration::from_millis(1500));
                            let _ = fs::remove_file(f);
                        });
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_workspace,
            set_workspace,
            read_grids,
            save_preset,
            delete_preset,
            list_folder,
            read_file,
            upload_file,
            delete_file,
            save_design,
            write_export,
            fetch_url,
            copy_png,
            new_window,
            save_session,
            app_updated,
            restart_app,
            load_session,
            set_title,
            list_fonts
        ])
        .run(tauri::generate_context!())
        .expect("error while running Photobooth Studio");
}
