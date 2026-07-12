from __future__ import annotations

import pytest

import services.execution.ohlcv_preflight as preflight
from services.execution import strategy_runner


class _FakeExchange:
    def __init__(self, *, rows=None, error: Exception | None = None):
        self.rows = rows or []
        self.error = error
        self.calls: list[tuple[str, str | None, int | None]] = []
        self.closed = False

    def fetch_ohlcv(self, symbol, timeframe=None, limit=None):
        self.calls.append((symbol, timeframe, limit))
        if self.error:
            raise self.error
        return self.rows

    def close(self):
        self.closed = True


class _SequenceFactory:
    def __init__(self, exchanges):
        self.exchanges = list(exchanges)
        self.created = []

    def __call__(self, *args, **kwargs):
        ex = self.exchanges.pop(0)
        self.created.append(ex)
        return ex


def _rows(count: int) -> list[list[float]]:
    return [[1_700_000_000_000 + idx * 60_000, 100, 101, 99, 100.5, 10] for idx in range(count)]


def _patch_fetch_path(monkeypatch: pytest.MonkeyPatch, exchange: _FakeExchange) -> None:
    import services.market_data.symbol_router as symbol_router
    import services.security.exchange_factory as exchange_factory

    monkeypatch.setattr(exchange_factory, "make_exchange", lambda *args, **kwargs: exchange)
    monkeypatch.setattr(symbol_router, "normalize_symbol", lambda symbol: str(symbol).upper())
    monkeypatch.setattr(symbol_router, "map_symbol", lambda venue, symbol: f"{venue}:{symbol}")


def test_reachable_source_with_rows_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = _FakeExchange(rows=_rows(5))
    _patch_fetch_path(monkeypatch, exchange)

    result = preflight.check_ohlcv_reachable(
        venue="okx",
        symbol="btc/usdt",
        signal_source="public_ohlcv_1h",
    )

    assert result["ok"] is True
    assert result["status"] == "ok"
    assert result["timeframe"] == "1h"
    assert result["row_count"] == 5
    assert exchange.calls == [("okx:BTC/USDT", "1h", 5)]
    assert exchange.closed is True


def test_unreachable_source_is_flagged_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = _FakeExchange(error=ConnectionError("dns failure"))
    _patch_fetch_path(monkeypatch, exchange)

    result = preflight.check_ohlcv_reachable(
        venue="coinbase",
        symbol="BTC/USD",
        signal_source="public_ohlcv_5m",
    )

    assert result["ok"] is False
    assert result["status"] == "ohlcv_source_unreachable"
    assert "ConnectionError" in str(result["error"])
    assert exchange.closed is True


def test_transient_unreachable_source_retries_then_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    import services.market_data.symbol_router as symbol_router
    import services.security.exchange_factory as exchange_factory

    first = _FakeExchange(error=ConnectionError("dns failure"))
    second = _FakeExchange(rows=_rows(2))
    factory = _SequenceFactory([first, second])
    monkeypatch.setattr(exchange_factory, "make_exchange", factory)
    monkeypatch.setattr(symbol_router, "normalize_symbol", lambda symbol: str(symbol).upper())
    monkeypatch.setattr(symbol_router, "map_symbol", lambda venue, symbol: f"{venue}:{symbol}")

    result = preflight.check_ohlcv_reachable(
        venue="okx",
        symbol="BTC/USDT",
        signal_source="public_ohlcv_5m",
        attempts=2,
    )

    assert result["ok"] is True
    assert result["attempts_used"] == 2
    assert result["errors"] == ["ConnectionError: dns failure"]
    assert first.closed is True
    assert second.closed is True


def test_reachable_but_empty_is_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = _FakeExchange(rows=[])
    _patch_fetch_path(monkeypatch, exchange)

    result = preflight.check_ohlcv_reachable(
        venue="okx",
        symbol="BTC/USDT",
        signal_source="public_ohlcv_1h",
    )

    assert result["ok"] is False
    assert result["status"] == "ohlcv_source_empty"


def test_unknown_venue_is_config_problem(monkeypatch: pytest.MonkeyPatch) -> None:
    import services.security.exchange_factory as exchange_factory

    monkeypatch.setattr(exchange_factory, "make_exchange", lambda *args, **kwargs: (_ for _ in ()).throw(AttributeError("bad venue")))

    result = preflight.check_ohlcv_reachable(
        venue="bad_venue",
        symbol="BTC/USDT",
        signal_source="public_ohlcv_1h",
    )

    assert result["ok"] is False
    assert result["status"] == "invalid_preflight_config"
    assert result["reason"] == "unknown venue"


def test_non_public_source_is_config_problem() -> None:
    result = preflight.check_ohlcv_reachable(
        venue="okx",
        symbol="BTC/USDT",
        signal_source="crypto_edge_funding",
    )

    assert result["ok"] is False
    assert result["status"] == "not_public_ohlcv_source"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"venue": "", "symbol": "BTC/USDT", "signal_source": "public_ohlcv_1h"}, "missing venue"),
        ({"venue": "okx", "symbol": "", "signal_source": "public_ohlcv_1h"}, "missing symbol"),
        ({"venue": "okx", "symbol": "BTC/USDT", "signal_source": "public_ohlcv_1h", "probe_limit": 0}, "probe_limit must be positive"),
    ],
)
def test_invalid_config_is_exit_one_classification(kwargs: dict, reason: str) -> None:
    result = preflight.check_ohlcv_reachable(**kwargs)

    assert result["ok"] is False
    assert result["status"] == "invalid_preflight_config"
    assert result["reason"] == reason


def test_config_wrapper_reads_runner_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = _FakeExchange(rows=_rows(3))
    _patch_fetch_path(monkeypatch, exchange)
    cfg = {"venue": "okx", "symbol": "ETH/USDT", "signal_source": "public_ohlcv_4h"}

    result = preflight.check_config_ohlcv_reachable(cfg)

    assert result["ok"] is True
    assert result["timeframe"] == "4h"
    assert result["symbol"] == "ETH/USDT"


@pytest.mark.parametrize("source", ["public_ohlcv_5m", "public_ohlcv_1d", "", "crypto_edge_funding"])
def test_timeframe_parser_matches_strategy_runner(source: str) -> None:
    assert preflight._timeframe_from_source(source) == strategy_runner._public_ohlcv_timeframe({"signal_source": source})


def test_probe_persists_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = _FakeExchange(rows=_rows(5))
    _patch_fetch_path(monkeypatch, exchange)
    calls = []
    monkeypatch.setattr(strategy_runner, "_persist_public_ohlcv_snapshot", lambda *args, **kwargs: calls.append((args, kwargs)))

    result = preflight.check_ohlcv_reachable(
        venue="okx",
        symbol="BTC/USDT",
        signal_source="public_ohlcv_1h",
    )

    assert result["ok"] is True
    assert calls == []


def test_cli_exit_code_policy(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts import check_ohlcv_preflight

    monkeypatch.setattr(
        check_ohlcv_preflight,
        "check_ohlcv_reachable",
        lambda **kwargs: {
            "ok": False,
            "status": "ohlcv_source_unreachable",
            "reason": "public ohlcv fetch failed",
            "venue": kwargs["venue"],
            "symbol": kwargs["symbol"],
            "timeframe": "5m",
            "row_count": 0,
            "error": "ConnectionError: dns failure",
        },
    )

    code = check_ohlcv_preflight.main(["--venue", "coinbase", "--symbol", "BTC/USD", "--signal-source", "public_ohlcv_5m"])

    assert code == 2
    assert "OHLCV preflight OHLCV_SOURCE_UNREACHABLE" in capsys.readouterr().out
