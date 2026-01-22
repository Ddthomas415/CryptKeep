from __future__ import annotations

import os
import sys
import json
import socket
import importlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

REQUIRED_IMPORTS = [
    "streamlit",
    "yaml",
    "ccxt",
    "pandas",
    "numpy",
    "sqlite3",
]

REQUIRED_PATHS = [
    "config/trading.yaml",
    "dashboard/app.py",
]

@dataclass
class Check:
    name: str
    ok: bool
    detail: str

def _port_free(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return False
    except Exception:
        return True

def run() -> Dict[str, Any]:
    checks: List[Check] = []
    root = Path(".").resolve()

    # Python version (Streamlit supports recent 3 minors; avoid ancient)
    pyv = sys.version_info
    checks.append(Check("python_version", pyv.major == 3 and pyv.minor >= 10, f"{pyv.major}.{pyv.minor}.{pyv.micro}"))

    # Required files
    for rp in REQUIRED_PATHS:
        p = root / rp
        checks.append(Check(f"exists:{rp}", p.exists(), str(p)))

    # Required imports
    for mod in REQUIRED_IMPORTS:
        try:
            importlib.import_module(mod)
            checks.append(Check(f"import:{mod}", True, "ok"))
        except Exception as e:
            checks.append(Check(f"import:{mod}", False, f"{type(e).__name__}: {e}"))

    # Data dirs
    for d in ["data", "docs", "storage", "services", "dashboard", "scripts"]:
        p = root / d
        checks.append(Check(f"dir:{d}", p.exists() and p.is_dir(), str(p)))

    # Port availability
    host = os.environ.get("CBP_HOST", "127.0.0.1")
    port = int(os.environ.get("CBP_PORT", "8501"))
    free = _port_free(host, port)
    checks.append(Check("port_free", free, f"{host}:{port} ({'free' if free else 'in_use'})"))

    # Config sanity (read YAML)
    cfg_ok = False
    cfg_detail = ""
    try:
        import yaml
        cfg = yaml.safe_load((root / "config/trading.yaml").read_text(encoding="utf-8"))
        cfg_ok = isinstance(cfg, dict)
        # minimal keys
        live = (cfg or {}).get("live") or {}
        ex = str(live.get("exchange_id") or "")
        sym = (cfg or {}).get("symbols") or []
        cfg_detail = f"exchange_id={ex} symbols={len(sym)}"
    except Exception as e:
        cfg_ok = False
        cfg_detail = f"{type(e).__name__}: {e}"
    checks.append(Check("config_yaml_parse", cfg_ok, cfg_detail))

    ok = all(c.ok for c in checks if not c.name.startswith("port_free")) and True
    # port_free is informational (you may already be running); don't fail preflight on it
    return {
        "ok": ok,
        "root": str(root),
        "checks": [asdict(c) for c in checks],
    }

def main() -> int:
    out = run()
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
