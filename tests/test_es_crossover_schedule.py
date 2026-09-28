from scripts.research.es_crossover_schedule import schedule
from services.strategies import es_daily_trend as es
from services.strategies.daily_crossover import DAY_MS


def test_schedule_does_not_read_execution_bar_prices(monkeypatch):
    monkeypatch.setattr(es, "regime_stability", lambda *a, **kw: {"entry_allowed": True, "regime": "test"})
    rows = [[(i+1)*DAY_MS,c,c+1,c-1,c,10] for i,c in enumerate([10,10,10,12,13])]
    result = schedule(rows, sma_period=3)
    assert result[0]["signal"]["action"] == "buy"
    rows[-1][1:] = [1000, 2000, 1, 500, 0]
    assert schedule(rows, sma_period=3) == result
