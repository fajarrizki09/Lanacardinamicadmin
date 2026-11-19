import sys
import os
import threading
import queue
import socket
import urllib.request
import logging
import random
from logging.handlers import RotatingFileHandler


log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(log_format)
logger.addHandler(ch)

if getattr(sys, "frozen", False):
    from utils.app_paths import get_app_data_dir

    log_dir = get_app_data_dir()
    log_path = os.path.join(log_dir, "RumahSehat_debug.log")

    fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(log_format)
    logger.addHandler(fh)
    logger.removeHandler(ch)

    class StreamToLogger(object):
        def __init__(self, logger, log_level):
            self.logger = logger
            self.log_level = log_level
            self.linebuf = ""

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.log_level, line.rstrip())

        def flush(self):
            pass

        def isatty(self):
            return False

    sys.stdout = StreamToLogger(logging.getLogger("STDOUT"), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger("STDERR"), logging.ERROR)


os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--allow-insecure-localhost --disable-web-security --ignore-certificate-errors --log-level=3 --disable-logging",
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtCore import QObject, QUrl, QTimer, Signal, QStandardPaths
from PySide6.QtGui import QDesktopServices

from helpers.license import (
    LICENSE_STATUS_INVALID,
    LICENSE_STATUS_NETWORK_ERROR,
    LICENSE_STATUS_OK,
    LicenseNetworkError,
    is_license_invalid,
    mark_license_invalid,
    report_error_feedback,
    verify_license,
)
from helpers.local_token import get_local_app_token


APP_HOST = "127.0.0.1"
APP_PORT = 8000
APP_URL = f"http://{APP_HOST}:{APP_PORT}"
HEALTH_URL = f"{APP_URL}/health"
STARTUP_TIMEOUT_MS = 15000
RETRY_INTERVAL_MS = 150
LICENSE_RECHECK_MIN_SECONDS = 6 * 60 * 60
LICENSE_RECHECK_MAX_SECONDS = 12 * 60 * 60
LICENSE_RECHECK_BACKOFF_INITIAL_SECONDS = 60
LICENSE_RECHECK_BACKOFF_MAX_SECONDS = 60 * 60


class LicenseRecheckNotifier(QObject):
    invalid = Signal()


