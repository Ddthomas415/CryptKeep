from __future__ import annotations

import json
import time
from pathlib import Path

from services.os.app_paths import data_dir
from services.exchanges.symbols import normalize_symbol

PATH = data_dir() / "ws_feature_blacklist.json"

def _key(venue: str, symbol: str, feature: str) -> str:
    v = str(venue).strip().lower()
    s = normalize_symbol(symbol)
    f = str(feature).strip()
    return f"{v}::{s}::{f}"

def _load() -> dict:
    try:
        if not PATH.exists():
            return {"items": {}}
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"items": {}}

def _save(doc: dict) -> dict:
    try:
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "path": str(PATH)}
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}:{e}"}

def list_items() -> dict:
    doc = _load()
    items = doc.get("items", {})
    if not isinstance(items, dict):
        items = {}
    return {"ok": True, "path": str(PATH), "items": items}

def clear_all() -> dict:
    return _save({"items": {}})

def clear_one(*, venue: str, symbol: str, feature: str) -> dict:
    doc = _load()
    items = doc.get("items", {})
    if not isinstance(items, dict):
        items = {}
    k = _key(venue, symbol, feature)
    if k in items:
        del items[k]
    doc["items"] = items
    return _save(doc)

def disable(*, venue: str, symbol: str, feature: str, reason: str, cooldown_sec: int = 1800) -> dict:
    doc = _load()
    items = doc.get("items", {})
    if not isinstance(items, dict):
        items = {}
    now = time.time()
    k = _key(venue, symbol, feature)
    items[k] = {
        "venue": str(venue).strip().lower(),
        "symbol": normalize_symbol(symbol),
        "feature": str(feature),
        "reason": str(reason)[:500],
        "disabled_ts": float(now),
        "cooldown_sec": int(cooldown_sec),
        "until_ts": float(now + float(cooldown_sec)),
    }
    doc["items"] = items
    res = _save(doc)
    return {"ok": bool(res.get("ok")), "key": k, "item": items[k], **res}

def is_disabled(*, venue: str, symbol: str, feature: str) -> dict:
    doc = _load()
    items = doc.get("items", {})
    if not isinstance(items, dict):
        items = {}
    k = _key(venue, symbol, feature)
    item = items.get(k)
    if not isinstance(item, dict):
        return {"ok": True, "disabled": False, "key": k}

    # auto-expire
    try:
        until = float(item.get("until_ts", 0.0))
        now = time.time()
        if now >= until:
            del items[k]
            doc["items"] = items
            _save(doc)
            return {"ok": True, "disabled": False, "expired": True, "key": k}
    except Exception:
        pass

    return {"ok": True, "disabled": True, "key": k, "item": item}
