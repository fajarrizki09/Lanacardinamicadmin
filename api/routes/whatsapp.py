from datetime import datetime
from pathlib import Path
import logging
import os
import secrets
import socket
import subprocess
import sys
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import APIRouter, Form, HTTPException, Request

from api.admin_pin import require_admin_pin
from api.database_manager import db
from helpers.openwa_client import OpenWAClient, OpenWAConfig, OpenWAError, extract_openwa_message_id, phone_to_chat_id
from utils.app_paths import get_app_data_dir
from settings import AppSettings

router = APIRouter(prefix="/whatsapp")
logger = logging.getLogger("lancar.whatsapp")

_OPENWA_PROCESS = None
_OPENWA_SHUTDOWN_TOKEN = None
_OPENWA_API_TOKEN = None
_OPENWA_LOG_STREAM = None
WA_GATEWAY_PORT = 3000
WA_GATEWAY_BASE_URL = f"http://127.0.0.1:{WA_GATEWAY_PORT}/api"
WA_GATEWAY_DASHBOARD_URL = f"http://127.0.0.1:{WA_GATEWAY_PORT}"


def _gateway_failure_reason(exc):
    text = str(exc or "")
    if "berhenti saat startup" in text:
        return "gateway_process_exited"
    if "startup timeout" in text or "tidak siap setelah" in text:
        return "gateway_startup_timeout"
    if "HTTP 403" in text:
        return "gateway_auth_rejected"
    if "HTTP 404" in text:
        return "qr_not_ready"
    if "Tidak bisa terhubung" in text or "refused" in text.lower():
        return "gateway_unreachable"
    return "gateway_request_failed"


def _project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _node_compatible_runtime_path(path_value):
    """Node on Windows cannot resolve Tauri's extended-length entrypoint path."""
    normalized = str(path_value or "").strip()
    if normalized.startswith("\\\\?\\UNC\\"):
        return "\\\\" + normalized[8:]
    if normalized.startswith("\\\\?\\"):
        return normalized[4:]
    return normalized


def _runtime_root():
    configured = str(os.getenv("LANCAR_RUNTIME_DIR") or "").strip()
    if configured:
        return Path(_node_compatible_runtime_path(configured)).expanduser().resolve()
    return _project_root()


def _openwa_server_dir():
    return _runtime_root() / "openwa_server"


def _openwa_data_dir():
    return Path(get_app_data_dir()) / "whatsapp_gateway"


