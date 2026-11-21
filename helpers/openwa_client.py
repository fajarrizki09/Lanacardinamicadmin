from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


class OpenWAError(RuntimeError):
    """Raised when OpenWA API cannot complete the requested action."""


@dataclass
class OpenWAConfig:
    base_url: str = "http://127.0.0.1:3000/api"
    session_id: str = ""
    timeout_seconds: int = 15
    api_token: str = ""


class OpenWAClient:
    def __init__(self, config: OpenWAConfig):
        self.config = config
        self.base_url = str(config.base_url or "").strip().rstrip("/")
        if not self.base_url:
            raise OpenWAError("OpenWA Base URL belum diatur.")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = str(self.config.api_token or "").strip()
        if token:
            headers["X-Gateway-Token"] = token
        return headers

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        clean_path = path.lstrip('/')
        if clean_path.startswith('sessions/') and not self.base_url.endswith('/api'):
            clean_path = f"api/{clean_path}"
        url = f"{self.base_url}/{clean_path}"
        return self._request_url(method, url, payload)

    def _request_url(self, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=self._headers(), method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=max(1, int(self.config.timeout_seconds or 15))) as response:
                raw = response.read().decode("utf-8", errors="replace")
                if not raw:
                    return {"status_code": response.status}
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    return {"status_code": response.status, "raw": raw}
                if isinstance(parsed, dict):
                    parsed.setdefault("status_code", response.status)
                    return parsed
                return {"status_code": response.status, "data": parsed}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            detail = body
            try:
                parsed = json.loads(body)
                detail = parsed.get("message") or parsed.get("detail") or parsed.get("error") or body
            except Exception:
                pass
            raise OpenWAError(f"OpenWA HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise OpenWAError(f"Tidak bisa terhubung ke OpenWA: {reason}") from exc
        except TimeoutError as exc:
            raise OpenWAError("Koneksi ke OpenWA timeout.") from exc

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "health")

    def create_session(self, name: str) -> Dict[str, Any]:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise OpenWAError("Nama session OpenWA wajib diisi.")
        return self._request("POST", "sessions", {"name": clean_name})

    def start_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self._session_id(session_id)
        return self._request("POST", f"sessions/{urllib.parse.quote(sid)}/start")

    def logout_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self._session_id(session_id)
        try:
            return self._request("POST", f"sessions/{urllib.parse.quote(sid)}/logout")
        except OpenWAError as exc:
            message = str(exc)
            if "Cannot POST" not in message and "/layanan/koneksis/" not in message:
                raise
            fallback_base = self.base_url.rsplit("/", 1)[0] if self.base_url.endswith("/api") else self.base_url
            fallback_url = f"{fallback_base.rstrip('/')}/api/sessions/{urllib.parse.quote(sid)}/logout"
            return self._request_url("POST", fallback_url, None)

    def session_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self._session_id(session_id)
        return self._request("GET", f"sessions/{urllib.parse.quote(sid)}/status")

    def get_qr(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self._session_id(session_id)
        return self._request("GET", f"sessions/{urllib.parse.quote(sid)}/qr")

    def send_text(self, chat_id: str, text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self._session_id(session_id)
        target = str(chat_id or "").strip()
        body = str(text or "").strip()
        if not target:
            raise OpenWAError("Chat ID WhatsApp wajib diisi.")
        if not body:
            raise OpenWAError("Isi pesan WhatsApp wajib diisi.")
        return self._request(
            "POST",
            f"sessions/{urllib.parse.quote(sid)}/messages/send-text",
            {"chatId": target, "text": body},
        )

    def _session_id(self, session_id: Optional[str] = None) -> str:
        sid = str(session_id or self.config.session_id or "").strip()
        if not sid:
            raise OpenWAError("Session ID OpenWA belum diatur.")
        return sid


def normalize_indonesia_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", str(value or ""))
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    return digits


def phone_to_chat_id(value: str) -> str:
    phone = normalize_indonesia_phone(value)
    return f"{phone}@s.whatsapp.net" if phone else ""


def extract_openwa_message_id(response: Dict[str, Any]) -> str:
    if not isinstance(response, dict):
        return ""
    for key in ("id", "messageId", "message_id"):
        if response.get(key):
            return str(response[key])
    data = response.get("data")
    if isinstance(data, dict):
        for key in ("id", "messageId", "message_id"):
            if data.get(key):
                return str(data[key])
    return ""
