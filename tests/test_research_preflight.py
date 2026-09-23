import copy

import pytest

from services.backtest import walk_forward as wf
from services.backtest.research_preflight import check_research_inputs, resolve_research_config
from services.strategies import strategy_registry


def candles():
    return [[1700000100000 + i * 300000, 100., 101., 99., 100., 10.] for i in range(30)]


def check(rows, **kwargs):
    return check_research_inputs(rows, timeframe="5m", since_ms=None,
                                 initial_cash=10000, fee_bps=kwargs.get("fee", 10), slippage_bps=5)


def test_nested_parameters_reach_signal_function_without_mutation(monkeypatch):
    cfg = {"strategy": {"name": "breakout_donchian", "signal": {"donchian_len": 21},
                        "no_trade_filters": {"min_volatility_pct": 0.2,
                                             "require_directional_confirmation": True}}}
    before = copy.deepcopy(cfg)
    resolved = resolve_research_config(cfg)
    monkeypatch.setitem(strategy_registry.SUPPORTED, "breakout_donchian", lambda **kw: kw)
    out = strategy_registry.compute_signal(cfg=resolved, symbol="BTC/USDT", ohlcv=candles())
    assert out["donchian_len"] == 21
    assert out["min_volatility_pct"] == 0.2
    assert out["require_directional_confirmation"] is True
    assert cfg == before


def test_conflicting_flat_and_nested_refused():
    with pytest.raises(ValueError, match="conflicting_strategy_parameter"):
        resolve_research_config({"strategy": {"name": "breakout_donchian", "donchian_len": 10,
                                             "signal": {"donchian_len": 20}}})


@pytest.mark.parametrize("fee", [float("nan"), float("inf"), -1, 10000])
def test_invalid_costs_refused(fee):
    with pytest.raises(ValueError, match="invalid_research_cost"):
        check(candles(), fee=fee)


@pytest.mark.parametrize("kind", ["gap", "duplicate", "off_grid", "bad_price", "missing_volume"])
def test_bad_data_refused(kind):
    rows = candles()
    if kind == "gap":
        rows.pop(5)
    elif kind == "duplicate":
        rows[5] = rows[4]
    elif kind == "off_grid":
        rows[5][0] += 1
    elif kind == "bad_price":
        rows[5][2] = 90
    else:
        rows[5][5] = None
    with pytest.raises(ValueError):
        check(rows)


def test_gap_stops_before_simulator(monkeypatch):
    rows = candles()
    rows.pop(5)
    monkeypatch.setattr(wf, "load_archived_ohlcv", lambda *a, **kw: {
        "ok": True, "complete": True, "rows": rows})
    monkeypatch.setattr(wf, "run_anchored_walk_forward", lambda **kw: pytest.fail("simulation must not run"))
    out = wf.run_archive_backed_walk_forward(cfg={"strategy": {"name": "breakout_donchian"}},
        venue="coinbase", symbol="BTC/USDT", timeframe="5m", limit=len(rows))
    assert out["ok"] is False
    assert out["reason"] == "archive_not_contiguous"
    assert out["window_count"] == 0


def test_valid_data_declares_costs():
    out = check(candles())
    assert out["status"] == "passed"
    assert out["cost_assumptions"]["fee_bps"] == 10


@pytest.mark.parametrize("strategy", [
    {"name": "typo"},
    {"name": "ema_cross", "ema_fsat": 99},
    {"name": "ema_cross", "trade_enabled": False},
    {"name": "ema_cross", "trade_enabled": "true"},
    {"name": "ema_cross", "signal": {"type": "rsi"}},
    {"name": "ema_cross", "signal": {"direction": "short_only"}},
    {"name": "ema_cross", "no_trade_filters": {"breakout_buffer_pct": .05}},
])
def test_ineffective_config_refused_before_simulation(monkeypatch, strategy):
    monkeypatch.setattr(wf, "load_archived_ohlcv", lambda *a, **kw: {
        "ok": True, "complete": True, "rows": candles()})
    monkeypatch.setattr(wf, "run_anchored_walk_forward", lambda **kw: pytest.fail("unexpected simulation"))
    out = wf.run_archive_backed_walk_forward(cfg={"strategy": strategy},
        venue="coinbase", symbol="BTC/USDT", timeframe="5m", limit=30)
    assert out["preflight"]["status"] == "failed"
    assert out["ok"] is False


@pytest.mark.parametrize("kind", ["duplicate", "fractional", "reversed", "invalid_first"])
def test_raw_loader_values_not_sanitized_before_check(monkeypatch, kind):
    rows = candles()
    if kind == "duplicate":
        rows.insert(1, rows[0][:])
    elif kind == "fractional":
        rows[2][0] += .25
    elif kind == "reversed":
        rows.reverse()
    else:
        rows.insert(0, [])
    def loader(*args, **kwargs):
        assert kwargs["strict_raw"] is True
        return {"ok": True, "complete": True, "rows": rows}
    monkeypatch.setattr(wf, "load_archived_ohlcv", loader)
    monkeypatch.setattr(wf, "run_anchored_walk_forward", lambda **kw: pytest.fail("unexpected simulation"))
    out = wf.run_archive_backed_walk_forward(cfg={"strategy": {"name": "ema_cross"}},
        venue="coinbase", symbol="BTC/USDT", timeframe="5m", limit=len(rows))
    assert out["preflight"]["status"] == "failed"


def test_strict_loader_retains_fractional_timestamp_and_does_not_mutate(tmp_path):
    import sqlite3
    from services.backtest.ohlcv_archive import load_archived_ohlcv
    db = tmp_path / "archive.sqlite"
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE market_ohlcv(ts_ms, exchange, symbol, timeframe, o,h,l,cl,v)")
        con.execute("INSERT INTO market_ohlcv VALUES(?,?,?,?,?,?,?,?,?)",
                    (1700000100000.25, "coinbase", "BTC/USDT", "5m", 100., 101., 99., 100., 10.))
    before = db.read_bytes()
    loaded = load_archived_ohlcv("coinbase", "BTC/USDT", timeframe="5m", limit=1,
                                 db_path=db, strict_raw=True)
    assert loaded["rows"][0][0] == 1700000100000.25
    with pytest.raises(ValueError, match="archive_off_grid"):
        check(loaded["rows"])
    assert db.read_bytes() == before


def test_effective_config_and_costs_retained_in_success(monkeypatch):
    monkeypatch.setattr(wf, "load_archived_ohlcv", lambda *a, **kw: {
        "ok": True, "complete": True, "rows": candles()})
    def simulate(**kwargs):
        assert kwargs["cfg"]["strategy"]["ema_fast"] == 3
        return {"ok": True, "windows": []}
    monkeypatch.setattr(wf, "run_anchored_walk_forward", simulate)
    out = wf.run_archive_backed_walk_forward(cfg={"strategy": {"name": "ema_cross",
        "signal": {"ema_fast": 3, "ema_slow": 5}}}, venue="coinbase", symbol="BTC/USDT",
        timeframe="5m", limit=30, fee_bps=17, slippage_bps=9)
    assert out["resolved_config"]["strategy"]["ema_fast"] == 3
    assert out["config_hash"] != out["resolved_config_hash"]
    assert out["preflight"]["cost_assumptions"] == {"initial_cash": 10000., "fee_bps": 17, "slippage_bps": 9}
