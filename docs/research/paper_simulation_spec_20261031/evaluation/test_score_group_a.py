"""Tests for score_group_a.py (spec v2 7.2-7.4). Run: python3 -m pytest -q test_score_group_a.py"""
import csv
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_group_a as S  # noqa: E402

START = "2026-11-16T00:00:00Z"


def ts(hours: float) -> str:
    base = S.parse_ts(START)
    return (base + S.dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def hourly_rows(acc, n_hours, price=100.0, spread=2.0):
    return [{"account_id": acc, "ts_utc": ts(h), "mid": price, "bid": price - spread / 2, "ask": price + spread / 2}
            for h in range(n_hours)]


def fill(acc, strategy, coin, hours, side, qty, mid, bid, ask, rule=""):
    return {"account_id": acc, "strategy": strategy, "coin": coin, "ts_utc": ts(hours), "side": side, "qty": qty,
            "mid": mid, "bid": bid, "ask": ask, "fee_rate": 0.005, "exit_rule": rule}


def test_round_trip_both_bases():
    f = [fill("a", "breakout_default", "BTC", 1.5, "buy", 0.01, 100, 99, 101),
         fill("a", "breakout_default", "BTC", 2.5, "sell", 0.01, 110, 109, 111, "take_profit")]
    h = hourly_rows("a", 5)
    start, end = S.parse_ts(START), S.parse_ts(ts(5))
    ba = S.account_result(f, h, "bidask", start, end, 1000.0)
    mid = S.account_result(f, h, "mid", start, end, 1000.0)
    exp_ba = (0.01 * 109 * 0.995 - 0.01 * 101 * 1.005) / (0.01 * 101 * 1.005)
    exp_mid = (0.01 * 110 * 0.995 - 0.01 * 100 * 1.005) / (0.01 * 100 * 1.005)
    assert abs(ba["trades"][0]["ret"] - exp_ba) < 1e-12
    assert abs(mid["trades"][0]["ret"] - exp_mid) < 1e-12
    assert ba["closed_trades"] == 1 and not ba["open_at_end"]
    assert abs(ba["fees"] - (0.01 * 101 * 0.005 + 0.01 * 109 * 0.005)) < 1e-12
    assert ba["entry_minute_of_hour"]["30-44"] == 1


def test_open_position_valued_as_sold_at_bid():
    f = [fill("a", "breakout_default", "BTC", 0.5, "buy", 1.0, 100, 99, 101)]
    h = hourly_rows("a", 3)
    r = S.account_result(f, h, "bidask", S.parse_ts(START), S.parse_ts(ts(3)), 1000.0)
    cash = 1000 - 101 * 1.005
    assert abs(r["pnl"] - (cash + 99 * 0.995 - 1000)) < 1e-9 and r["open_at_end"] and r["closed_trades"] == 0


def test_sell_larger_than_holding_is_an_error():
    f = [fill("a", "breakout_default", "BTC", 0.5, "buy", 1.0, 100, 99, 101),
         fill("a", "breakout_default", "BTC", 1.5, "sell", 2.0, 100, 99, 101)]
    try:
        S.account_result(f, hourly_rows("a", 3), "bidask", S.parse_ts(START), S.parse_ts(ts(3)), 1000.0)
    except ValueError as e:
        assert "larger than holding" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_bootstrap_is_deterministic_and_detects_a_clear_edge():
    trades = [{"exit_ts": ts(24 * 7 * w + i), "ret": 0.02 + 0.001 * (i % 3)} for w in range(26) for i in range(3)]
    a = S.bootstrap_p(trades, S.parse_ts(START), 26, 2000, 7)
    b = S.bootstrap_p(trades, S.parse_ts(START), 26, 2000, 7)
    assert a == b and a["p_one_sided"] < 0.01
    flat = [{"exit_ts": t["exit_ts"], "ret": (0.01 if k % 2 else -0.01)} for k, t in enumerate(trades)]
    assert S.bootstrap_p(flat, S.parse_ts(START), 26, 2000, 7)["p_one_sided"] > 0.2


RULES = {"minimum_closed_trades": {"breakout_default": 42, "ema_cross_default": 42, "mean_reversion_default": 31},
         "alpha_per_strategy": 0.05 / 3}


def accs(valid=True, breach=False):
    return [{"account_id": f"x{i}", "valid": valid, "drawdown_breach": breach and i == 0} for i in range(3)]


def test_classification_rules():
    c = S.classify
    assert c("breakout_default", accs(valid=False), RULES, 26, 0.001, 0.2, 100)[0] == "Inconclusive"
    assert c("breakout_default", accs(breach=True), RULES, 26, 0.001, 0.2, 5)[0] == "Fail"
    assert c("breakout_default", accs(), RULES, 26, 0.5, -0.1, 41)[0] == "Extend to week 52"
    assert c("breakout_default", accs(), RULES, 52, 0.5, -0.1, 41)[0] == "Inconclusive"
    assert c("mean_reversion_default", accs(), RULES, 26, 0.5, -0.1, 31)[0] == "Fail"
    assert c("ema_cross_default", accs(), RULES, 26, 0.03, 0.05, 50)[0] == "Promising but unproven"
    assert c("ema_cross_default", accs(), RULES, 26, 0.01, 0.05, 50)[0] == "Pass"


def test_drawdown_rules():
    assert S.drawdown_breach({"type": "hold"}, 0.41, 0.40) and not S.drawdown_breach({"type": "hold"}, 0.39, 0.40)
    assert S.drawdown_breach({"type": "fixed", "max_drawdown": 0.2}, 0.21, 0.9)
    assert S.drawdown_breach({"type": "both", "max_drawdown": 0.5}, 0.45, 0.40)


def _write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_end_to_end_and_week52_judges_only_extended(tmp_path):
    fills, hourly, validity = [], [], {}
    end_h = 24 * 7 * 26
    for strategy, n in (("breakout_default", 60), ("ema_cross_default", 10), ("mean_reversion_default", 40)):
        for coin in ("BTC", "ETH", "SOL"):
            acc = f"{strategy}:{coin}"
            validity[acc] = {"strategy": strategy, "coin": coin, "valid": True, "reasons": []}
            hourly += hourly_rows(acc, end_h + 1, 100.0, 0.02)
            for k in range(n // 3 + (1 if strategy == "breakout_default" else 0)):
                h0 = 10 + k * (end_h // (n // 3 + 2))
                fills.append(fill(acc, strategy, coin, h0, "buy", 1.0, 100, 99.99, 100.01))
                fills.append(fill(acc, strategy, coin, h0 + 3, "sell", 1.0, 100, 99.99, 100.01, "signal"))
    _write_csv(tmp_path / "f.csv", fills)
    _write_csv(tmp_path / "h.csv", hourly)
    (tmp_path / "v.json").write_text(json.dumps(validity))
    rules = dict(RULES, starting_cash=1000, fee_rate_per_side=0.005, bootstrap_resamples=500, seed=1,
                 drawdown_rule={"type": "fixed", "max_drawdown": 0.99})
    (tmp_path / "r.json").write_text(json.dumps(rules))
    args = types.SimpleNamespace(fills=str(tmp_path / "f.csv"), hourly=str(tmp_path / "h.csv"),
                                 validity=str(tmp_path / "v.json"), rules=str(tmp_path / "r.json"), start=START,
                                 end=ts(end_h + 1), stage=26, week26=None, out=str(tmp_path / "o.json"))
    rep = S.run(args)
    assert rep["strategies"]["breakout_default"]["classification"] == "Fail"  # flat prices, fees only: loses
    assert rep["strategies"]["ema_cross_default"]["classification"] == "Extend to week 52"  # 9 trades < 42
    assert rep["strategies"]["mean_reversion_default"]["classification"] == "Fail"  # 39 trades >= 31, loses
    (tmp_path / "w26.json").write_text(json.dumps(rep, default=str))
    args.stage, args.week26 = 52, str(tmp_path / "w26.json")
    rep52 = S.run(args)
    assert rep52["strategies"]["breakout_default"]["reason"] == "judged at week 26; not judged again"
    assert rep52["strategies"]["ema_cross_default"]["classification"] == "Inconclusive"
