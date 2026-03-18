from __future__ import annotations

import json

from scripts import collect_live_crypto_edge_snapshot as script


def test_collect_live_crypto_edge_snapshot_writes_live_rows(tmp_path, monkeypatch, capsys) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "funding": [{"venue": "binance", "symbol": "BTC/USDT:USDT", "interval_hours": 8.0}],
                "basis": [{"venue": "binance", "spot_symbol": "BTC/USDT", "perp_symbol": "BTC/USDT:USDT", "days_to_expiry": 7}],
                "quotes": [{"venue": "coinbase", "symbol": "BTC/USD"}],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        script,
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
    db_path = tmp_path / "crypto_edges.sqlite"
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "collect_live_crypto_edge_snapshot.py",
            "--plan-file",
            str(plan_path),
            "--db-path",
            str(db_path),
            "--print-report",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["research_only"] is True
    assert out["execution_enabled"] is False
    assert out["funding_count"] == 1
    assert out["basis_count"] == 1
    assert out["quote_count"] == 1
    assert out["report"]["has_any_data"] is True


def test_collect_live_crypto_edge_snapshot_rejects_empty_live_collection(tmp_path, monkeypatch, capsys) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"funding": [], "basis": [], "quotes": []}), encoding="utf-8")
    monkeypatch.setattr(
        script,
        "collect_live_crypto_edge_snapshot",
        lambda plan: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "funding_rows": [],
            "basis_rows": [],
            "quote_rows": [],
            "checks": [{"kind": "funding", "venue": "binance", "symbol": "BTC/USDT:USDT", "ok": False, "reason": "funding_unsupported"}],
        },
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "collect_live_crypto_edge_snapshot.py",
            "--plan-file",
            str(plan_path),
        ],
    )

    assert script.main() == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["reason"] == "no_live_rows_collected"
    assert out["research_only"] is True
