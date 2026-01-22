from __future__ import annotations

import os
import sys
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

def now_ms() -> int:
    return int(time.time() * 1000)

def can_bind(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass

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
    out: Dict[str, Any] = {"ts_ms": now_ms()}

    out["python"] = {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "platform": sys.platform,
    }

    # Config presence
    ty = Path(cfg.trading_yaml)
    out["config"] = {
        "trading_yaml_exists": ty.exists(),
        "trading_yaml_path": str(ty),
    }

    # Env vars (presence only, never values)
    keys = ["EXCHANGE_API_KEY", "EXCHANGE_API_SECRET", "EXCHANGE_API_PASSPHRASE", "ENABLE_RUNBOOK_EXECUTION"]
    out["env"] = {k: ("set" if (os.environ.get(k) not in (None, "")) else "missing") for k in keys}

    # Port availability
    out["network"] = {
        "bind_ok": can_bind(cfg.host, int(cfg.port)),
        "host": cfg.host,
        "port": int(cfg.port),
    }

    # DB write access (best effort)
    out["storage"] = {
        "can_write_orders": file_writable("data/orders.sqlite"),
        "can_write_portfolio": file_writable("data/portfolio.sqlite"),
        "can_write_recon": file_writable("data/reconciliation.sqlite"),
        "can_write_runbooks": file_writable("data/repair_runbooks.sqlite"),
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
    if not out["config"]["trading_yaml_exists"]:
        hard_fails.append("missing config/trading.yaml")
    if not out["network"]["bind_ok"]:
        hard_fails.append("port not available (8501)")
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
