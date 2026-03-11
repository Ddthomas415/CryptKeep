from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from services.admin.config_editor import load_user_yaml
from services.evidence.ingest import ingest_event
from services.os.app_paths import ensure_dirs, runtime_dir

FLAGS_DIR = runtime_dir() / "flags"
STOP_FILE = FLAGS_DIR / "evidence_webhook.stop"

_RUNTIME_CFG: Dict[str, Any] = {}


def _cfg() -> Dict[str, Any]:
    cfg = load_user_yaml()
    evidence = cfg.get("evidence") if isinstance(cfg.get("evidence"), dict) else {}
    webhook = evidence.get("webhook") if isinstance(evidence.get("webhook"), dict) else {}
    return {
        "host": str(os.environ.get("CBP_EVIDENCE_HOST") or webhook.get("host") or "127.0.0.1"),
        "port": int(os.environ.get("CBP_EVIDENCE_PORT") or webhook.get("port") or 8787),
        "source_id": str(webhook.get("source_id") or "webhook_default"),
        "source_type": str(webhook.get("source_type") or "webhook"),
        "display_name": str(webhook.get("display_name") or "Webhook Source"),
        "consent_confirmed": bool(webhook.get("consent_confirmed", True)),
        "require_hmac": bool(webhook.get("require_hmac", False)),
        "hmac_secret": str(webhook.get("hmac_secret") or ""),
        "hmac_header": str(webhook.get("hmac_header") or "X-Signature"),
        "allow_public_bind": bool(webhook.get("allow_public_bind", False)),
    }


def _bind_guard(cfg: Dict[str, Any]) -> None:
    host = str(cfg.get("host") or "")
    if bool(cfg.get("allow_public_bind")):
        return
    if host in {"127.0.0.1", "localhost", "::1"}:
        return
    raise RuntimeError("Public bind is disabled; use 127.0.0.1 or set evidence.webhook.allow_public_bind=true")


def _validate_hmac(body: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False
    sig = (signature or "").strip()
    if "=" in sig:
        _, sig = sig.split("=", 1)
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig.lower())


def _write_json(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    handler.send_response(int(status))
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[evidence_webhook] {self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/health", "/healthz"}:
            _write_json(self, 200, {"ok": True})
            return
        _write_json(self, 404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/evidence":
            _write_json(self, 404, {"ok": False, "error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"

        if bool(_RUNTIME_CFG.get("require_hmac")):
            hdr_name = str(_RUNTIME_CFG.get("hmac_header") or "X-Signature")
            sig = self.headers.get(hdr_name, "")
            if not _validate_hmac(raw, sig, str(_RUNTIME_CFG.get("hmac_secret") or "")):
                _write_json(self, 401, {"ok": False, "error": "bad_signature"})
                return

        try:
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
        except Exception as e:
            _write_json(self, 400, {"ok": False, "error": f"invalid_json: {type(e).__name__}: {e}"})
            return

        out = ingest_event(
            payload,
            source_id=str(_RUNTIME_CFG["source_id"]),
            source_type=str(_RUNTIME_CFG["source_type"]),
            display_name=str(_RUNTIME_CFG["display_name"]),
            consent_confirmed=bool(_RUNTIME_CFG["consent_confirmed"]),
        )
        if out.get("ok"):
            _write_json(self, 200, out)
            return
        if out.get("quarantined"):
            _write_json(self, 202, out)
            return
        _write_json(self, 400, out)


def request_stop() -> dict:
    ensure_dirs()
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text("1\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}


def run() -> None:
    ensure_dirs()
    cfg = _cfg()
    try:
        _bind_guard(cfg)
    except RuntimeError as e:
        print(f"Bind error: {e}")
        return

    global _RUNTIME_CFG
    _RUNTIME_CFG = dict(cfg)

    host = str(cfg["host"])
    port = int(cfg["port"])
    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except Exception:
            pass

    httpd = HTTPServer((host, port), Handler)
    httpd.timeout = 1.0
    print(f"[evidence_webhook] listening on http://{host}:{port}/evidence (hmac_required={cfg['require_hmac']})")
    try:
        while True:
            if STOP_FILE.exists():
                break
            httpd.handle_request()
    finally:
        httpd.server_close()
        print("[evidence_webhook] stopped")
