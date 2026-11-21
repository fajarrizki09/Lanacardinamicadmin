#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    fs::{self, OpenOptions},
    io::Write,
    net::{TcpListener, TcpStream},
    path::{Component, Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

use serde::{Deserialize, Serialize};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
use std::path::Prefix;
use tauri::{path::BaseDirectory, Manager, State, WindowEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};
use url::Url;
use uuid::Uuid;

const APP_HOST: &str = "127.0.0.1";
const START_PORT: u16 = 8000;
const MAX_PORT_ATTEMPTS: u16 = 20;
const STARTUP_TIMEOUT: Duration = Duration::from_secs(15);

struct BackendState(Mutex<Option<BackendRuntime>>);

struct BackendRuntime {
    process: BackendProcess,
    url: String,
    port: u16,
    shutdown_token: String,
}

#[derive(Serialize)]
struct NativePathInfo {
    kind: String,
    path: String,
    exists: bool,
}

#[derive(Serialize)]
struct NativePathsResponse {
    paths: Vec<NativePathInfo>,
}

#[derive(Serialize)]
struct NativeDiagnosticsResponse {
    app_version: String,
    platform: String,
    app_data_path: String,
    log_path: String,
    config_path: String,
    install_runtime_path: Option<String>,
    install_runtime_exists: Option<bool>,
    backend_port: Option<u16>,
    backend_running: bool,
    timestamp: u64,
}

#[derive(Serialize)]
struct NativeProcessStatusResponse {
    target: String,
    owner: String,
    running: Option<bool>,
    pid: Option<u32>,
    port: Option<u16>,
}

#[derive(Serialize)]
struct NativeOpenPathResponse {
    status: String,
    path: String,
}

#[derive(Serialize)]
struct NativeOpenExternalUrlResponse {
    status: String,
    host: String,
    source: String,
}

#[derive(Serialize)]
struct NativeOpenInvoiceFileResponse {
    status: String,
    normalized_path: String,
}

#[derive(Serialize)]
struct NativePrintFileResponse {
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
}

struct AllowedExternalUrl {
    url: String,
    scheme: String,
    host: String,
}

#[derive(Deserialize)]
#[serde(rename_all = "kebab-case")]
enum ProcessStatusTarget {
    PythonSidecar,
    TauriShell,
    Openwa,
}

impl ProcessStatusTarget {
    fn as_str(&self) -> &'static str {
        match self {
            Self::PythonSidecar => "python-sidecar",
            Self::TauriShell => "tauri-shell",
            Self::Openwa => "openwa",
        }
    }
}

#[derive(Clone, Copy)]
enum NativePathKind {
    AppData,
    Exports,
    Logs,
    Config,
    Invoices,
    Backups,
}

impl NativePathKind {
    fn parse(kind: &str) -> Result<Self, String> {
        match kind {
            "app_data" => Ok(Self::AppData),
            "exports" => Ok(Self::Exports),
            "logs" => Ok(Self::Logs),
            "config" => Ok(Self::Config),
            "invoices" => Ok(Self::Invoices),
            "backups" => Ok(Self::Backups),
            _ => Err("Jenis path native tidak didukung.".to_string()),
        }
    }

    fn parse_reveal(kind: &str) -> Result<Self, String> {
        let parsed = Self::parse(kind)?;
        if matches!(
            parsed,
            Self::Exports | Self::Logs | Self::Invoices | Self::Backups
        ) {
            Ok(parsed)
        } else {
            Err("Jenis path native tidak didukung.".to_string())
        }
    }

    fn as_str(self) -> &'static str {
        match self {
            Self::AppData => "app_data",
            Self::Exports => "exports",
            Self::Logs => "logs",
            Self::Config => "config",
            Self::Invoices => "invoices",
            Self::Backups => "backups",
        }
    }
}

fn shell_log(app: &tauri::AppHandle, message: &str) {
    let Ok(log_dir) = app.path().app_log_dir() else {
        return;
    };
    if fs::create_dir_all(&log_dir).is_err() {
        return;
    }
    let Ok(mut file) = OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_dir.join("desktop_shell.log"))
    else {
        return;
    };
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0);
    let _ = writeln!(file, "[{timestamp}] {message}");
}

enum BackendProcess {
    Development(Child),
    Bundled(CommandChild),
}

