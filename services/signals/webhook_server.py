from __future__ import annotations
import json
import hashlib
import hmac
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime, timezone
from services.signals.normalizer import normalize_signal
from storage.signal_inbox_sqlite import SignalInboxSQLite

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _validate_hmac(body: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False
    sig = (signature or "").strip()
    if "=" in sig:
        _, sig = sig.split("=", 1)
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig.lower())

class Handler(BaseHTTPRequestHandler):
    inbox = SignalInboxSQLite()

    def _send(self, code: int, obj: dict):
        raw = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path not in ("/signal", "/signals"):
            self._send(404, {"ok": False, "reason": "not_found", "path": u.path})
            return
        try:
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(n) if n > 0 else b"{}"
            secret = str(os.environ.get("SIGNAL_WEBHOOK_SECRET") or "")
            header = str(os.environ.get("SIGNAL_WEBHOOK_HEADER") or "X-Signature")
            sig_header = str(self.headers.get(header) or "")
            if not _validate_hmac(body, sig_header, secret):
                self._send(401, {"ok": False, "reason": "unauthorized"})
                return
            payload = json.loads(body.decode("utf-8", errors="replace"))
            if not isinstance(payload, dict):
                raise ValueError("payload_must_be_object")
            sig = normalize_signal(payload)
            self.inbox.upsert_signal({
                "signal_id": sig.signal_id,
                "ts": sig.ts,
                "received_ts": _now(),
                "source": sig.source,
                "author": sig.author,
                "venue_hint": sig.venue_hint,
                "symbol": sig.symbol,
                "action": sig.action,
                "confidence": sig.confidence,
                "notes": sig.notes,
                "raw": sig.raw,
                "status": "new",
            })
            self._send(200, {"ok": True, "signal_id": sig.signal_id})
        except Exception as e:
            self._send(400, {"ok": False, "reason": "invalid_request", "error_type": type(e).__name__})

    def log_message(self, fmt, *args):
        return

def run(host: str = "127.0.0.1", port: int = 8787):
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Public bind is disabled; use 127.0.0.1")
    srv = HTTPServer((host, int(port)), Handler)
    srv.serve_forever()
