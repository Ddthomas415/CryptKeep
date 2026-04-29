from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from services.desktop.simple_service_manager import specs_default


def test_service_ctl_list_has_tick_publisher():
    root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(root / "scripts" / "service_ctl.py"), "list"]
    out = subprocess.check_output(cmd, cwd=str(root), text=True)
    services = {line.strip() for line in out.splitlines() if line.strip()}
    assert "market_ws" in services
    assert "tick_publisher" in services
    assert "intent_consumer" in services
    assert "reconciler" in services
    assert "ops_signal_adapter" in services
    assert "ops_risk_gate" in services


def test_service_manager_uses_safe_wrappers_for_managed_live_services():
    specs = {spec.name: spec for spec in specs_default()}

    assert specs["market_ws"].cmd[-1] == "run"
    assert specs["market_ws"].cmd[-2].endswith("scripts/run_ws_ticker_feed_safe.py")
    assert specs["intent_consumer"].cmd[-1] == "run"
    assert specs["intent_consumer"].cmd[-2].endswith("scripts/run_intent_consumer_safe.py")
    assert specs["reconciler"].cmd[-1] == "run"
    assert specs["reconciler"].cmd[-2].endswith("scripts/run_live_reconciler_safe.py")
