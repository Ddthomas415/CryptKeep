from __future__ import annotations

import json

from scripts.research import run_ohlcv_archive_backfill as runner


def test_fetch_public_ohlcv_uses_exchange_factory_and_closes(monkeypatch):
    seen: dict[str, object] = {}

    class FakeExchange:
        def fetch_ohlcv(self, symbol, **kwargs):
            seen["symbol"] = symbol
            seen["kwargs"] = dict(kwargs)
            return [[1_700_000_000_000, 1, 2, 0.5, 1.5, 10]]

        def close(self):
            seen["closed"] = True

    monkeypatch.setattr(runner, "make_exchange", lambda venue, creds, enable_rate_limit=True: FakeExchange())

    rows = runner.fetch_public_ohlcv("okx", "BTC/USDT", timeframe="5m", limit=10, since_ms=123)

    assert rows == [[1_700_000_000_000, 1, 2, 0.5, 1.5, 10]]
    assert seen["symbol"] == "BTC/USDT"
    assert seen["kwargs"] == {"timeframe": "5m", "limit": 10, "since": 123}
    assert seen["closed"] is True


def test_ohlcv_archive_backfill_cli_writes_json_artifact(monkeypatch, tmp_path, capsys):
    calls: list[dict[str, object]] = []

    def _fake_backfill(fetcher, **kwargs):
        calls.append({"fetcher": fetcher, **kwargs})
        return {
            "ok": True,
            "archive_path": str(tmp_path / "market_raw.sqlite"),
            "exchange": kwargs["venue"],
            "stored_symbol": "BTC/USDT",
            "symbol": "BTC/USDT",
            "timeframe": kwargs["timeframe"],
            "rows_written": 3,
            "dataset_hash": "hash123",
        }

    monkeypatch.setattr(runner, "backfill_archive", _fake_backfill)
    out_path = tmp_path / "backfill.json"

    rc = runner.main(
        [
            "--venue",
            "okx",
            "--symbol",
            "BTC/USDT",
            "--timeframe",
            "5m",
            "--since",
            "2026-07-20T00:00:00Z",
            "--until",
            "2026-07-20T01:00:00Z",
            "--archive-db",
            str(tmp_path / "market_raw.sqlite"),
            "--page-limit",
            "2",
            "--max-pages",
            "3",
            "--max-bars",
            "4",
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload == printed
    assert payload["artifact_type"] == "ohlcv_archive_backfill_v1"
    assert payload["research_data_ingestion"] is True
    assert payload["rows_written"] == 3
    assert payload["limitations"] == [
        "market_data_archive_only",
        "not_strategy_evidence",
        "not_promotion_evidence",
        "not_trading",
    ]
    assert calls[0]["fetcher"] is runner.fetch_public_ohlcv
    assert calls[0]["venue"] == "okx"
    assert calls[0]["symbol"] == "BTC/USDT"
    assert calls[0]["timeframe"] == "5m"
    assert calls[0]["page_limit"] == 2
    assert calls[0]["max_pages"] == 3
    assert calls[0]["max_bars"] == 4


def test_ohlcv_archive_backfill_cli_returns_2_when_requested_and_not_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(
        runner,
        "backfill_archive",
        lambda fetcher, **kwargs: {
            "ok": False,
            "archive_path": str(tmp_path / "market_raw.sqlite"),
            "rows_written": 0,
            "dataset_hash": "empty",
        },
    )

    rc = runner.main(["--since", "2026-07-20", "--fail-if-not-ok"])

    assert rc == 2
