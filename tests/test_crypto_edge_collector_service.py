from __future__ import annotations

import json

from services.analytics import crypto_edge_collector_service as svc


def test_collect_once_writes_live_public_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"funding": [], "basis": [], "quotes": []}), encoding="utf-8")
    monkeypatch.setattr(
        svc,
        "collect_live_crypto_edge_snapshot",
        lambda plan: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "funding_rows": [{"symbol": "BTC/USDT:USDT", "venue": "binance", "funding_rate": 0.0002, "interval_hours": 8.0}],
            "basis_rows": [{"symbol": "BTC/USDT:USDT", "venue": "binance", "spot_px": 84000.0, "perp_px": 84020.0, "days_to_expiry": 7}],
            "quote_rows": [{"symbol": "BTC/USD", "venue": "coinbase", "bid": 84010.0, "ask": 84015.0}],
            "checks": [{"kind": "quotes", "venue": "coinbase", "symbol": "BTC/USD", "ok": True}],
        },
    )

    out = svc.collect_once(
        svc.CryptoEdgeCollectorServiceCfg(plan_file=str(plan_path), db_path=str(tmp_path / "crypto_edges.sqlite"))
    )

    assert out["ok"] is True
    assert out["reason"] == "collected"
    assert out["source"] == "live_public"
    assert out["report"]["has_any_data"] is True


def test_run_forever_writes_status_and_stops_on_max_loops(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"funding": [], "basis": [], "quotes": []}), encoding="utf-8")
    monkeypatch.setattr(
        svc,
        "collect_once",
        lambda cfg: {
            "ok": True,
            "reason": "collected",
            "research_only": True,
            "execution_enabled": False,
            "source": "live_public",
        },
    )
    monkeypatch.setattr(svc.time, "sleep", lambda *_args, **_kwargs: None)

    out = svc.run_forever(
        svc.CryptoEdgeCollectorServiceCfg(plan_file=str(plan_path), poll_interval_sec=0.01),
        max_loops=1,
    )

    assert out["ok"] is True
    assert out["reason"] == "max_loops"
    assert out["writes"] == 1
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["status"] == "stopped"
    assert status["reason"] == "max_loops"


def test_run_forever_honors_stop_request(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"funding": [], "basis": [], "quotes": []}), encoding="utf-8")

    def _collect_once(cfg):
        svc.request_stop()
        return {
            "ok": True,
            "reason": "collected",
            "research_only": True,
            "execution_enabled": False,
            "source": "live_public",
        }

    monkeypatch.setattr(svc, "collect_once", _collect_once)
    monkeypatch.setattr(svc.time, "sleep", lambda *_args, **_kwargs: None)

    out = svc.run_forever(
        svc.CryptoEdgeCollectorServiceCfg(plan_file=str(plan_path), poll_interval_sec=0.01),
        max_loops=None,
    )

    assert out["ok"] is True
    assert out["reason"] == "stop_requested"
    assert out["writes"] == 1
