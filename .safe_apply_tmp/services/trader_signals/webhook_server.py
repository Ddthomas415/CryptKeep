from __future__ import annotations

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple
from pathlib import Path
from storage.signals_store_sqlite import SignalsStoreSQLite

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or "").strip()

def _token_ok(hdrs) -> bool:
    token = _env("CBP_TRADER_WEBHOOK_TOKEN", "")
    if not token:
        return True
    got = hdrs.get("X-CBP-Token") or hdrs.get("x-cbp-token") or ""
    return str(got).strip() == token

def _parse_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None

def _normalize_signal(obj: Dict[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None
    side = str(obj.get("side") or "").lower()
    if side not in ("buy", "sell"):
        return None
    sym = str(obj.get("symbol_norm") or obj.get("symbol") or "").strip().upper().replace("/", "-")
    if not sym:
        return None
    platform = str(obj.get("platform") or "manual").strip()
    trader_id = str(obj.get("trader_id") or "unknown").strip()
    ts = str(obj.get("ts") or _utcnow().isoformat())
    venue = str(obj.get("venue") or "").strip().lower()
    out = dict(obj)
    out["platform"] = platform
    out["trader_id"] = trader_id
    out["symbol_norm"] = sym
    out["side"] = side
    out["venue"] = venue
    out["ts"] = ts
    try:
        c = float(out.get("confidence", 0.5))
        if c < 0: c = 0.0
        if c > 1: c = 1.0
        out["confidence"] = c
    except Exception:
        out["confidence"] = 0.5
    return out

def _rate_limit_ok(signals_db_path: str, platform: str, trader_id: str, max_per_hour: int) -> Tuple[bool, str]:
    if max_per_hour <= 0:
        return True, "ok"
    try:
        since = (_utcnow() - timedelta(hours=1)).isoformat()
        conn = sqlite3.connect(signals_db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM trader_signals WHERE platform=? AND trader_id=? AND ts>=?",
                (platform, trader_id, since),
            ).fetchone()
            n = int(row[0]) if row else 0
        finally:
            conn.close()
        if n >= max_per_hour:
            return False, f"rate_limited:{n}>={max_per_hour}"
        return True, "ok"
    except Exception:
        return True, "ok"

class Handler(BaseHTTPRequestHandler):
    store = SignalsStoreSQLite(Path("data") / "signals.sqlite")

    def _send(self, code: int, obj: Dict[str, Any]):
        b = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/health"):
            self._send(200, {"ok": True, "service": "trader_webhook", "ts": _utcnow().isoformat()})
        else:
            self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if not _token_ok(self.headers):
            self._send(401, {"ok": False, "error": "unauthorized"})
            return
        if self.path not in ("/signal", "/batch"):
            self._send(404, {"ok": False, "error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except Exception:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        data = _parse_json(body)
        if data is None:
            self._send(400, {"ok": False, "error": "invalid_json"})
            return
        max_per_hour = int(_env("CBP_TRADER_MAX_PER_HOUR", "120") or "120")
        items: List[Dict[str, Any]] = []
        if isinstance(data, list):
            items = [x for x in data if isinstance(x, dict)]
        elif isinstance(data, dict):
            items = [data]
        else:
            self._send(400, {"ok": False, "error": "json_must_be_object_or_list"})
            return
        accepted = 0
        rejected = 0
        reasons = {}
        import asyncio
        async def run():
            nonlocal accepted, rejected, reasons
            for obj in items:
                norm = _normalize_signal(obj)
                if not norm:
                    rejected += 1
                    reasons["bad_signal"] = reasons.get("bad_signal", 0) + 1
                    continue
                ok_rl, why = _rate_limit_ok(str(Path("data") / "signals.sqlite"), norm["platform"], norm["trader_id"], max_per_hour)
                if not ok_rl:
                    rejected += 1
                    reasons[why] = reasons.get(why, 0) + 1
                    continue
                ok = await self.store.upsert_signal(norm)
                if ok:
                    accepted += 1
                else:
                    rejected += 1
                    reasons["db_reject"] = reasons.get("db_reject", 0) + 1
        asyncio.run(run())
        self._send(200, {"ok": True, "accepted": accepted, "rejected": rejected, "reasons": reasons})

def main():
    host = _env("CBP_TRADER_WEBHOOK_HOST", "127.0.0.1")
    port = int(_env("CBP_TRADER_WEBHOOK_PORT", "8787") or "8787")
    httpd = HTTPServer((host, port), Handler)
    print("trader_webhook listening", {"host": host, "port": port, "token_required": bool(_env("CBP_TRADER_WEBHOOK_TOKEN",""))})
    httpd.serve_forever()

if __name__ == "__main__":
    main()
