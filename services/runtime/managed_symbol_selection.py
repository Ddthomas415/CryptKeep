from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir
from services.runtime.managed_symbol_config import normalize_symbols, resolve_managed_symbols


def _selection_path() -> Path:
    return runtime_dir() / "health" / "managed_symbol_selection.json"


def _load_selection() -> dict[str, Any]:
    path = _selection_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_managed_symbol_selection(
    cfg: dict[str, Any],
    *,
    venue: str,
    mode: str,
    live_enabled: bool,
) -> dict[str, Any]:
    base_symbols = resolve_managed_symbols(cfg)
    out: dict[str, Any] = {
        "source": "static",
        "symbols": list(base_symbols),
        "base_symbols": list(base_symbols),
        "selected_symbols": list(base_symbols),
        "protected_symbols": [],
        "protected_symbol_details": [],
        "scan_ok": None,
        "reason": "static_config",
    }

    if mode != "paper" or live_enabled:
        return out

    selection = _load_selection()
    if not selection:
        return out

    out["scan_ok"] = bool(selection.get("ok"))
    selected = normalize_symbols(selection.get("selected"))
    selected_venue = str(selection.get("venue") or "").strip().lower()
    if selected_venue and venue and selected_venue != str(venue).strip().lower():
        out["reason"] = "scanner_venue_mismatch"
        return out
    if bool(selection.get("ok")) and selected:
        out.update(
            {
                "source": str(selection.get("source") or "scanner"),
                "symbols": list(selected),
                "selected_symbols": list(selected),
                "reason": "scanner_selected",
            }
        )
        return out

    out["reason"] = "scanner_fallback_to_base"
    return out