#[cfg(windows)]
fn force_kill_process_tree(pid: u32) -> bool {
    let mut command = Command::new("taskkill");
    command
        .args(["/PID", &pid.to_string(), "/T", "/F"])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(0x08000000);

    command
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

impl BackendProcess {
    fn pid(&self) -> u32 {
        match self {
            Self::Development(child) => child.id(),
            Self::Bundled(child) => child.pid(),
        }
    }

    fn kill(self) {
        match self {
            Self::Development(mut child) => {
                #[cfg(windows)]
                if !force_kill_process_tree(child.id()) {
                    let _ = child.kill();
                }
                #[cfg(not(windows))]
                let _ = child.kill();
                let _ = child.wait();
            }
            Self::Bundled(child) => {
                #[cfg(windows)]
                if !force_kill_process_tree(child.pid()) {
                    let _ = child.kill();
                }
                #[cfg(not(windows))]
                let _ = child.kill();
            }
        }
    }
}

fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

fn path_to_string(path: PathBuf) -> String {
    path.to_string_lossy().to_string()
}

fn app_data_root() -> Result<PathBuf, String> {
    if let Ok(override_dir) = std::env::var("LANCAR_APP_DATA_DIR") {
        let trimmed = override_dir.trim();
        if !trimmed.is_empty() {
            return Ok(PathBuf::from(trimmed));
        }
    }

    let appdata = std::env::var("APPDATA").map_err(|_| "APPDATA tidak tersedia.".to_string())?;
    Ok(PathBuf::from(appdata).join("LancarDinamicAdmin"))
}

fn native_path_for(_app: &tauri::AppHandle, kind: NativePathKind) -> Result<PathBuf, String> {
    let app_data = app_data_root()?;

    let root = match kind {
        NativePathKind::AppData => app_data.clone(),
        NativePathKind::Exports => app_data.join("exports"),
        NativePathKind::Logs => app_data.join("logs"),
        NativePathKind::Config => app_data.clone(),
        NativePathKind::Invoices => app_data.join("invoices"),
        NativePathKind::Backups => app_data.join("backups"),
    };

    if matches!(
        kind,
        NativePathKind::Exports | NativePathKind::Invoices | NativePathKind::Backups
    ) {
        let _ = fs::create_dir_all(&root);
    }

    Ok(root)
}

fn has_unsafe_path_prefix(path: &Path) -> bool {
    path.components().any(|component| {
        let Component::Prefix(prefix) = component else {
            return false;
        };
        #[cfg(windows)]
        {
            !matches!(prefix.kind(), Prefix::Disk(_) | Prefix::VerbatimDisk(_))
        }
        #[cfg(not(windows))]
        {
            let _ = prefix;
            true
        }
    })
}

fn has_sensitive_component(path: &Path) -> bool {
    path.components().any(|component| {
        let Component::Normal(value) = component else {
            return false;
        };
        let value = value.to_string_lossy().to_ascii_lowercase();
        matches!(
            value.as_str(),
            "session"
                | "sessions"
                | "cache"
                | "auth"
                | "credential"
                | "credentials"
                | "token"
                | "tokens"
                | "key"
                | "keys"
                | "secret"
                | "secrets"
        )
    })
}

fn safe_canonical_root(root: &Path) -> Result<PathBuf, String> {
    let canonical = root
        .canonicalize()
        .map_err(|_| "File tidak ditemukan.".to_string())?;
    if has_unsafe_path_prefix(&canonical) || has_sensitive_component(&canonical) {
        return Err("Path tidak diizinkan.".to_string());
    }
    Ok(canonical)
}

fn resolve_allowed_path(root: &Path, requested_path: Option<&str>) -> Result<PathBuf, String> {
    let canonical_root = safe_canonical_root(root)?;
    let Some(raw_path) = requested_path
        .map(str::trim)
        .filter(|value| !value.is_empty())
    else {
        return Ok(canonical_root);
    };

    if raw_path.contains('\0')
        || raw_path.starts_with("\\\\")
        || raw_path.starts_with("//")
        || raw_path.starts_with(r"\\?\")
        || raw_path.starts_with(r"\\.\")
    {
        return Err("Path tidak diizinkan.".to_string());
    }

    let requested = Path::new(raw_path);
    if has_unsafe_path_prefix(requested) || has_sensitive_component(requested) {
        return Err("Path tidak diizinkan.".to_string());
    }

    let candidate = if requested.is_absolute() {
        requested.to_path_buf()
    } else {
        canonical_root.join(requested)
    };

    let canonical_candidate = candidate
        .canonicalize()
        .map_err(|_| "File tidak ditemukan.".to_string())?;

    if has_unsafe_path_prefix(&canonical_candidate)
        || has_sensitive_component(&canonical_candidate)
        || !canonical_candidate.starts_with(&canonical_root)
    {
        return Err("Path tidak diizinkan.".to_string());
    }

    Ok(canonical_candidate)
}

#[cfg(windows)]
fn os_display_path(path: &Path) -> PathBuf {
    let text = path.to_string_lossy();
    if let Some(stripped) = text.strip_prefix(r"\\?\") {
        PathBuf::from(stripped)
    } else {
        path.to_path_buf()
    }
}

#[cfg(not(windows))]
fn os_display_path(path: &Path) -> PathBuf {
    path.to_path_buf()
}

#[cfg(windows)]
fn spawn_os_open(path: &Path) -> Result<(), String> {
    let path = os_display_path(path);
    let mut command = Command::new("cmd");
    command
        .args(["/C", "start", "", &path.to_string_lossy()])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(0x08000000);
    command
        .spawn()
        .map(|_| ())
        .map_err(|_| "Path tidak dapat dibuka.".to_string())
}

#[cfg(target_os = "macos")]
fn spawn_os_open(path: &Path) -> Result<(), String> {
    Command::new("open")
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|_| "Path tidak dapat dibuka.".to_string())
}

#[cfg(all(not(windows), not(target_os = "macos")))]
fn spawn_os_open(path: &Path) -> Result<(), String> {
    Command::new("xdg-open")
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|_| "Path tidak dapat dibuka.".to_string())
}

#[cfg(windows)]
fn spawn_os_reveal(path: &Path) -> Result<(), String> {
    let path = os_display_path(path);
    let mut command = Command::new("explorer");
    if path.is_file() {
        command.arg(format!("/select,{}", path.to_string_lossy()));
    } else {
        command.arg(path);
    }
    command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(0x08000000)
        .spawn()
        .map(|_| ())
        .map_err(|_| "Path tidak dapat dibuka.".to_string())
}

#[cfg(target_os = "macos")]
fn spawn_os_reveal(path: &Path) -> Result<(), String> {
    Command::new("open")
        .args(["-R", &path.to_string_lossy()])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|_| "Path tidak dapat dibuka.".to_string())
}

#[cfg(all(not(windows), not(target_os = "macos")))]
fn spawn_os_reveal(path: &Path) -> Result<(), String> {
    let target = if path.is_dir() {
        path.to_path_buf()
    } else {
        path.parent().unwrap_or(path).to_path_buf()
    };
    spawn_os_open(&target)
}

