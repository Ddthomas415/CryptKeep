from __future__ import annotations

import asyncio

from services.admin import preflight as ap



def test_run_preflight_accepts_extended_signature_without_private_checks(monkeypatch):
    monkeypatch.setattr(ap, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(ap, "kill_state", lambda: {"armed": True, "note": "default"})

    out = asyncio.run(
        ap.run_preflight(
            venues=["Coinbase"],
            symbols=["ETH/USD"],
            time_tolerance_ms=999,
            do_private_check=False,
        )
    )

    assert out["ok"] is True
    assert out["venues"] == ["coinbase"]
    assert out["symbols"] == ["ETH/USD"]
    assert out["time_tolerance_ms"] == 999
    assert out["private_checks_enabled"] is False
    assert out["private_connectivity"] == []
    assert out["permission_probes"] == []
    assert out["probe_keys"] == list(ap.DEFAULT_PROBES)



def test_run_preflight_collects_private_connectivity_and_probe_results(monkeypatch):
    monkeypatch.setattr(ap, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(ap, "kill_state", lambda: {"armed": True, "note": "default"})
    monkeypatch.setattr(ap, "test_private_connectivity", lambda exchange: {"ok": exchange == "coinbase", "exchange": exchange})
    monkeypatch.setattr(ap, "run_probes", lambda exchange, probe_keys: {"ok": True, "exchange": exchange, "results": [{"probe": p} for p in probe_keys]})

    out = asyncio.run(
        ap.run_preflight(
            venues=["coinbase", "gateio"],
            symbols=["BTC/USD"],
            do_private_check=True,
            probe_keys=["fetch_balance"],
        )
    )

    assert out["ok"] is False
    assert [row["exchange"] for row in out["private_connectivity"]] == ["coinbase", "gateio"]
    assert out["private_connectivity"][0]["ok"] is True
    assert out["private_connectivity"][1]["ok"] is False
    assert out["permission_probes"][0]["results"] == [{"probe": "fetch_balance"}]
