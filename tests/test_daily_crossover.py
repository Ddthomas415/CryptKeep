import pytest

from services.strategies import es_daily_trend as es
from services.strategies.daily_crossover import DAY_MS, POLICY, completed_crossover
from services.strategies.strategy_registry import compute_signal


def bars(closes):
    return [[(i + 1) * DAY_MS, c, c + 1, c - 1, c, 10] for i, c in enumerate(closes)]


def test_each_close_uses_its_own_sma_and_equality_is_flat():
    rows = bars([10, 10, 10, 12])
    assert completed_crossover(rows, period=3, decision_time_ms=5 * DAY_MS)[1]
    assert not completed_crossover(bars([10, 11, 12, 13]), period=3, decision_time_ms=5 * DAY_MS)[1]


def test_forming_bar_cannot_create_entry():
    rows = bars([10, 10, 10, 10, 20])
    selected, cross = completed_crossover(rows, period=3, decision_time_ms=5 * DAY_MS + 100)
    assert len(selected) == 4 and not cross


@pytest.mark.parametrize("kind", ["gap", "duplicate", "stale", "future", "nan", "missing_time"])
def test_invalid_inputs_refused(kind):
    rows = bars([10, 10, 10, 12])
    now = 5 * DAY_MS
    if kind == "gap": rows.pop(1)
    if kind == "duplicate": rows.insert(1, rows[0])
    if kind == "stale": now += DAY_MS
    if kind == "future": rows.append([6 * DAY_MS, 12, 13, 11, 12, 10])
    if kind == "nan": rows[-1][4] = float("nan")
    if kind == "missing_time": now = None
    with pytest.raises(ValueError):
        completed_crossover(rows, period=3, decision_time_ms=now)


@pytest.mark.parametrize("allowed,expected", [(True, "buy"), (False, "hold")])
def test_registry_applies_regime_at_cross(monkeypatch, allowed, expected):
    monkeypatch.setattr(es, "regime_stability", lambda *a, **kw: {"entry_allowed": allowed, "regime": "test"})
    cfg = {"strategy": {"name": "sma_200_trend", "sma_period": 3,
           "entry_policy": POLICY, "decision_time_ms": 5 * DAY_MS, "emit_evidence": False}}
    result = compute_signal(cfg=cfg, symbol="BTC/USDT", ohlcv=bars([10, 10, 10, 12]))
    assert result["action"] == expected and result["entry_crossover"] is True
    cfg["strategy"]["decision_time_ms"] = 6 * DAY_MS
    # Regime recovery above the SMA is not a second crossing.
    result = compute_signal(cfg=cfg, symbol="BTC/USDT", ohlcv=bars([10, 10, 10, 12, 13]))
    assert result["action"] == "hold"


def test_unknown_policy_fails_closed():
    result = es.signal_from_ohlcv(bars([10]*4), sma_period=3, entry_policy="typo", emit_evidence=False)
    assert result["ok"] is False and result["action"] == "hold"
