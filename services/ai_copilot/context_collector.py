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


def collect_incident_context(extra_notes: str = "") -> str:
    ctx: Dict[str, Any] = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    guard_path = runtime_dir() / "flags" / "system_guard.json"
    ctx["system_guard"] = json.loads(guard_path.read_text()) if guard_path.exists() else {"state": "missing"}

    ks_path = runtime_dir() / "flags" / "kill_switch.json"
    ctx["kill_switch"] = json.loads(ks_path.read_text()) if ks_path.exists() else {"armed": "unknown"}

    exec_db = data_dir() / "execution.sqlite"
    if exec_db.exists():
        ctx["recent_intents"] = _safe_sqlite_query(
            exec_db,
            "SELECT intent_id, ts_ms, symbol, side, status, reason FROM intents ORDER BY ts_ms DESC LIMIT 20",
        )
        ctx["risk_daily"] = _safe_sqlite_query(
            exec_db,
            "SELECT * FROM risk_daily ORDER BY day DESC LIMIT 7",
        )
        ctx["symbol_locks"] = _safe_sqlite_query(
            exec_db,
            "SELECT symbol, locked_until_ms, loss_count, reason FROM symbol_locks WHERE locked_until_ms > 0",
        )

    le_db = data_dir() / "lifecycle_events.sqlite"
    if le_db.exists():
        ctx["recent_lifecycle_events"] = _safe_sqlite_query(
            le_db,
            "SELECT ts_ms, venue, symbol, event, ref_id FROM lifecycle_events ORDER BY id DESC LIMIT 20",
        )

    flags_dir = runtime_dir() / "flags"
    health: Dict[str, Any] = {}
    if flags_dir.exists():
        for f in flags_dir.glob("*.status.json"):
            try:
                health[f.stem.replace(".status", "")] = json.loads(f.read_text())
            except Exception:
                pass
    ctx["service_health"] = health

    log_path = data_dir() / "logs" / "bot.log"
    if log_path.exists():
        try:
            lines = log_path.read_text(errors="replace").splitlines()
            ctx["recent_logs"] = "\n".join(lines[-50:])
        except Exception:
            ctx["recent_logs"] = "[unreadable]"

    parts = [
        "=== CryptKeep System State ===",
        f"Collected: {ctx['collected_at']}",
        "\n--- System Guard ---",
        json.dumps(ctx.get("system_guard"), indent=2),
        "\n--- Kill Switch ---",
        json.dumps(ctx.get("kill_switch"), indent=2),
        "\n--- Service Health ---",
        json.dumps(ctx.get("service_health"), indent=2),
        "\n--- Recent Intents ---",
        json.dumps(ctx.get("recent_intents"), indent=2),
        "\n--- Symbol Locks ---",
        json.dumps(ctx.get("symbol_locks"), indent=2),
        "\n--- Risk Daily ---",
        json.dumps(ctx.get("risk_daily"), indent=2),
        "\n--- Recent Lifecycle Events ---",
        json.dumps(ctx.get("recent_lifecycle_events"), indent=2),
        "\n--- Recent Logs ---",
        ctx.get("recent_logs", "(none)"),
    ]
    if extra_notes:
        parts.append(f"\n--- Operator Notes ---\n{extra_notes}")

    return "\n".join(str(p) for p in parts)[:MAX_CONTEXT_CHARS]