def run_fastapi(error_queue=None, port=None):
    """Jalankan server Uvicorn (FastAPI) pada port lokal."""
    try:
        import uvicorn
        from api.main import app as fastapi_app

        selected_port = int(port or APP_PORT)
        config = uvicorn.Config(
            fastapi_app,
            host=APP_HOST,
            port=selected_port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()
    except BaseException as exc:
        if error_queue is not None:
            error_queue.put(exc)
        report_error_feedback(exc, source="fastapi_startup", severity="critical")
        logging.exception("FastAPI server failed to start")


def configure_runtime_port(port: int) -> None:
    global APP_PORT, APP_URL, HEALTH_URL
    APP_PORT = int(port)
    APP_URL = f"http://{APP_HOST}:{APP_PORT}"
    HEALTH_URL = f"{APP_URL}/health"


def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    for offset in range(max_attempts):
        candidate = start_port + offset
        if not is_port_open(APP_HOST, candidate):
            return candidate
    raise RuntimeError(f"Tidak ada port lokal kosong dari {start_port} sampai {start_port + max_attempts - 1}.")


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def health_check(timeout: float = 0.5) -> bool:
    try:
        request = urllib.request.Request(
            HEALTH_URL,
            headers={"X-App-Token": get_local_app_token()},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def compact_error(exc) -> str:
    if exc is None:
        return "Aplikasi belum siap merespon."
    return "Aplikasi belum siap. Tutup aplikasi lalu buka kembali."


def start_license_recheck_thread(notifier: LicenseRecheckNotifier, stop_event: threading.Event):
    def with_jitter(interval_seconds: float) -> float:
        return interval_seconds * random.uniform(0.8, 1.2)

    def worker():
        backoff_seconds = LICENSE_RECHECK_BACKOFF_INITIAL_SECONDS
        next_delay = with_jitter(random.uniform(LICENSE_RECHECK_MIN_SECONDS, LICENSE_RECHECK_MAX_SECONDS))

        while not stop_event.wait(next_delay):
            if is_license_invalid():
                notifier.invalid.emit()
                return

            try:
                license_status = verify_license(
                    exit_on_fail=False,
                    show_message=False,
                )
            except LicenseNetworkError:
                logging.warning("Background license re-check network error; retrying later.")
                next_delay = with_jitter(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, LICENSE_RECHECK_BACKOFF_MAX_SECONDS)
                continue
            except Exception:
                logging.exception("Background license re-check failed; retrying later.")
                next_delay = with_jitter(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, LICENSE_RECHECK_BACKOFF_MAX_SECONDS)
                continue

            if license_status == LICENSE_STATUS_NETWORK_ERROR:
                next_delay = with_jitter(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, LICENSE_RECHECK_BACKOFF_MAX_SECONDS)
                continue

            if license_status == LICENSE_STATUS_INVALID:
                mark_license_invalid()
                notifier.invalid.emit()
                return

            backoff_seconds = LICENSE_RECHECK_BACKOFF_INITIAL_SECONDS
            next_delay = with_jitter(random.uniform(LICENSE_RECHECK_MIN_SECONDS, LICENSE_RECHECK_MAX_SECONDS))

    thread = threading.Thread(target=worker, name="LicenseRecheckThread", daemon=True)
    thread.start()
    return thread


class CustomWebPage(QWebEnginePage):
    """Page custom yang mengabaikan SSL/certificate errors untuk localhost."""

    def _is_external_url(self, url):
        return (
            url.scheme() in {"http", "https"}
            and url.host() not in {"127.0.0.1", "localhost", APP_HOST}
        )

    def _open_external_url(self, url):
        if not self._is_external_url(url):
            return False
        QDesktopServices.openUrl(url)
        return True

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if self._open_external_url(url):
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

    def createWindow(self, window_type):
        page = CustomWebPage(self.profile(), self)
        page.urlChanged.connect(lambda url: self._open_external_url(url))
        return page

    def certificateError(self, error):
        if "127.0.0.1" in error.url().host() or "localhost" in error.url().host():
            error.acceptCertificate()
            return True
        return super().certificateError(error)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        try:
            err_level = QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel
            if level.value >= err_level.value:
                print(f"[JS ERROR] {sourceID}:{lineNumber} - {message}")
                report_error_feedback(
                    message,
                    source=f"webengine:{sourceID}:{lineNumber}",
                    severity="error",
                    context="JavaScript console error",
                )
        except Exception:
            pass


class BrowserApp(QMainWindow):
    def __init__(self, server_errors=None, target_url=None):
        super().__init__()
        clinic_name = "Lancar Dynamic Admin"
        try:
            from settings import AppSettings
            clinic_name = AppSettings().get_clinic_profile().get("clinic_name") or clinic_name
        except Exception:
            pass
        self.setWindowTitle(f"{clinic_name} - Aplikasi Klinik")
        self.resize(1280, 720)

        self._profile = QWebEngineProfile("LancarDinamicAdmin", self)
        self._profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self._profile.downloadRequested.connect(self.handle_download_requested)

        self._profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        self._profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
        )
        self._profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
        )

        self._page = CustomWebPage(self._profile, self)
        self.browser = QWebEngineView(self)
        self.browser.setPage(self._page)
        self.browser.setZoomFactor(1.0)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self._target_url = target_url or APP_URL
        self._retries = 0
        self._server_errors = server_errors
        self._max_retries = max(1, STARTUP_TIMEOUT_MS // RETRY_INTERVAL_MS)
        self.show_loading_page()

    def handle_download_requested(self, download):
        download_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        if not download_dir:
            download_dir = os.path.expanduser("~/Downloads")

        filename = download.suggestedFileName() or download.downloadFileName() or "laporan_owner.xlsx"
        filename = os.path.basename(filename).strip() or "laporan_owner.xlsx"
        target = os.path.join(download_dir, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(target):
            filename = f"{base}_{counter}{ext or '.xlsx'}"
            target = os.path.join(download_dir, filename)
            counter += 1

        download.setDownloadDirectory(download_dir)
        download.setDownloadFileName(filename)
        download.accept()
        logging.info("Download accepted: %s", target)

    def load_url(self, url_string: str):
        self._target_url = url_string
        self.browser.setUrl(QUrl(url_string))

    def show_loading_page(self):
        self.browser.setHtml(
            """
            <!doctype html>
            <html lang="id">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#f7faf9;color:#17231f;display:grid;place-items:center;min-height:100vh}
                main{width:min(520px,calc(100vw - 48px));text-align:center}
                .mark{width:54px;height:54px;border:5px solid #d7e7e1;border-top-color:#178060;border-radius:50%;margin:0 auto 22px;animation:spin .8s linear infinite}
                h1{font-size:24px;margin:0 0 10px;font-weight:650}
                p{margin:0;color:#5c6f68;line-height:1.5}
                @keyframes spin{to{transform:rotate(360deg)}}
              </style>
            </head>
            <body>
              <main>
                <div class="mark" aria-hidden="true"></div>
                <h1>Menyiapkan aplikasi</h1>
                <p>Sedang memuat data klinik. Mohon tunggu sebentar...</p>
              </main>
            </body>
            </html>
            """
        )

    def show_error_page(self, message: str):
        safe_message = (
            message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        self.browser.setHtml(
            f"""
            <!doctype html>
            <html lang="id">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body{{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#fff8f6;color:#2b1712;display:grid;place-items:center;min-height:100vh}}
                main{{width:min(620px,calc(100vw - 48px));padding:28px;border:1px solid #f1c9bd;background:#fff;border-radius:8px;box-shadow:0 12px 32px rgba(92,42,24,.08)}}
                h1{{font-size:24px;margin:0 0 12px;font-weight:650}}
                p{{margin:0 0 14px;color:#6b4b40;line-height:1.5}}
                code{{display:block;padding:12px;background:#fff1ed;border:1px solid #f4d3ca;border-radius:6px;white-space:pre-wrap;color:#5a1f10}}
              </style>
            </head>
            <body>
              <main>
                <h1>Aplikasi belum siap</h1>
                <p>Tutup aplikasi lalu buka lagi. Jika masih gagal, hubungi bantuan dengan menyertakan pesan di bawah ini.</p>
                <code>{safe_message}</code>
              </main>
            </body>
            </html>
            """
        )

    def retry_load(self):
        """Coba muat ulang jika gagal (server mungkin belum siap)."""
        if health_check(timeout=0.75):
            print("========================================")
            print(f"STATUS API: BERHASIL TERKONEKSI DI {APP_URL}!")
            print("========================================")
            self.browser.setUrl(QUrl(self._target_url))
            return

        server_error = None
        if self._server_errors is not None and not self._server_errors.empty():
            server_error = self._server_errors.get()

        self._retries += 1
        if server_error is None and self._retries < self._max_retries:
            print(f"Menunggu API siap... (Percobaan ke-{self._retries})", end="\r")
            QTimer.singleShot(RETRY_INTERVAL_MS, self.retry_load)
            return

        error_message = compact_error(server_error)
        print(f"\n[ERROR] {error_message}")
        report_error_feedback(
            server_error or error_message,
            source="desktop_backend_retry",
            severity="critical",
            context=f"Backend lokal gagal siap setelah {self._retries} percobaan.",
        )
        self.show_error_page(error_message)

    def closeEvent(self, event):
        """Clean up PySide6 WebEngine instances gracefully to avoid profile warnings."""
        if hasattr(self, "browser") and self.browser:
            self.browser.setPage(None)
        if hasattr(self, "_page") and self._page:
            self._page.deleteLater()
        event.accept()


def main():
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.exception("Unhandled application exception", exc_info=(exc_type, exc_value, exc_traceback))
        report_error_feedback(exc_value, source="sys.excepthook", severity="critical")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def handle_thread_exception(args):
        logging.exception(
            "Unhandled thread exception",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        report_error_feedback(
            args.exc_value,
            source=f"thread:{getattr(args.thread, 'name', '')}",
            severity="critical",
        )

    sys.excepthook = handle_unhandled_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = handle_thread_exception

    app = QApplication(sys.argv)
    startup_license_status = verify_license(exit_on_fail=False, show_message=False)
    startup_license_valid = startup_license_status == LICENSE_STATUS_OK

    server_errors = queue.Queue()

    selected_port = find_available_port(APP_PORT)
    if selected_port != APP_PORT:
        print(f"Port {APP_PORT} sudah dipakai. Memakai port lokal {selected_port}.")
    configure_runtime_port(selected_port)

    server_thread = threading.Thread(target=run_fastapi, args=(server_errors, selected_port), daemon=True)
    server_thread.start()

    target_url = APP_URL if startup_license_valid else f"{APP_URL}/license"
    window = BrowserApp(server_errors, target_url=target_url)

    recheck_stop_event = threading.Event()
    recheck_notifier = LicenseRecheckNotifier()

    def redirect_to_license_page():
        window.load_url(f"{APP_URL}/license?reason=expired")

    recheck_notifier.invalid.connect(redirect_to_license_page)
    app.aboutToQuit.connect(recheck_stop_event.set)
    if startup_license_valid:
        start_license_recheck_thread(recheck_notifier, recheck_stop_event)

    window.show()

    QTimer.singleShot(100, window.retry_load)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
