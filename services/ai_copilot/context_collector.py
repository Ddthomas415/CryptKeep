from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

from services.os.app_paths import data_dir, runtime_dir
from services.ai_copilot.policy import MAX_CONTEXT_CHARS


def _safe_sqlite_query(db_path: Path, query: str, limit: int = 20) -> list[dict]:
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchmany(limit)
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def collect_system_state() -> Dict[str, Any]:
    ctx: Dict[str, Any] = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    guard_path = runtime_dir() / "flags" / "system_guard.json"
    if guard_path.exists():
        try:
            ctx["system_guard"] = json.loads(guard_path.read_text())
        except Exception:
            ctx["system_guard"] = {"error": "unreadable"}
    else:
        ctx["system_guard"] = {"state": "missing"}

    ks_path = runtime_dir() / "flags" / "kill_switch.json"
    if ks_path.exists():
        try:
            ctx["kill_switch"] = json.loads(ks_path.read_text())
        except Exception:
            ctx["kill_switch"] = {"error": "unreadable"}

    le_db = data_dir() / "lifecycle_events.sqlite"
    if le_db.exists():
        ctx["recent_lifecycle_events"] = _safe_sqlite_query(
            le_db,
            "SELECT ts_ms, venue, symbol, event, ref_id, payload "
            "FROM lifecycle_events ORDER BY id DESC LIMIT 20",
        )

    exec_db = data_dir() / "execution.sqlite"
    if exec_db.exists():
        ctx["recent_intents"] = _safe_sqlite_query(
            exec_db,
            "SELECT intent_id, ts_ms, symbol, side, status, reason "
            "FROM intents ORDER BY ts_ms DESC LIMIT 20",
        )
        ctx["risk_daily"] = _safe_sqlite_query(
            exec_db,
            "SELECT day, realized_pnl, fee_total, fill_count "
            "FROM risk_daily ORDER BY day DESC LIMIT 7",
        )
        ctx["symbol_locks"] = _safe_sqlite_query(
            exec_db,
            "SELECT symbol, locked_until_ms, loss_count, reason "
            "FROM symbol_locks WHERE locked_until_ms > 0",
        )

    flags_dir = runtime_dir() / "flags"
    health: Dict[str, Any] = {}
    if flags_dir.exists():
        for f in flags_dir.glob("*.status.json"):
            try:
                health[f.stem.replace(".status", "")] = json.loads(f.read_text())
            except Exception:
                health[f.stem] = {"error": "unreadable"}
    ctx["service_health"] = health

    try:
        from services.os.app_paths import logs_dir
        log_path = logs_dir() / "bot.log"
    except Exception:
        log_path = data_dir() / "logs" / "bot.log"

    if log_path.exists():
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            ctx["recent_logs"] = "\n".join(lines[-50:])
        except Exception:
            ctx["recent_logs"] = "[unreadable]"

    return ctx


def collect_incident_context(extra_notes: str = "") -> str:
    state = collect_system_state()
    parts = [
        "=== CryptKeep System State ===",
        f"Collected: {state['collected_at']}",
        "\n--- System Guard ---",
        json.dumps(state.get("system_guard"), indent=2),
        "\n--- Kill Switch ---",
        json.dumps(state.get("kill_switch"), indent=2),
        "\n--- Service Health ---",
        json.dumps(state.get("service_health"), indent=2),
        "\n--- Recent Intents (last 20) ---",
        json.dumps(state.get("recent_intents"), indent=2),
        "\n--- Symbol Locks ---",
        json.dumps(state.get("symbol_locks"), indent=2),
        "\n--- Risk Daily (last 7 days) ---",
        json.dumps(state.get("risk_daily"), indent=2),
        "\n--- Recent Lifecycle Events (last 20) ---",
        json.dumps(state.get("recent_lifecycle_events"), indent=2),
        "\n--- Recent Logs (last 50 lines) ---",
        state.get("recent_logs", "(no logs)"),
    ]
    if extra_notes:
        parts.append(f"\n--- Operator Notes ---\n{extra_notes}")

    full = "\n".join(str(p) for p in parts)
    return full[:MAX_CONTEXT_CHARS]
