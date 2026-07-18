"""Integration proof for campaign stop/failure alert wiring (Active #23).

Proves the hook in paper_strategy_evidence_service._write_status:
- fires the campaign alert on a real running->stopped transition
- the alert receives the status payload (reason/symbol)
- a RAISING alert channel cannot block the status write (the file still
  advances), matching the notification-only contract
- the first write is a silent baseline (no prior status to transition from)
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path


def _reload(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.analytics.paper_strategy_evidence_service as svc

    importlib.reload(app_paths)
    importlib.reload(svc)
    return svc


def test_write_status_fires_alert_on_stop_transition(monkeypatch, tmp_path):
    svc = _reload(monkeypatch, tmp_path)
    sent: list[tuple[str, str, dict | None]] = []
    import services.alerts.campaign_events as ce
    monkeypatch.setattr(ce, "_send", lambda level, message, payload: sent.append((level, message, payload)))

    # First write establishes baseline silently.
    svc._write_status({"status": "running", "symbol": "BTC/USDT"})
    assert sent == []

    # Transition running -> stopped fires exactly one warning-level alert.
    svc._write_status({"status": "stopped", "reason": "stop_requested", "symbol": "BTC/USDT"})
    assert len(sent) == 1
    level, message, payload = sent[0]
    assert level == "warning"
    assert message == "campaign:stopped"
    assert payload["reason"] == "stop_requested"
    assert payload["symbol"] == "BTC/USDT"

    # Status file advanced to stopped regardless.
    written = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert written["status"] == "stopped"


def test_write_status_fires_alert_once_on_blocked_transition(monkeypatch, tmp_path):
    svc = _reload(monkeypatch, tmp_path)
    sent: list[tuple[str, str, dict | None]] = []
    import services.alerts.campaign_events as ce
    monkeypatch.setattr(ce, "_send", lambda level, message, payload: sent.append((level, message, payload)))

    svc._write_status({"status": "running", "symbol": "BTC/USD"})
    svc._write_status({"status": "blocked", "reason": "ohlcv_source_unreachable", "symbol": "BTC/USD"})
    svc._write_status({"status": "blocked", "reason": "ohlcv_source_unreachable", "symbol": "BTC/USD"})

    assert len(sent) == 1
    level, message, payload = sent[0]
    assert level == "warning"
    assert message == "campaign:blocked"
    assert payload["reason"] == "ohlcv_source_unreachable"
    assert payload["symbol"] == "BTC/USD"


def test_raising_channel_does_not_block_status_write(monkeypatch, tmp_path):
    svc = _reload(monkeypatch, tmp_path)
    import services.alerts.campaign_events as ce

    def _boom(level, message, payload):
        raise RuntimeError("dispatcher exploded")

    monkeypatch.setattr(ce, "_send", _boom)

    svc._write_status({"status": "running"})
    # Even though the alert channel raises, the status write must complete.
    svc._write_status({"status": "failed", "reason": "boom"})
    written = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert written["status"] == "failed"