fn parse_external_source(source: &str) -> Result<&'static str, String> {
    match source.trim() {
        "payment" => Ok("payment"),
        "whatsapp_help" => Ok("whatsapp_help"),
        "gateway_dashboard" => Ok("gateway_dashboard"),
        "support" => Ok("support"),
        "unknown" | "" => Ok("unknown"),
        _ => Err("Sumber URL tidak didukung.".to_string()),
    }
}

fn validate_external_url(raw_url: &str) -> Result<AllowedExternalUrl, String> {
    let value = raw_url.trim();
    if value.is_empty() {
        return Err("URL eksternal tidak diizinkan.".to_string());
    }

    let parsed = Url::parse(value).map_err(|_| "URL eksternal tidak valid.".to_string())?;
    if !parsed.username().is_empty() || parsed.password().is_some() {
        return Err("URL eksternal tidak diizinkan.".to_string());
    }

    let scheme = parsed.scheme().to_ascii_lowercase();
    let host = parsed
        .host_str()
        .map(|value| value.to_ascii_lowercase())
        .ok_or_else(|| "URL eksternal tidak diizinkan.".to_string())?;
    let port = parsed.port();

    let allowed_https = scheme == "https"
        && matches!(host.as_str(), "app.sandbox.midtrans.com" | "wa.me")
        && port.is_none();
    let allowed_gateway_dashboard = scheme == "http" && host == "127.0.0.1" && port == Some(3000);

    if !allowed_https && !allowed_gateway_dashboard {
        return Err("URL eksternal tidak diizinkan.".to_string());
    }

    Ok(AllowedExternalUrl {
        url: parsed.to_string(),
        scheme,
        host,
    })
}

#[cfg(windows)]
fn spawn_os_open_url(url: &str) -> Result<(), String> {
    let mut command = Command::new("cmd");
    command
        .args(["/C", "start", "", url])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(0x08000000);
    command
        .spawn()
        .map(|_| ())
        .map_err(|_| "URL eksternal tidak dapat dibuka.".to_string())
}

#[cfg(target_os = "macos")]
fn spawn_os_open_url(url: &str) -> Result<(), String> {
    Command::new("open")
        .arg(url)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|_| "URL eksternal tidak dapat dibuka.".to_string())
}

#[cfg(all(not(windows), not(target_os = "macos")))]
fn spawn_os_open_url(url: &str) -> Result<(), String> {
    Command::new("xdg-open")
        .arg(url)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|_| "URL eksternal tidak dapat dibuka.".to_string())
}

fn parse_invoice_file_action(action: &str) -> Result<&'static str, String> {
    match action.trim() {
        "open" => Ok("open"),
        "reveal" => Ok("reveal"),
        _ => Err("Aksi file invoice tidak didukung.".to_string()),
    }
}

fn parse_print_file_source(source: &str) -> Result<&'static str, String> {
    match source.trim() {
        "invoice" => Ok("invoice"),
        "herbal_invoice" => Ok("herbal_invoice"),
        "export" => Ok("export"),
        "receipt" => Ok("receipt"),
        _ => Err("Sumber print tidak didukung.".to_string()),
    }
}

fn is_allowed_invoice_file_extension(path: &Path) -> bool {
    path.extension()
        .and_then(|value| value.to_str())
        .map(|value| value.eq_ignore_ascii_case("pdf"))
        .unwrap_or(false)
}

fn resolve_allowed_invoice_file_from_roots<'a>(
    roots: &'a [(PathBuf, &'static str)],
    requested_path: &str,
) -> Result<(PathBuf, &'static str), String> {
    let raw_path = requested_path.trim();
    if raw_path.is_empty() {
        return Err("Path tidak diizinkan.".to_string());
    }

    let mut saw_missing = false;
    for (root, root_name) in roots {
        let mut candidates = vec![raw_path.to_string()];
        let root_prefix = format!("{root_name}/");
        let root_prefix_windows = format!("{root_name}\\");
        if let Some(stripped) = raw_path
            .strip_prefix(&root_prefix)
            .or_else(|| raw_path.strip_prefix(&root_prefix_windows))
        {
            candidates.push(stripped.to_string());
        }

        for candidate in candidates {
            match resolve_allowed_path(&root, Some(&candidate)) {
                Ok(resolved) => {
                    if !resolved.is_file() {
                        return Err("File tidak ditemukan.".to_string());
                    }
                    if !is_allowed_invoice_file_extension(&resolved) {
                        return Err("Ekstensi file tidak diizinkan.".to_string());
                    }
                    return Ok((resolved, root_name));
                }
                Err(error) if error == "File tidak ditemukan." => {
                    saw_missing = true;
                }
                Err(_) => {}
            }
        }
    }

    if saw_missing {
        Err("File tidak ditemukan.".to_string())
    } else {
        Err("Path tidak diizinkan.".to_string())
    }
}

fn resolve_allowed_invoice_file(
    app: &tauri::AppHandle,
    requested_path: &str,
) -> Result<(PathBuf, &'static str), String> {
    let roots = [
        (native_path_for(app, NativePathKind::Invoices)?, "invoices"),
        (native_path_for(app, NativePathKind::Exports)?, "exports"),
    ];
    resolve_allowed_invoice_file_from_roots(&roots, requested_path)
}

