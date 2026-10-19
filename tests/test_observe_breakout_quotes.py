import pytest
import json
from types import SimpleNamespace

from scripts.research import observe_breakout_quotes as experiment

from scripts.research.observe_breakout_quotes import closed_bars, label, quote, run


def test_fee_break_even_and_spread_not_double_counted():
    result = label({"bid": 99, "ask": 101}, {"bid": 102, "ask": 104})
    assert result["gross_mid_bps"] == pytest.approx(300)
    assert result["quote_cross_return_bps"] == pytest.approx(10000/101)
    assert result["break_even_equal_fee_bps_per_side"] == pytest.approx(10000/203)


def test_closed_bars_excludes_incomplete_and_rejects_gaps():
    raw = [[i*300, 99, 102, 100, 101, 5] for i in range(42)]
    assert len(closed_bars(raw, 41*300+2)) == 41
    with pytest.raises(ValueError, match="bar_gap"):
        closed_bars(raw[:20]+raw[21:], 41*300+2)


def test_bad_quote_and_unbounded_duration_rejected(tmp_path):
    with pytest.raises(ValueError):
        quote({"payload": {"bid": 2, "ask": 1}})
    with pytest.raises(ValueError):
        run(tmp_path/"run", 3601)
    assert not (tmp_path/"run").exists()


@pytest.mark.parametrize("broken", [False, True])
def test_bounded_run_has_no_orders_and_records_censoring(monkeypatch, tmp_path, broken):
    clock = [12302.0]
    monkeypatch.setattr(experiment, "time", SimpleNamespace(
        time=lambda: clock[0], time_ns=lambda: int(clock[0]*1e9),
        monotonic=lambda: clock[0], monotonic_ns=lambda: int(clock[0]*1e9),
        sleep=lambda seconds: clock.__setitem__(0, clock[0]+seconds)))
    requests = []
    def fetch(endpoint):
        requests.append(endpoint)
        if broken:
            raise OSError("injected unavailable")
        payload = ([[i*300, 99, 102, 100, 101, 5] for i in range(42)]
                   if "candles" in endpoint else {"bid": 100, "ask": 101})
        return {"payload": payload, "received_ns": int(clock[0]*1e9),
                "mono_ns": int(clock[0]*1e9)}
    monkeypatch.setattr(experiment, "fetch", fetch)
    monkeypatch.setattr(experiment, "compute_signal", lambda **kwargs: {"ok": True, "action": "buy"})
    experiment.run(tmp_path/"run", 60)
    result = json.loads((tmp_path/"run"/"result.json").read_text())
    assert result["profitability"] == "NOT_EVALUATED"
    assert all(r in ("/ticker", "/candles?granularity=300") for r in requests)
    if broken:
        assert result["status"] == "data_blocked"
        assert len(requests) == 3
    else:
        assert len(result["signals"]) == 1
        assert len(result["labels"]) == 1
        assert result["pending_labels"] == 1
        assert clock[0] == 12362
