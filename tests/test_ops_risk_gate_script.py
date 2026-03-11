from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def test_ops_risk_gate_script_import_safe():
    mod = importlib.import_module("scripts.run_ops_risk_gate_service")
    assert mod is not None


def test_ops_risk_gate_script_once_exit_codes(tmp_path):
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    script = str(root / "scripts" / "run_ops_risk_gate_service.py")
    db = str(tmp_path / "ops.sqlite")

    no_data = subprocess.run(
        [py, script, "once", "--db", db],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    assert no_data.returncode == 2
    payload_no = json.loads((no_data.stdout or "{}").strip() or "{}")
    assert payload_no.get("reason") == "no_raw_signal"

    store = OpsSignalStoreSQLite(path=db)
    store.insert_raw_signal(
        {
            "ts": "2026-03-09T00:00:00+00:00",
            "source": "bot",
            "exchange_api_ok": True,
            "order_reject_rate": 0.01,
            "ws_lag_ms": 120.0,
            "venue_latency_ms": 100.0,
            "realized_volatility": 0.01,
            "drawdown_pct": 1.0,
            "pnl_usd": 1.0,
            "exposure_usd": 1000.0,
            "leverage": 1.0,
        }
    )

    ok = subprocess.run(
        [py, script, "once", "--db", db],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    assert ok.returncode == 0
    payload_ok = json.loads((ok.stdout or "{}").strip() or "{}")
    assert payload_ok.get("ok") is True
    assert "gate" in payload_ok


def test_ops_risk_gate_script_stop_command_writes_flag(tmp_path):
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    script = str(root / "scripts" / "run_ops_risk_gate_service.py")
    env = dict(os.environ)
    env["CBP_STATE_DIR"] = str(tmp_path / "state")
    out = subprocess.run([py, script, "stop"], cwd=str(root), text=True, capture_output=True, env=env)
    assert out.returncode == 0
    payload = json.loads((out.stdout or "{}").strip() or "{}")
    assert payload.get("ok") is True
    assert (tmp_path / "state" / "runtime" / "flags" / "ops_risk_gate_service.stop").exists()
