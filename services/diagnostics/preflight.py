from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from services.config_loader import runtime_trading_config_available
from services.os.app_paths import data_dir, ensure_dirs
from services.os.ports import can_bind, resolve_preferred_port

def now_ms() -> int:
    return int(time.time() * 1000)

def file_writable(path: str) -> bool:
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False

@dataclass(frozen=True)
class PreflightConfig:
    host: str = "127.0.0.1"
    port: int = 8501
    trading_yaml: str = "config/trading.yaml"

def run_preflight(cfg: PreflightConfig = PreflightConfig()) -> Dict[str, Any]:
    ensure_dirs()
    droot = data_dir()
    out: Dict[str, Any] = {"ts_ms": now_ms()}

    out["python"] = {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "platform": sys.platform,
    }

    # Config presence
    ty = Path(cfg.trading_yaml)
    runtime_cfg_available = runtime_trading_config_available(cfg.trading_yaml)
    out["config"] = {
        "runtime_trading_config_available": runtime_cfg_available,
        "trading_yaml_exists": ty.exists(),
        "trading_yaml_path": str(ty),
    }

    # Env vars (presence only, never values)
    keys = ["EXCHANGE_API_KEY", "EXCHANGE_API_SECRET", "EXCHANGE_API_PASSPHRASE", "ENABLE_RUNBOOK_EXECUTION"]
    out["env"] = {k: ("set" if (os.environ.get(k) not in (None, "")) else "missing") for k in keys}

    # Port availability
    resolution = resolve_preferred_port(
        cfg.host,
        int(cfg.port),
        max_offset=int(os.environ.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )
    out["network"] = {
        "bind_ok": can_bind(cfg.host, int(resolution.resolved_port)),
        "host": resolution.host,
        "requested_port": int(resolution.requested_port),
        "resolved_port": int(resolution.resolved_port),
        "requested_available": bool(resolution.requested_available),
        "auto_switched": bool(resolution.auto_switched),
    }

    # DB write access (best effort)
    out["storage"] = {
        "can_write_orders": file_writable(str(droot / "orders.sqlite")),
        "can_write_portfolio": file_writable(str(droot / "portfolio.sqlite")),
        "can_write_recon": file_writable(str(droot / "reconciliation.sqlite")),
        "can_write_runbooks": file_writable(str(droot / "repair_runbooks.sqlite")),
    }

    # Quick imports
    import_status = {}
    for mod in ["streamlit", "ccxt"]:
        try:
            __import__(mod)
            import_status[mod] = "ok"
        except Exception as e:
            import_status[mod] = f"FAIL: {type(e).__name__}"
    out["imports"] = import_status

    # Overall
    hard_fails = []
    if not out["config"]["runtime_trading_config_available"]:
        hard_fails.append("missing runtime trading config")
    if not out["network"]["bind_ok"]:
        hard_fails.append(f"no available UI port near {cfg.port}")
    if import_status.get("streamlit","").startswith("FAIL"):
        hard_fails.append("streamlit not importable")
    if import_status.get("ccxt","").startswith("FAIL"):
        hard_fails.append("ccxt not importable")

    out["status"] = "OK" if not hard_fails else "BLOCKED"
    out["blocked_reasons"] = hard_fails
    return out

def diagnostics_text(preflight: Dict[str, Any]) -> str:
    # deterministic, copy/paste friendly
    import json
    return json.dumps(preflight, indent=2, sort_keys=True)
