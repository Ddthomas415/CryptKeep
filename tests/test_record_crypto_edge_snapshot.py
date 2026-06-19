from __future__ import annotations

import json

from scripts import record_crypto_edge_snapshot as script


def test_record_crypto_edge_snapshot_writes_rows_and_report(tmp_path, monkeypatch, capsys) -> None:
    funding_path = tmp_path / "funding.json"
    open_interest_path = tmp_path / "open_interest.json"
    basis_path = tmp_path / "basis.json"
    quotes_path = tmp_path / "quotes.json"
    order_books_path = tmp_path / "order_books.json"
    funding_path.write_text(json.dumps([{"symbol": "BTC-PERP", "venue": "binance", "funding_rate": 0.0002}]), encoding="utf-8")
    open_interest_path.write_text(
        json.dumps([{"symbol": "BTC/USDT:USDT", "venue": "binance", "open_interest": 123456.0}]),
        encoding="utf-8",
    )
    basis_path.write_text(
        json.dumps([{"symbol": "BTC-PERP", "venue": "binance", "spot_px": 84000.0, "perp_px": 84030.0, "days_to_expiry": 7}]),
        encoding="utf-8",
    )
    order_books_path.write_text(
        json.dumps(
            [
                {
                    "symbol": "BTC/USD",
                    "venue": "coinbase",
                    "depth": 5,
                    "best_bid": 84010.0,
                    "best_ask": 84015.0,
                    "spread_bps": 0.5952,
                    "bid_notional": 420050.0,
                    "ask_notional": 420075.0,
                    "imbalance": -0.00003,
                }
            ]
        ),
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
            "--open-interest-file",
            str(open_interest_path),
            "--basis-file",
            str(basis_path),
            "--quotes-file",
            str(quotes_path),
            "--order-books-file",
            str(order_books_path),
            "--print-report",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["funding_count"] == 1
    assert out["open_interest_count"] == 1
    assert out["basis_count"] == 1
    assert out["quote_count"] == 2
    assert out["order_book_count"] == 1
    assert out["report"]["has_any_data"] is True


def test_record_crypto_edge_snapshot_rejects_empty_invocation(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["record_crypto_edge_snapshot.py"])

    assert script.main() == 1
    out = json.loads(capsys.readouterr().out)
    assert out == {"ok": False, "reason": "no_rows_supplied"}