#[cfg(windows)]
fn spawn_os_print_direct(path: &Path) -> Result<(), String> {
    let path = os_display_path(path);
    let mut command = Command::new("powershell");
    command
        .args([
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-Command",
            "Start-Process -FilePath $args[0] -Verb Print -WindowStyle Hidden",
        ])
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .creation_flags(0x08000000);
    command
        .status()
        .map_err(|_| "Print tidak tersedia, file dibuka di viewer.".to_string())
        .and_then(|status| {
            if status.success() {
                Ok(())
            } else {
                Err("Print tidak tersedia, file dibuka di viewer.".to_string())
            }
        })
}

#[cfg(target_os = "macos")]
fn spawn_os_print_direct(path: &Path) -> Result<(), String> {
    Command::new("lp")
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|_| "Print tidak tersedia, file dibuka di viewer.".to_string())
        .and_then(|status| {
            if status.success() {
                Ok(())
            } else {
                Err("Print tidak tersedia, file dibuka di viewer.".to_string())
            }
        })
}

#[cfg(all(not(windows), not(target_os = "macos")))]
fn spawn_os_print_direct(path: &Path) -> Result<(), String> {
    Command::new("lp")
        .arg(path)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|_| "Print tidak tersedia, file dibuka di viewer.".to_string())
        .and_then(|status| {
            if status.success() {
                Ok(())
            } else {
                Err("Print tidak tersedia, file dibuka di viewer.".to_string())
            }
        })
}

fn print_file_with_fallback<D, O>(
    path: &Path,
    direct_print: D,
    open_fallback: O,
) -> Result<&'static str, String>
where
    D: Fn(&Path) -> Result<(), String>,
    O: Fn(&Path) -> Result<(), String>,
{
    if direct_print(path).is_ok() {
        return Ok("printed");
    }
    open_fallback(path).map_err(|_| "Gagal membuka file untuk print.".to_string())?;
    Ok("open_fallback")
}

fn backend_snapshot(
    state: &State<'_, BackendState>,
) -> Result<(Option<u16>, bool, Option<u32>), String> {
    let runtime = state
        .0
        .lock()
        .map_err(|_| "Status proses tidak dapat diakses.".to_string())?;

    let Some(backend) = runtime.as_ref() else {
        return Ok((None, false, None));
    };

    let running = TcpStream::connect((APP_HOST, backend.port)).is_ok();
    Ok((Some(backend.port), running, Some(backend.process.pid())))
}

impl BackendRuntime {
    fn stop(self) {
        request_graceful_shutdown(self.port, &self.shutdown_token);
        wait_until_stopped(self.port);
        self.process.kill();
    }
}

fn available_port() -> Result<u16, String> {
    for offset in 0..MAX_PORT_ATTEMPTS {
        let port = START_PORT + offset;
        if TcpListener::bind((APP_HOST, port)).is_ok() {
            return Ok(port);
        }
    }

    Err("Tidak ada port lokal kosong untuk menjalankan backend.".to_string())
}

fn source_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("src-tauri must be inside the project root")
        .to_path_buf()
}

fn runtime_root(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    if cfg!(debug_assertions) {
        return Ok(source_root());
    }

    app.path()
        .resolve("runtime", BaseDirectory::Resource)
        .map_err(|error| format!("Resource runtime tidak ditemukan: {error}"))
}

fn start_development_sidecar(
    port: u16,
    shutdown_token: &str,
    app_data_dir: &Path,
) -> Result<BackendProcess, String> {
    let root = source_root();
    let local_python = root.join(".venv").join("Scripts").join("python.exe");
    let executable = if local_python.exists() {
        local_python
    } else {
        PathBuf::from("python")
    };

    let mut command = Command::new(executable);
    command
        .arg("sidecar_main.py")
        .arg("--port")
        .arg(port.to_string())
        .arg("--shutdown-token")
        .arg(shutdown_token)
        .arg("--app-data-dir")
        .arg(app_data_dir)
        .current_dir(root)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(windows)]
    command.creation_flags(0x08000000);

    let child = command
        .spawn()
        .map_err(|error| format!("Backend development gagal dijalankan: {error}"))?;

    Ok(BackendProcess::Development(child))
}

fn start_bundled_sidecar(
    app: &tauri::AppHandle,
    port: u16,
    shutdown_token: &str,
    app_data_dir: &Path,
) -> Result<BackendProcess, String> {
    let runtime_dir = runtime_root(app)?;
    let runtime_arg = runtime_dir.to_string_lossy().to_string();
    let app_data_arg = app_data_dir.to_string_lossy().to_string();
    shell_log(app, "Starting bundled FastAPI sidecar.");
    let sidecar = app
        .shell()
        .sidecar("lancar-api")
        .map_err(|error| {
            let message = format!("Binary backend tidak ditemukan: {error}");
            shell_log(app, &message);
            message
        })?
        .args([
            "--port",
            &port.to_string(),
            "--shutdown-token",
            shutdown_token,
            "--runtime-dir",
            &runtime_arg,
            "--app-data-dir",
            &app_data_arg,
        ]);
    let (mut events, child) = sidecar.spawn().map_err(|error| {
        let message = format!("Backend gagal dijalankan: {error}");
        shell_log(app, &message);
        message
    })?;

    tauri::async_runtime::spawn(async move { while events.recv().await.is_some() {} });

    Ok(BackendProcess::Bundled(child))
}

fn wait_until_listening(port: u16) -> Result<(), String> {
    let deadline = Instant::now() + STARTUP_TIMEOUT;
    while Instant::now() < deadline {
        if TcpStream::connect((APP_HOST, port)).is_ok() {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(150));
    }

    Err("Backend lokal belum siap setelah 15 detik.".to_string())
}

