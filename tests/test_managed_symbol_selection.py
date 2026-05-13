from __future__ import annotations

import json

from services.runtime import managed_symbol_selection as mss


def test_selection_uses_runtime_health_payload(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    health = runtime / "health"
    health.mkdir(parents=True, exist_ok=True)
    (health / "managed_symbol_selection.json").write_text(
        json.dumps({"ok": True, "selected": ["BILL/USD", "BILL/USDC"], "source": "coinbase_movers", "venue": "coinbase"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mss, "runtime_dir", lambda: runtime)

    out = mss.resolve_managed_symbol_selection(
        {
            "execution": {"symbols": ["BTC/USD"]},
            "pipeline": {"exchange_id": "coinbase"},
        },
        venue="coinbase",
        mode="paper",
        live_enabled=False,
    )

    assert out["source"] == "coinbase_movers"
    assert out["symbols"] == ["BILL/USD", "BILL/USDC"]
    assert out["reason"] == "scanner_selected"
    assert out["scan_ok"] is True


def test_selection_falls_back_on_venue_mismatch(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    health = runtime / "health"
    health.mkdir(parents=True, exist_ok=True)
    (health / "managed_symbol_selection.json").write_text(
        json.dumps({"ok": True, "selected": ["BILL/USD"], "source": "coinbase_movers", "venue": "coinbase"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mss, "runtime_dir", lambda: runtime)

    out = mss.resolve_managed_symbol_selection(
        {
            "execution": {"symbols": ["BTC/USD"]},
            "pipeline": {"exchange_id": "binance"},
        },
        venue="binance",
        mode="paper",
        live_enabled=False,
    )

    assert out["symbols"] == ["BTC/USD"]
    assert out["reason"] == "scanner_venue_mismatch"
