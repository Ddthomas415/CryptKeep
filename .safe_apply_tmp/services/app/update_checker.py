from __future__ import annotations
import json
import socket
import urllib.request
from services.admin.config_editor import load_user_yaml

def _cfg() -> dict:
    cfg = load_user_yaml()
    u = cfg.get("updates") if isinstance(cfg.get("updates"), dict) else {}
    return {
        "enabled": bool(u.get("enabled", False)),
        "channel_url": str(u.get("channel_url", "") or "").strip(),
        "timeout_sec": float(u.get("timeout_sec", 5.0) or 5.0),
        "allow_download": bool(u.get("allow_download", False)),
    }

def _safe_fetch_json(url: str, timeout_sec: float) -> dict:
    socket.setdefaulttimeout(float(timeout_sec))
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoBotPro/1.0"})
    with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)

def check_for_update(current_version: str) -> dict:
    cfg = _cfg()
    if not cfg["enabled"]:
        return {"ok": True, "enabled": False, "reason": "updates.disabled"}
    if not cfg["channel_url"]:
        return {"ok": False, "enabled": True, "reason": "updates.channel_url_missing"}
    try:
        data = _safe_fetch_json(cfg["channel_url"], cfg["timeout_sec"])
    except Exception as e:
        return {"ok": False, "enabled": True, "reason": f"fetch_failed:{type(e).__name__}:{e}"}
    latest = str(data.get("latest_version") or "").strip()
    if not latest:
        return {"ok": False, "enabled": True, "reason": "bad_channel_payload:missing_latest_version", "data": data}
    def parse(v: str):
        parts = v.strip().split(".")
        out = []
        for p in parts[:3]:
            try:
                out.append(int(p))
            except Exception:
                return None
        while len(out) < 3:
            out.append(0)
        return tuple(out)
    cur_p = parse(current_version)
    lat_p = parse(latest)
    is_newer = False
    if cur_p is not None and lat_p is not None:
        is_newer = lat_p > cur_p
    else:
        is_newer = latest != current_version
    return {
        "ok": True,
        "enabled": True,
        "current_version": current_version,
        "latest_version": latest,
        "update_available": bool(is_newer),
        "published_ts": data.get("published_ts"),
        "notes": data.get("notes"),
        "release_page_url": data.get("release_page_url"),
        "download_url": data.get("download_url"),
        "allow_download": bool(cfg["allow_download"]),
        "raw": data,
    }

def download_update(download_url: str, dest_path: str, *, timeout_sec: float = 30.0) -> dict:
    try:
        socket.setdefaulttimeout(float(timeout_sec))
        req = urllib.request.Request(download_url, headers={"User-Agent": "CryptoBotPro/1.0"})
        with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
            data = resp.read()
        import pathlib
        p = pathlib.Path(dest_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return {"ok": True, "saved_to": str(p), "bytes": len(data)}
    except Exception as e:
        return {"ok": False, "reason": f"download_failed:{type(e).__name__}:{e}"}