def _bundled_node_exe():
    root = _runtime_root()
    candidates = []
    if sys.platform.startswith("win"):
        candidates.extend([
            root / "node" / "node.exe",
            root / "tools" / "node" / "node.exe",
            root / "runtime" / "node" / "node.exe",
        ])
    else:
        candidates.extend([
            root / "node" / "bin" / "node",
            root / "runtime" / "node" / "bin" / "node",
        ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _node_command(server_dir=None):
    bundled = _bundled_node_exe()
    if bundled:
        entrypoint = Path(server_dir or _openwa_server_dir()) / "server.js"
        return [str(bundled), str(entrypoint.resolve())]
    npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
    return [npm_cmd, "start"]


def _npm_command():
    root = _runtime_root()
    if sys.platform.startswith("win"):
        candidates = [
            root / "node" / "npm.cmd",
            root / "tools" / "node" / "npm.cmd",
            root / "runtime" / "node" / "npm.cmd",
        ]
        for candidate in candidates:
            if candidate.exists():
                return [str(candidate)]
        bundled_node = _bundled_node_exe()
        npm_cli = root / "node" / "node_modules" / "npm" / "bin" / "npm-cli.js"
        if bundled_node and npm_cli.exists():
            return [str(bundled_node), str(npm_cli)]
        return ["npm.cmd"]
    return ["npm"]


def _openwa_subprocess_env(shutdown_token="", api_token=""):
    env = os.environ.copy()
    bundled_node = _bundled_node_exe()
    if bundled_node:
        node_dir = str(bundled_node.parent)
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    env["WA_GATEWAY_PORT"] = str(WA_GATEWAY_PORT)
    env["WA_GATEWAY_DATA_DIR"] = str(_openwa_data_dir())
    if shutdown_token:
        env["WA_GATEWAY_SHUTDOWN_TOKEN"] = shutdown_token
    if api_token:
        env["WA_GATEWAY_API_TOKEN"] = api_token
    env["NODE_ENV"] = env.get("NODE_ENV", "production")
    return env


def _openwa_creation_flags():
    if not sys.platform.startswith("win"):
        return 0
    return subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW


def _openwa_log_stream():
    log_dir = Path(get_app_data_dir()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return open(log_dir / "whatsapp_gateway.log", "a", encoding="utf-8", buffering=1)


def _close_openwa_log_stream():
    global _OPENWA_LOG_STREAM
    if _OPENWA_LOG_STREAM is not None:
        _OPENWA_LOG_STREAM.close()
        _OPENWA_LOG_STREAM = None


def _default_session_id():
    cfg = AppSettings().get_openwa_settings(include_secret=False)
    return str(cfg.get("openwa_session_id") or "clinic").strip() or "clinic"


def _is_port_open(host="127.0.0.1", port=WA_GATEWAY_PORT, timeout=0.5):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _openwa_server_status():
    running = _is_port_open()
    process_running = _OPENWA_PROCESS is not None and _OPENWA_PROCESS.poll() is None
    return {
        "running": running,
        "dashboard_running": running,
        "process_running": process_running,
        "base_url": WA_GATEWAY_BASE_URL,
        "dashboard_url": WA_GATEWAY_DASHBOARD_URL,
        "server_dir": str(_openwa_server_dir()),
        "data_dir": str(_openwa_data_dir()),
        "bundled_node": str(_bundled_node_exe() or ""),
        "runtime_root": str(_runtime_root()),
        "auth_mode": "qr",
    }


def get_local_openwa_api_token():
    return str(_OPENWA_API_TOKEN or "")


def _wait_for_local_openwa_ready(api_token, process=None, timeout_seconds=30.0):
    client = OpenWAClient(
        OpenWAConfig(
            base_url=WA_GATEWAY_BASE_URL,
            timeout_seconds=1,
            api_token=api_token,
        )
    )
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise OpenWAError(
                "Node gateway berhenti saat startup. Periksa whatsapp_gateway.log "
                "untuk detail runtime/entrypoint."
            )
        try:
            client.health()
            return
        except OpenWAError as exc:
            last_error = str(exc)
            time.sleep(0.2)
    detail = f" ({last_error})" if last_error else ""
    raise OpenWAError(
        f"Gateway WhatsApp startup timeout setelah {int(timeout_seconds)} detik. "
        f"Periksa whatsapp_gateway.log{detail}"
    )


def _force_kill_process_tree(process):
    if sys.platform.startswith("win"):
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    process.kill()


def _request_openwa_shutdown(shutdown_token):
    if not shutdown_token:
        return False
    request = urllib_request.Request(
        f"{WA_GATEWAY_BASE_URL}/_desktop/shutdown",
        method="POST",
        headers={"X-Shutdown-Token": shutdown_token},
    )
    try:
        with urllib_request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except (OSError, urllib_error.URLError):
        return False


def stop_local_openwa_server(timeout_seconds=5.0):
    """Stop only the local gateway process started by this API process."""
    global _OPENWA_PROCESS, _OPENWA_SHUTDOWN_TOKEN, _OPENWA_API_TOKEN
    process = _OPENWA_PROCESS
    shutdown_token = _OPENWA_SHUTDOWN_TOKEN
    _OPENWA_PROCESS = None
    _OPENWA_SHUTDOWN_TOKEN = None
    _OPENWA_API_TOKEN = None
    if process is None:
        _close_openwa_log_stream()
        return {"owned": False, "stopped": False, "forced": False}
    if process.poll() is not None:
        _close_openwa_log_stream()
        return {"owned": True, "stopped": True, "forced": False}

    forced = False
    try:
        graceful_requested = _request_openwa_shutdown(shutdown_token)
        if not graceful_requested:
            if sys.platform.startswith("win"):
                forced = True
                _force_kill_process_tree(process)
            else:
                process.terminate()
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        forced = True
        _force_kill_process_tree(process)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

    stopped = process.poll() is not None
    if stopped:
        _close_openwa_log_stream()
    return {"owned": True, "stopped": stopped, "forced": forced}


def _client(include_secret=True):
    settings = AppSettings()
    cfg = settings.get_openwa_settings(include_secret=include_secret)
    api_token = get_local_openwa_api_token()
    if not api_token:
        if _is_port_open():
            raise OpenWAError(
                "Gateway WhatsApp aktif tetapi tidak dikelola aplikasi. "
                "Tutup proses gateway lama lalu mulai ulang WhatsApp dari aplikasi."
            )
        raise OpenWAError("Gateway WhatsApp belum berjalan. Jalankan gateway dari aplikasi terlebih dahulu.")
    return OpenWAClient(
        OpenWAConfig(
            base_url=WA_GATEWAY_BASE_URL,
            session_id=cfg.get("openwa_session_id") or "",
            timeout_seconds=15,
            api_token=api_token,
        )
    ), cfg


@router.get("/settings")
def get_whatsapp_settings():
    settings = AppSettings()
    return settings.get_openwa_settings(include_secret=False)


@router.post("/auto-login")
def whatsapp_auto_login(request: Request):
    """Start local Baileys server/session and return connected account or QR."""
    try:
        require_admin_pin(request)
        settings = AppSettings()
        cfg = settings.get_openwa_settings(include_secret=False)
        sid = str(cfg.get("openwa_session_id") or "clinic").strip() or "clinic"
        updates = {
            "openwa_enabled": True,
            "openwa_base_url": WA_GATEWAY_BASE_URL,
            "openwa_session_id": sid,
            "openwa_auto_followup_enabled": cfg.get("openwa_auto_followup_enabled"),
            "openwa_followup_delay_hours": cfg.get("openwa_followup_delay_hours") or 24,
            "openwa_rate_limit_per_run": cfg.get("openwa_rate_limit_per_run") or 10,
        }
        settings.set_openwa_settings(updates)

        server_status = _openwa_server_status()
        if not server_status["running"]:
            start_local_openwa_server(request)
        elif not get_local_openwa_api_token():
            raise OpenWAError(
                "Port gateway WhatsApp digunakan proses yang tidak dikelola aplikasi. "
                "Tutup proses gateway lama lalu buka ulang aplikasi."
            )

        client, _cfg = _client(include_secret=True)
        try:
            client.create_session(sid)
        except OpenWAError:
            pass
        status_result = client.session_status(sid)
        session_status = str(status_result.get("status") or status_result.get("sessionStatus") or "").strip().lower()
        start_result = {"skipped": True, "reason": "session already active"}

        # Start/reconnect jika belum benar-benar connected. Jika ada kredensial lama,
        # Baileys akan reconnect tanpa QR; jika tidak ada, QR baru akan muncul.
        if session_status != "connected":
            start_result = client.start_session(sid)

        qr_result = None

        # Tunggu status connected atau QR terbaru.
        if session_status != "connected":
            for _ in range(14):
                try:
                    status_result = client.session_status(sid)
                    session_status = str(status_result.get("status") or status_result.get("sessionStatus") or "").strip().lower()
                    if session_status == "connected":
                        qr_result = None
                        break
                    if session_status in {"qr", "qr_ready", "logged_out", "idle", "disconnected", "connecting"}:
                        try:
                            qr_result = client.get_qr(sid)
                            if qr_result:
                                break
                        except OpenWAError as exc:
                            if _gateway_failure_reason(exc) != "qr_not_ready":
                                logger.warning("WhatsApp QR auto-login gagal: reason=%s", _gateway_failure_reason(exc))
                except OpenWAError as exc:
                    logger.warning("WhatsApp status auto-login gagal: reason=%s", _gateway_failure_reason(exc))
                time.sleep(1)
        return {
            "status": "success",
            "session_id": sid,
            "server": _openwa_server_status(),
            "session": status_result,
            "start": start_result,
            "qr": qr_result,
            "settings": settings.get_openwa_settings(include_secret=False),
        }
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/server/status")
def get_local_openwa_server_status():
    status = _openwa_server_status()
    status["status"] = "success"
    return status


@router.post("/server/start")
def start_local_openwa_server(request: Request):
    global _OPENWA_PROCESS, _OPENWA_SHUTDOWN_TOKEN, _OPENWA_API_TOKEN, _OPENWA_LOG_STREAM
    try:
        require_admin_pin(request)
        status = _openwa_server_status()
        if status["running"]:
            if not get_local_openwa_api_token():
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Port gateway WhatsApp digunakan proses yang tidak dikelola aplikasi. "
                        "Tutup proses gateway lama lalu buka ulang aplikasi."
                    ),
                )
            return {"status": "success", "message": "Server Baileys sudah berjalan. Login WhatsApp memakai scan QR.", "data": status}

        server_dir = _openwa_server_dir()
        package_json = server_dir / "package.json"
        if not package_json.exists():
            raise HTTPException(status_code=400, detail="Folder openwa_server belum tersedia di folder aplikasi.")

        node_modules = server_dir / "node_modules"
        if not node_modules.exists():
            raise HTTPException(status_code=400, detail="Dependency OpenWA belum terinstall. Jalankan npm install di folder openwa_server terlebih dahulu.")

        node_cmd = _node_command(server_dir)
        shutdown_token = secrets.token_urlsafe(32)
        api_token = secrets.token_urlsafe(32)
        _close_openwa_log_stream()
        _OPENWA_LOG_STREAM = _openwa_log_stream()
        try:
            _OPENWA_PROCESS = subprocess.Popen(
                node_cmd,
                cwd=str(server_dir),
                env=_openwa_subprocess_env(shutdown_token, api_token),
                stdout=_OPENWA_LOG_STREAM,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=_openwa_creation_flags(),
            )
        except Exception:
            _close_openwa_log_stream()
            raise
        _OPENWA_SHUTDOWN_TOKEN = shutdown_token
        _OPENWA_API_TOKEN = api_token
        logger.info(
            "Starting WhatsApp gateway: runtime=%s server_dir=%s node=%s entrypoint=%s",
            _runtime_root(),
            server_dir,
            Path(node_cmd[0]).name,
            node_cmd[-1],
        )
        try:
            _wait_for_local_openwa_ready(api_token, process=_OPENWA_PROCESS)
        except OpenWAError as exc:
            logger.error("WhatsApp gateway startup gagal: reason=%s", _gateway_failure_reason(exc))
            stop_local_openwa_server(timeout_seconds=2.0)
            raise HTTPException(
                status_code=400,
                detail=f"Gateway WhatsApp gagal dimulai. Periksa log whatsapp_gateway.log. {exc}",
            )
        return {
            "status": "success",
            "message": "Server WhatsApp lokal siap. Klik Perbarui Status untuk menampilkan QR login.",
            "data": _openwa_server_status(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/server/install")
def install_local_openwa_server(request: Request):
    try:
        require_admin_pin(request)
        server_dir = _openwa_server_dir()
        package_json = server_dir / "package.json"
        if not package_json.exists():
            raise HTTPException(status_code=400, detail="Template server WhatsApp lokal belum tersedia.")
        npm_cmd = _npm_command()
        subprocess.run(
            [*npm_cmd, "install"],
            cwd=str(server_dir),
            env=_openwa_subprocess_env(),
            check=True,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        return {
            "status": "success",
            "message": "Server WhatsApp lokal berhasil diinstall. Klik Start Server untuk menjalankan API + Dashboard sederhana.",
            "data": _openwa_server_status(),
        }
    except HTTPException:
        raise
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise HTTPException(status_code=400, detail=detail[-1200:] or "Install server WhatsApp lokal gagal.")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/settings")
async def update_whatsapp_settings(
    request: Request,
    openwa_enabled: str = Form(""),
    openwa_base_url: str = Form(WA_GATEWAY_BASE_URL),
    openwa_session_id: str = Form(""),
    openwa_auto_followup_enabled: str = Form(""),
    openwa_followup_delay_hours: int = Form(24),
    openwa_rate_limit_per_run: int = Form(10),
):
    try:
        require_admin_pin(request)
        settings = AppSettings()
        settings.set_openwa_settings({
            "openwa_enabled": openwa_enabled,
            "openwa_base_url": openwa_base_url,
            "openwa_session_id": openwa_session_id,
            "openwa_auto_followup_enabled": openwa_auto_followup_enabled,
            "openwa_followup_delay_hours": openwa_followup_delay_hours,
            "openwa_rate_limit_per_run": openwa_rate_limit_per_run,
        })
        db.log_audit("whatsapp_settings_updated", "settings", "openwa", "Pengaturan WhatsApp diperbarui.")
        return {"status": "success", "message": "Pengaturan WhatsApp tersimpan."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/health-check")
def openwa_health_check(request: Request):
    try:
        require_admin_pin(request)
        client, _cfg = _client(include_secret=True)
        return {"status": "success", "data": client.health()}
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/create")
def create_openwa_session(request: Request, session_id: str = Form("")):
    try:
        require_admin_pin(request)
        client, cfg = _client(include_secret=True)
        sid = str(session_id or cfg.get("openwa_session_id") or "").strip()
        if not sid:
            raise HTTPException(status_code=400, detail="Session ID wajib diisi.")
        result = client.create_session(sid)
        return {"status": "success", "message": "Session OpenWA dibuat.", "session_id": sid, "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/start")
def start_openwa_session(request: Request, session_id: str = Form("")):
    try:
        require_admin_pin(request)
        client, cfg = _client(include_secret=True)
        sid = str(session_id or cfg.get("openwa_session_id") or "").strip()
        if not sid:
            raise HTTPException(status_code=400, detail="Session ID wajib diisi.")
        result = client.start_session(sid)
        return {"status": "success", "message": "Session OpenWA dijalankan.", "session_id": sid, "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/logout")
def logout_openwa_session(request: Request, session_id: str = Form("")):
    try:
        require_admin_pin(request)
        client, cfg = _client(include_secret=True)
        sid = str(session_id or cfg.get("openwa_session_id") or "clinic").strip() or "clinic"
        result = client.logout_session(sid)
        db.log_audit("whatsapp_session_logout", "settings", "whatsapp", "WhatsApp logout dan session lokal dihapus.")
        return {"status": "success", "message": "WhatsApp berhasil logout. Klik Perbarui Status untuk membuat QR baru.", "session_id": sid, "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/session/status")
def get_openwa_session_status(session_id: str = ""):
    try:
        client, cfg = _client(include_secret=True)
        sid = str(session_id or cfg.get("openwa_session_id") or "").strip()
        if not sid:
            raise HTTPException(status_code=400, detail="Session ID wajib diisi.")
        result = client.session_status(sid)
        session_status = str(result.get("status") or result.get("sessionStatus") or "").strip().lower()
        if session_status in {"qr", "qr_ready", "idle", "disconnected", "connecting", "logged_out"} and not result.get("qr"):
            try:
                qr_result = client.get_qr(sid)
                if isinstance(qr_result, dict) and qr_result.get("qr"):
                    result["qr"] = qr_result.get("qr")
                    result["qrcode"] = qr_result.get("qrcode") or qr_result.get("qr")
                    result["qrCode"] = qr_result.get("qrCode") or qr_result.get("qr")
                    result["hasQr"] = True
                    result["status"] = result.get("status") or qr_result.get("status") or "qr_ready"
                    result["sessionStatus"] = result.get("sessionStatus") or qr_result.get("sessionStatus") or "qr_ready"
            except OpenWAError as exc:
                if "HTTP 404" not in str(exc):
                    logger.warning("WhatsApp QR status proxy gagal: reason=%s", _gateway_failure_reason(exc))
                    raise
        return {"status": "success", "session_id": sid, "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        logger.warning("WhatsApp QR proxy gagal: reason=%s", _gateway_failure_reason(exc))
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/session/qr")
def get_openwa_session_qr(session_id: str = ""):
    try:
        client, cfg = _client(include_secret=True)
        sid = str(session_id or cfg.get("openwa_session_id") or "").strip()
        if not sid:
            raise HTTPException(status_code=400, detail="Session ID wajib diisi.")
        result = client.get_qr(sid)
        return {"status": "success", "session_id": sid, "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        logger.warning("WhatsApp QR endpoint gagal: reason=%s", _gateway_failure_reason(exc))
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/send-test")
def send_test_whatsapp(
    request: Request,
    phone: str = Form(""),
    chat_id: str = Form(""),
    message: str = Form("Tes koneksi WhatsApp Lancar Dynamic Admin."),
):
    try:
        require_admin_pin(request)
        client, _cfg = _client(include_secret=True)
        target = str(chat_id or "").strip() or phone_to_chat_id(phone)
        if not target:
            raise HTTPException(status_code=400, detail="Nomor WhatsApp tujuan wajib diisi.")
        result = client.send_text(chat_id=target, text=message)
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/enqueue")
def enqueue_whatsapp_message(
    phone: str = Form(""),
    message: str = Form(""),
    template_key: str = Form("manual"),
    patient_id: int = Form(None),
):
    try:
        queue_id = db.enqueue_whatsapp_followup(
            phone=phone,
            message=message,
            patient_id=patient_id,
            template_key=template_key,
            scheduled_at=datetime.now(),
            created_by="admin",
        )
        return {"status": "success", "queue_id": queue_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/process-queue")
def process_whatsapp_queue(request: Request):
    try:
        require_admin_pin(request)
        client, cfg = _client(include_secret=True)
        if not cfg.get("openwa_enabled"):
            raise HTTPException(status_code=400, detail="OpenWA belum diaktifkan di pengaturan.")

        limit = int(cfg.get("openwa_rate_limit_per_run") or 10)
        rows = db.get_pending_whatsapp_followups(limit=limit)
        processed = []
        for row in rows:
            queue_id = row["id"]
            try:
                response = client.send_text(chat_id=row["chat_id"], text=row["message"])
                message_id = extract_openwa_message_id(response)
                db.mark_whatsapp_followup_sent(queue_id, openwa_message_id=message_id)
                processed.append({"id": queue_id, "status": "sent"})
            except Exception as exc:
                db.mark_whatsapp_followup_failed(queue_id, str(exc), max_retry=3)
                processed.append({"id": queue_id, "status": "failed", "error": str(exc)})

        return {
            "status": "success",
            "processed": processed,
            "count": len(processed),
        }
    except HTTPException:
        raise
    except OpenWAError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
