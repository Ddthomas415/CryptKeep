from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

SUPPORTED_EXCHANGES = {"coinbase", "binance", "gateio"}

@dataclass
class PreflightResult:
    ok: bool
    checks: List[Dict[str, Any]]

def _check(name: str, ok: bool, detail: str, severity: str = "INFO") -> Dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": str(detail), "severity": str(severity)}

def run_preflight(cfg_path: str = "config/trading.yaml") -> PreflightResult:
    checks: List[Dict[str, Any]] = []

    p = Path(cfg_path)
    if not p.exists():
        checks.append(_check("config_exists", False, f"Missing {cfg_path}. Use Setup Wizard to generate it.", "ERROR"))
        return PreflightResult(ok=False, checks=checks)

    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    # Exchange support
    ex_id = str((cfg.get("pipeline") or {}).get("exchange_id") or "coinbase").lower().strip()
    checks.append(_check("exchange_supported", ex_id in SUPPORTED_EXCHANGES, f"exchange_id={ex_id} supported={sorted(SUPPORTED_EXCHANGES)}", "ERROR" if ex_id not in SUPPORTED_EXCHANGES else "INFO"))

    # Symbols
    symbols = cfg.get("symbols") or []
    checks.append(_check("symbols_configured", len(symbols) > 0, f"symbols={symbols}", "ERROR" if len(symbols) == 0 else "INFO"))

    # Executor mode
    exe = cfg.get("execution") or {}
    mode = str(exe.get("executor_mode") or "paper").lower().strip()
    checks.append(_check("executor_mode_valid", mode in ("paper","live"), f"executor_mode={mode}", "ERROR" if mode not in ("paper","live") else "INFO"))

    # Live gating
    live_enabled = bool(exe.get("live_enabled", False))
    if mode == "live":
        checks.append(_check("live_enabled", live_enabled, f"live_enabled={live_enabled} (required for live mode)", "ERROR" if not live_enabled else "INFO"))
    else:
        checks.append(_check("live_enabled", True, f"paper mode (live_enabled={live_enabled})", "INFO"))

    # DB writable
    db_path = str(exe.get("db_path") or "data/execution.sqlite")
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE IF NOT EXISTS preflight_ping(x INTEGER)")
        con.commit()
        con.close()
        checks.append(_check("db_writable", True, f"db_path={db_path}"))
    except Exception as e:
        checks.append(_check("db_writable", False, f"db_path={db_path} error={type(e).__name__}:{e}", "ERROR"))

    # Risk sanity
    risk = cfg.get("risk") or {}
    mx_loss = float(risk.get("max_daily_loss_quote") or 0.0)
    if mx_loss < 0:
        checks.append(_check("risk_max_daily_loss", False, "max_daily_loss_quote must be >= 0", "ERROR"))
    else:
        checks.append(_check("risk_max_daily_loss", True, f"max_daily_loss_quote={mx_loss}"))

    # Keys presence (best-effort; we just check env vars as a minimal signal)
    # We do NOT read your actual system keychain here.
    if mode == "live" and live_enabled:
        # generic env variable hints
        env_hits = [k for k in os.environ.keys() if any(s in k.upper() for s in ["COINBASE", "BINANCE", "GATE", "API_KEY", "APISECRET", "SECRET"])]
        checks.append(_check("live_keys_hint", len(env_hits) > 0, f"env_key_hints_found={len(env_hits)} (keychain may still be used)", "WARN" if len(env_hits)==0 else "INFO"))
    else:
        checks.append(_check("live_keys_hint", True, "not required in paper mode"))

    ok = all(c["ok"] or c["severity"] != "ERROR" for c in checks)
    return PreflightResult(ok=ok, checks=checks)