fn request_graceful_shutdown(port: u16, token: &str) {
    let Ok(mut stream) = TcpStream::connect((APP_HOST, port)) else {
        return;
    };
    let request = format!(
        "POST /_desktop/shutdown HTTP/1.1\r\nHost: {APP_HOST}:{port}\r\nX-Shutdown-Token: {token}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    );
    let _ = stream.write_all(request.as_bytes());
    let _ = stream.flush();
}

fn wait_until_stopped(port: u16) {
    let deadline = Instant::now() + Duration::from_secs(2);
    while Instant::now() < deadline {
        if TcpStream::connect((APP_HOST, port)).is_err() {
            return;
        }
        thread::sleep(Duration::from_millis(100));
    }
}

#[tauri::command]
fn start_backend(app: tauri::AppHandle, state: State<'_, BackendState>) -> Result<String, String> {
    let mut runtime = state
        .0
        .lock()
        .map_err(|_| "Status backend tidak dapat diakses.".to_string())?;

    if let Some(existing) = runtime.as_ref() {
        return Ok(existing.url.clone());
    }

    let port = available_port()?;
    let shutdown_token = Uuid::new_v4().to_string();
    let app_data_dir = app_data_root()?;
    let process = if cfg!(debug_assertions) {
        start_development_sidecar(port, &shutdown_token, &app_data_dir)?
    } else {
        start_bundled_sidecar(&app, port, &shutdown_token, &app_data_dir)?
    };

    if let Err(error) = wait_until_listening(port) {
        shell_log(&app, &format!("Sidecar tidak siap: {error}"));
        process.kill();
        return Err(error);
    }

    let url = format!("http://{APP_HOST}:{port}/license");
    *runtime = Some(BackendRuntime {
        process,
        url: url.clone(),
        port,
        shutdown_token,
    });
    shell_log(&app, &format!("Backend siap pada port {port}."));
    Ok(url)
}

#[tauri::command]
fn native_get_paths(
    app: tauri::AppHandle,
    kinds: Vec<String>,
) -> Result<NativePathsResponse, String> {
    let mut paths = Vec::with_capacity(kinds.len());

    for requested_kind in kinds {
        let kind = NativePathKind::parse(&requested_kind)?;
        let path = native_path_for(&app, kind)?;
        paths.push(NativePathInfo {
            kind: kind.as_str().to_string(),
            exists: path.exists(),
            path: path_to_string(path),
        });
    }

    Ok(NativePathsResponse { paths })
}

#[tauri::command]
fn native_get_diagnostics(
    app: tauri::AppHandle,
    state: State<'_, BackendState>,
) -> Result<NativeDiagnosticsResponse, String> {
    let app_data_path = native_path_for(&app, NativePathKind::AppData)?;
    let log_path = native_path_for(&app, NativePathKind::Logs)?;
    let config_path = native_path_for(&app, NativePathKind::Config)?;
    let runtime_path = runtime_root(&app).ok();
    let (backend_port, backend_running, _) = backend_snapshot(&state)?;

    Ok(NativeDiagnosticsResponse {
        app_version: app.package_info().version.to_string(),
        platform: format!("{}-{}", std::env::consts::OS, std::env::consts::ARCH),
        app_data_path: path_to_string(app_data_path),
        log_path: path_to_string(log_path),
        config_path: path_to_string(config_path),
        install_runtime_exists: runtime_path.as_ref().map(|path| path.exists()),
        install_runtime_path: runtime_path.map(path_to_string),
        backend_port,
        backend_running,
        timestamp: current_timestamp(),
    })
}

#[tauri::command]
fn native_get_process_status(
    target: ProcessStatusTarget,
    state: State<'_, BackendState>,
) -> Result<NativeProcessStatusResponse, String> {
    match target {
        ProcessStatusTarget::PythonSidecar => {
            let (port, running, pid) = backend_snapshot(&state)?;
            Ok(NativeProcessStatusResponse {
                target: ProcessStatusTarget::PythonSidecar.as_str().to_string(),
                owner: "rust".to_string(),
                running: Some(running),
                pid,
                port,
            })
        }
        ProcessStatusTarget::TauriShell => Ok(NativeProcessStatusResponse {
            target: ProcessStatusTarget::TauriShell.as_str().to_string(),
            owner: "rust".to_string(),
            running: Some(true),
            pid: Some(std::process::id()),
            port: None,
        }),
        ProcessStatusTarget::Openwa => Ok(NativeProcessStatusResponse {
            target: ProcessStatusTarget::Openwa.as_str().to_string(),
            owner: "python".to_string(),
            running: None,
            pid: None,
            port: None,
        }),
    }
}

#[tauri::command]
fn native_open_path(
    app: tauri::AppHandle,
    kind: String,
    path: Option<String>,
) -> Result<NativeOpenPathResponse, String> {
    let kind = NativePathKind::parse(&kind)?;
    let root = native_path_for(&app, kind)?;
    let resolved = resolve_allowed_path(&root, path.as_deref())?;
    spawn_os_open(&resolved)?;
    Ok(NativeOpenPathResponse {
        status: "success".to_string(),
        path: path_to_string(resolved),
    })
}

#[tauri::command]
fn native_reveal_path(
    app: tauri::AppHandle,
    kind: String,
    path: String,
) -> Result<NativeOpenPathResponse, String> {
    if path.trim().is_empty() {
        return Err("Path tidak diizinkan.".to_string());
    }
    let kind = NativePathKind::parse_reveal(&kind)?;
    let root = native_path_for(&app, kind)?;
    let resolved = resolve_allowed_path(&root, Some(path.as_str()))?;
    spawn_os_reveal(&resolved)?;
    Ok(NativeOpenPathResponse {
        status: "success".to_string(),
        path: path_to_string(resolved),
    })
}

#[tauri::command]
fn native_open_external_url(
    app: tauri::AppHandle,
    url: String,
    source: String,
) -> Result<NativeOpenExternalUrlResponse, String> {
    let source = parse_external_source(&source)?;
    let allowed = validate_external_url(&url).map_err(|error| {
        shell_log(
            &app,
            &format!("External URL denied: source={source} reason={error}"),
        );
        error
    })?;

    shell_log(
        &app,
        &format!(
            "External URL allowed: source={source} scheme={} host={}",
            allowed.scheme, allowed.host
        ),
    );
    spawn_os_open_url(&allowed.url)?;

    Ok(NativeOpenExternalUrlResponse {
        status: "opened".to_string(),
        host: allowed.host,
        source: source.to_string(),
    })
}

#[tauri::command]
fn native_open_invoice_file(
    app: tauri::AppHandle,
    path: String,
    action: String,
) -> Result<NativeOpenInvoiceFileResponse, String> {
    let action = parse_invoice_file_action(&action)?;
    let (resolved, root_name) = resolve_allowed_invoice_file(&app, &path).map_err(|error| {
        shell_log(
            &app,
            &format!("Invoice file denied: action={action} reason={error}"),
        );
        error
    })?;

    shell_log(
        &app,
        &format!("Invoice file allowed: action={action} root={root_name}"),
    );
    match action {
        "open" => spawn_os_open(&resolved)?,
        "reveal" => spawn_os_reveal(&resolved)?,
        _ => return Err("Aksi file invoice tidak didukung.".to_string()),
    }

    Ok(NativeOpenInvoiceFileResponse {
        status: if action == "open" {
            "opened".to_string()
        } else {
            "revealed".to_string()
        },
        normalized_path: path_to_string(resolved),
    })
}

#[tauri::command]
fn native_print_file(
    app: tauri::AppHandle,
    path: String,
    source: String,
) -> Result<NativePrintFileResponse, String> {
    let source = parse_print_file_source(&source)?;
    let (resolved, root_name) = resolve_allowed_invoice_file(&app, &path).map_err(|error| {
        shell_log(
            &app,
            &format!("Print file denied: source={source} reason={error}"),
        );
        error
    })?;

    shell_log(
        &app,
        &format!("Print file allowed: source={source} root={root_name}"),
    );
    let status = print_file_with_fallback(&resolved, spawn_os_print_direct, spawn_os_open)?;
    if status == "printed" {
        Ok(NativePrintFileResponse {
            status: "printed".to_string(),
            message: None,
        })
    } else {
        Ok(NativePrintFileResponse {
            status: "open_fallback".to_string(),
            message: Some("Print langsung tidak tersedia. File dibuka di viewer.".to_string()),
        })
    }
}

fn stop_backend(app: &tauri::AppHandle) {
    let state = app.state::<BackendState>();
    if let Ok(mut runtime) = state.0.lock() {
        if let Some(backend) = runtime.take() {
            shell_log(app, "Stopping bundled backend.");
            backend.stop();
        }
    };
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            start_backend,
            native_get_paths,
            native_get_diagnostics,
            native_get_process_status,
            native_open_path,
            native_reveal_path,
            native_open_external_url,
            native_open_invoice_file,
            native_print_file
        ])
        .setup(|app| {
            let app_handle = app.handle().clone();
            if let Some(window) = app.get_webview_window("main") {
                window.on_window_event(move |event| {
                    if matches!(event, WindowEvent::Destroyed) {
                        stop_backend(&app_handle);
                    }
                });
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Lancar Dynamic Admin");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn native_path_kind_accepts_only_known_values() {
        for kind in [
            "app_data", "exports", "logs", "config", "invoices", "backups",
        ] {
            assert!(NativePathKind::parse(kind).is_ok());
        }

        assert!(NativePathKind::parse("session").is_err());
        assert!(NativePathKind::parse("../logs").is_err());
    }

    #[test]
    fn native_reveal_kind_is_more_restricted_than_open_kind() {
        assert!(NativePathKind::parse_reveal("exports").is_ok());
        assert!(NativePathKind::parse_reveal("logs").is_ok());
        assert!(NativePathKind::parse_reveal("invoices").is_ok());
        assert!(NativePathKind::parse_reveal("backups").is_ok());
        assert!(NativePathKind::parse_reveal("app_data").is_err());
        assert!(NativePathKind::parse_reveal("config").is_err());
    }

    #[test]
    fn diagnostics_payload_does_not_define_secret_fields() {
        let payload = NativeDiagnosticsResponse {
            app_version: "1.7.49".to_string(),
            platform: "windows-x86_64".to_string(),
            app_data_path: "C:\\Users\\example\\AppData\\Roaming\\Lancar".to_string(),
            log_path: "C:\\Users\\example\\AppData\\Roaming\\Lancar\\logs".to_string(),
            config_path: "C:\\Users\\example\\AppData\\Roaming\\Lancar\\config".to_string(),
            install_runtime_path: Some("C:\\Program Files\\Lancar\\runtime".to_string()),
            install_runtime_exists: Some(true),
            backend_port: Some(8000),
            backend_running: true,
            timestamp: 1,
        };

        let serialized = serde_json::to_string(&payload).expect("serialize diagnostics");
        for forbidden in [
            "shutdown_token",
            "app_token",
            "gateway_token",
            "session",
            "api_key",
            "server_key",
            "database",
            "raw_log",
        ] {
            assert!(!serialized.contains(forbidden));
        }
    }

    #[test]
    fn process_status_target_parses_supported_targets_only() {
        assert!(serde_json::from_str::<ProcessStatusTarget>("\"python-sidecar\"").is_ok());
        assert!(serde_json::from_str::<ProcessStatusTarget>("\"tauri-shell\"").is_ok());
        assert!(serde_json::from_str::<ProcessStatusTarget>("\"openwa\"").is_ok());
        assert!(serde_json::from_str::<ProcessStatusTarget>("\"payment-gateway\"").is_err());
    }

    fn test_root(name: &str) -> PathBuf {
        let path =
            std::env::temp_dir().join(format!("lancar-tauri-path-test-{name}-{}", Uuid::new_v4()));
        fs::create_dir_all(&path).expect("create test root");
        path
    }

    #[test]
    fn resolve_allowed_path_accepts_root_and_child() {
        let root = test_root("valid");
        let child = root.join("invoice.pdf");
        fs::write(&child, "secret invoice content").expect("write child");

        let root_resolved = resolve_allowed_path(&root, None).expect("resolve root");
        let child_resolved =
            resolve_allowed_path(&root, Some("invoice.pdf")).expect("resolve child");

        assert_eq!(root_resolved, root.canonicalize().expect("canonical root"));
        assert_eq!(
            child_resolved,
            child.canonicalize().expect("canonical child")
        );
        assert!(!path_to_string(child_resolved).contains("secret invoice content"));
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn resolve_allowed_path_rejects_traversal_and_outside_root() {
        let root = test_root("traversal");
        let outside = test_root("outside").join("outside.pdf");
        fs::write(&outside, "outside").expect("write outside");

        assert_eq!(
            resolve_allowed_path(&root, Some("../outside.pdf")).unwrap_err(),
            "File tidak ditemukan."
        );
        assert_eq!(
            resolve_allowed_path(&root, Some(&path_to_string(outside))).unwrap_err(),
            "Path tidak diizinkan."
        );
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn resolve_allowed_path_rejects_missing_and_sensitive_paths() {
        let root = test_root("missing-sensitive");
        let cache = root.join("cache");
        fs::create_dir_all(&cache).expect("create cache");

        assert_eq!(
            resolve_allowed_path(&root, Some("missing.pdf")).unwrap_err(),
            "File tidak ditemukan."
        );
        assert_eq!(
            resolve_allowed_path(&root, Some("cache")).unwrap_err(),
            "Path tidak diizinkan."
        );
        assert_eq!(
            resolve_allowed_path(&root, Some(r"\\server\share\file.pdf")).unwrap_err(),
            "Path tidak diizinkan."
        );
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn external_url_allows_only_reviewed_targets() {
        let midtrans = validate_external_url(
            "https://app.sandbox.midtrans.com/snap/v2/vtweb/snap-token?order_id=secret",
        )
        .expect("allow sandbox midtrans");
        assert_eq!(midtrans.host, "app.sandbox.midtrans.com");

        let whatsapp =
            validate_external_url("https://wa.me/628111111111?text=Halo").expect("allow wa.me");
        assert_eq!(whatsapp.host, "wa.me");

        let gateway =
            validate_external_url("http://127.0.0.1:3000").expect("allow local gateway dashboard");
        assert_eq!(gateway.host, "127.0.0.1");
    }

    #[test]
    fn external_url_rejects_unsafe_schemes_credentials_and_invalid_values() {
        for url in [
            "",
            "not a url",
            "javascript:alert(1)",
            "file:///C:/Windows/System32/calc.exe",
            "data:text/html;base64,PHNjcmlwdD4=",
            "vbscript:msgbox(1)",
            "https://user:password@wa.me/628111111111",
        ] {
            assert!(validate_external_url(url).is_err(), "{url}");
        }
    }

    #[test]
    fn external_url_rejects_unknown_domains_ports_and_lookalikes() {
        for url in [
            "https://app.midtrans.com/snap/v2/vtweb/token",
            "https://api.midtrans.com/v2/token",
            "https://app.sandbox.midtrans.com.evil.example/pay",
            "https://wa.me.evil.example/628111111111",
            "https://wa.me:444/628111111111",
            "http://localhost:3000",
            "http://127.0.0.1:3001",
            "http://192.168.1.10:3000",
        ] {
            assert!(validate_external_url(url).is_err(), "{url}");
        }
    }

    #[test]
    fn external_url_source_accepts_only_known_sources() {
        for source in [
            "payment",
            "whatsapp_help",
            "gateway_dashboard",
            "support",
            "unknown",
            "",
        ] {
            assert!(parse_external_source(source).is_ok(), "{source}");
        }
        assert!(parse_external_source("payment_admin").is_err());
    }

    fn invoice_test_roots(name: &str) -> (PathBuf, PathBuf, Vec<(PathBuf, &'static str)>) {
        let invoices = test_root(&format!("{name}-invoices"));
        let exports = test_root(&format!("{name}-exports"));
        let roots = vec![(invoices.clone(), "invoices"), (exports.clone(), "exports")];
        (invoices, exports, roots)
    }

    #[test]
    fn invoice_file_action_accepts_open_and_reveal_only() {
        assert_eq!(parse_invoice_file_action("open").unwrap(), "open");
        assert_eq!(parse_invoice_file_action("reveal").unwrap(), "reveal");
        assert!(parse_invoice_file_action("print").is_err());
    }

    #[test]
    fn print_file_source_accepts_only_known_sources() {
        for source in ["invoice", "herbal_invoice", "export", "receipt"] {
            assert!(parse_print_file_source(source).is_ok(), "{source}");
        }
        assert!(parse_print_file_source("shell").is_err());
        assert!(parse_print_file_source("").is_err());
    }

    #[test]
    fn invoice_file_resolver_accepts_pdf_in_allowed_roots() {
        let (invoices, exports, roots) = invoice_test_roots("valid");
        let invoice_pdf = invoices.join("visit-001.pdf");
        let export_pdf = exports.join("owner-report.pdf");
        fs::write(&invoice_pdf, "secret invoice content").expect("write invoice pdf");
        fs::write(&export_pdf, "secret export content").expect("write export pdf");

        let (invoice_resolved, invoice_root) =
            resolve_allowed_invoice_file_from_roots(&roots, "visit-001.pdf")
                .expect("resolve invoice pdf");
        let (prefixed_invoice_resolved, prefixed_invoice_root) =
            resolve_allowed_invoice_file_from_roots(&roots, "invoices/visit-001.pdf")
                .expect("resolve invoice pdf with stored prefix");
        let export_pdf_text = path_to_string(export_pdf.clone());
        let (export_resolved, export_root) =
            resolve_allowed_invoice_file_from_roots(&roots, &export_pdf_text)
                .expect("resolve export pdf");

        assert_eq!(invoice_root, "invoices");
        assert_eq!(prefixed_invoice_root, "invoices");
        assert_eq!(export_root, "exports");
        assert_eq!(invoice_resolved, invoice_pdf.canonicalize().unwrap());
        assert_eq!(
            prefixed_invoice_resolved,
            invoice_pdf.canonicalize().unwrap()
        );
        assert_eq!(export_resolved, export_pdf.canonicalize().unwrap());
        assert!(!path_to_string(invoice_resolved).contains("secret invoice content"));
        let _ = fs::remove_dir_all(invoices);
        let _ = fs::remove_dir_all(exports);
    }

    #[test]
    fn print_file_resolver_accepts_pdf_in_invoice_and_export_roots() {
        let (invoices, exports, roots) = invoice_test_roots("print-valid");
        let invoice_pdf = invoices.join("visit-print.pdf");
        let export_pdf = exports.join("export-print.pdf");
        fs::write(&invoice_pdf, "secret invoice print content").expect("write invoice pdf");
        fs::write(&export_pdf, "secret export print content").expect("write export pdf");

        let (invoice_resolved, invoice_root) =
            resolve_allowed_invoice_file_from_roots(&roots, "visit-print.pdf")
                .expect("resolve invoice print pdf");
        let export_pdf_text = path_to_string(export_pdf.clone());
        let (export_resolved, export_root) =
            resolve_allowed_invoice_file_from_roots(&roots, &export_pdf_text)
                .expect("resolve export print pdf");

        assert_eq!(invoice_root, "invoices");
        assert_eq!(export_root, "exports");
        assert_eq!(invoice_resolved, invoice_pdf.canonicalize().unwrap());
        assert_eq!(export_resolved, export_pdf.canonicalize().unwrap());
        assert!(!path_to_string(invoice_resolved).contains("secret invoice print content"));
        let _ = fs::remove_dir_all(invoices);
        let _ = fs::remove_dir_all(exports);
    }

    #[test]
    fn print_file_uses_fallback_status_when_direct_print_is_unavailable() {
        let root = test_root("print-fallback");
        let pdf = root.join("fallback.pdf");
        fs::write(&pdf, "secret print fallback content").expect("write pdf");

        let status = print_file_with_fallback(
            &pdf,
            |_| Err("print unavailable".to_string()),
            |path| {
                assert_eq!(path.file_name().unwrap().to_string_lossy(), "fallback.pdf");
                Ok(())
            },
        )
        .expect("fallback opens");

        assert_eq!(status, "open_fallback");
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn print_file_reports_printed_only_when_direct_print_succeeds() {
        let root = test_root("print-direct");
        let pdf = root.join("direct.pdf");
        fs::write(&pdf, "secret print direct content").expect("write pdf");

        let status = print_file_with_fallback(
            &pdf,
            |_| Ok(()),
            |_| panic!("fallback must not run when direct print succeeds"),
        )
        .expect("direct print succeeds");

        assert_eq!(status, "printed");
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn invoice_file_resolver_rejects_traversal_and_outside_root() {
        let (invoices, exports, roots) = invoice_test_roots("outside");
        let outside = test_root("invoice-outside").join("outside.pdf");
        fs::write(&outside, "outside").expect("write outside pdf");

        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, "../outside.pdf").unwrap_err(),
            "File tidak ditemukan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, &path_to_string(outside)).unwrap_err(),
            "Path tidak diizinkan."
        );
        let _ = fs::remove_dir_all(invoices);
        let _ = fs::remove_dir_all(exports);
    }

    #[test]
    fn invoice_file_resolver_rejects_unc_device_sensitive_missing_and_bad_extension() {
        let (invoices, exports, roots) = invoice_test_roots("reject");
        let cache = invoices.join("cache");
        fs::create_dir_all(&cache).expect("create cache");
        let text_file = invoices.join("invoice.txt");
        fs::write(&text_file, "not a pdf").expect("write txt");

        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, r"\\server\share\invoice.pdf")
                .unwrap_err(),
            "Path tidak diizinkan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, r"\\?\C:\invoice.pdf").unwrap_err(),
            "Path tidak diizinkan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, "cache/invoice.pdf").unwrap_err(),
            "Path tidak diizinkan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, "missing.pdf").unwrap_err(),
            "File tidak ditemukan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, "invoice.txt").unwrap_err(),
            "Ekstensi file tidak diizinkan."
        );
        assert_eq!(
            resolve_allowed_invoice_file_from_roots(&roots, ".").unwrap_err(),
            "File tidak ditemukan."
        );
        let _ = fs::remove_dir_all(invoices);
        let _ = fs::remove_dir_all(exports);
    }
}
