from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def test_ops_signal_adapter_script_import_safe():
    mod = importlib.import_module("scripts.run_ops_signal_adapter")
    assert mod is not None


def test_ops_signal_adapter_script_once_writes_snapshot(tmp_path):
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    script = str(root / "scripts" / "run_ops_signal_adapter.py")
    db = str(tmp_path / "ops.sqlite")

    out = subprocess.run(
        [py, script, "once", "--db", db, "--symbol", "BTC/USD"],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    assert out.returncode == 0
    payload = json.loads((out.stdout or "{}").strip() or "{}")
    assert payload.get("ok") is True
    assert int(payload.get("raw_id") or 0) > 0

    store = OpsSignalStoreSQLite(path=db)
    latest = store.latest_raw_signal()
    assert isinstance(latest, dict)
    assert latest.get("source") == "ops_signal_adapter"


def test_ops_signal_adapter_script_stop_writes_flag(tmp_path):
    root = Path(__file__).resolve().parents[1]
    py = sys.executable
    script = str(root / "scripts" / "run_ops_signal_adapter.py")
    env = dict(os.environ)
    env["CBP_STATE_DIR"] = str(tmp_path / "state")

    out = subprocess.run([py, script, "stop"], cwd=str(root), text=True, capture_output=True, env=env)
    assert out.returncode == 0
    payload = json.loads((out.stdout or "{}").strip() or "{}")
    assert payload.get("ok") is True
    assert (tmp_path / "state" / "runtime" / "flags" / "ops_signal_adapter.stop").exists()

