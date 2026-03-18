from __future__ import annotations

import json
from pathlib import Path

from scripts import record_crypto_edge_snapshot as script


def test_record_crypto_edge_snapshot_writes_rows_and_report(tmp_path, monkeypatch, capsys) -> None:
    funding_path = tmp_path / "funding.json"
    basis_path = tmp_path / "basis.json"
    quotes_path = tmp_path / "quotes.json"
    funding_path.write_text(json.dumps([{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0002}]), encoding="utf-8")
    basis_path.write_text(
        json.dumps([{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84030.0, "days_to_expiry": 7}]),
        encoding="utf-8",
    )
    quotes_path.write_text(
        json.dumps(
            [
                {"symbol": "BTC/USD", "venue": "coinbase", "bid": 84010.0, "ask": 84015.0},
                {"symbol": "BTC/USD", "venue": "kraken", "bid": 84020.0, "ask": 84005.0},
            ]
        ),
        encoding="utf-8",
    )

    db_path = tmp_path / "edges.sqlite"
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "record_crypto_edge_snapshot.py",
            "--db-path",
            str(db_path),
            "--source",
            "test",
            "--funding-file",
            str(funding_path),
            "--basis-file",
            str(basis_path),
            "--quotes-file",
            str(quotes_path),
            "--print-report",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["funding_count"] == 1
    assert out["basis_count"] == 1
    assert out["quote_count"] == 2
    assert out["report"]["has_any_data"] is True


def test_record_crypto_edge_snapshot_rejects_empty_invocation(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["record_crypto_edge_snapshot.py"])

    assert script.main() == 1
    out = json.loads(capsys.readouterr().out)
    assert out == {"ok": False, "reason": "no_rows_supplied"}
