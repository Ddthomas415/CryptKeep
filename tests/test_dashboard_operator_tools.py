from __future__ import annotations

from dashboard.services.operator_tools import parse_symbol_list, synthetic_ohlcv


def test_parse_symbol_list_handles_commas_and_newlines() -> None:
    raw = "BTC/USD, ETH/USD\nSOL/USD , ,\n"
    out = parse_symbol_list(raw)
    assert out == ["BTC/USD", "ETH/USD", "SOL/USD"]


def test_parse_symbol_list_returns_empty_for_blank_input() -> None:
    assert parse_symbol_list("") == []
    assert parse_symbol_list(" , \n  ") == []


def test_synthetic_ohlcv_produces_expected_shape() -> None:
    rows = synthetic_ohlcv(12, start_px=100.0)
    # Minimum dataset length is intentionally enforced for strategy warmup safety.
    assert len(rows) >= 30
    for row in rows:
        assert len(row) == 6
        ts_ms, o, h, l, c, vol = row
        assert isinstance(ts_ms, float)
        assert isinstance(o, float)
        assert isinstance(h, float)
        assert isinstance(l, float)
        assert isinstance(c, float)
        assert isinstance(vol, float)
        assert h >= max(o, c)
        assert l <= min(o, c)
