from __future__ import annotations

import json
import time

from services.market_data import tick_reader
from services.risk import staleness_guard



def test_staleness_guard_accepts_valid_snapshot_json(monkeypatch, tmp_path):
    snap = tmp_path / "system_status.latest.json"
    snap.write_text(json.dumps({"ts_ms": int(time.time() * 1000)}), encoding="utf-8")
    monkeypatch.setattr(staleness_guard, "LATEST_SNAPSHOT", snap)

    fresh, reason = staleness_guard.is_snapshot_fresh(max_age_sec=5.0)

    assert fresh is True
    assert reason is None



def test_tick_reader_supports_venues_snapshot_shape(monkeypatch, tmp_path):
    snap = tmp_path / "system_status.latest.json"
    snap.write_text(
        json.dumps(
            {
                "ts_ms": 123456,
                "venues": {
                    "coinbase": {
                        "bid": 100.0,
                        "ask": 102.0,
                        "last": 101.0,
                        "timestamp": 123450,
                        "ok": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tick_reader, "LATEST", snap)

    out = tick_reader.get_best_bid_ask_last("coinbase", "BTC/USD")

    assert out == {"ts_ms": 123456, "bid": 100.0, "ask": 102.0, "last": 101.0}
    assert tick_reader.mid_price(out) == 101.0



def test_tick_reader_still_supports_ticks_snapshot_shape(monkeypatch, tmp_path):
    snap = tmp_path / "system_status.latest.json"
    snap.write_text(
        json.dumps(
            {
                "ticks": [
                    {"venue": "coinbase", "symbol": "BTC/USD", "bid": 99.0, "ask": 101.0, "last": 100.0, "ts_ms": 456}
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tick_reader, "LATEST", snap)

    out = tick_reader.get_best_bid_ask_last("coinbase", "BTC/USD")

    assert out == {"ts_ms": 456, "bid": 99.0, "ask": 101.0, "last": 100.0}
