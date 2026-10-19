"""Tests for tracker v2. Offline: uses the hash-checked majors daily files ([time, open, high, low, close, volume])."""
import copy, fcntl, json, sys
from pathlib import Path
import pytest
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
import tracker as T

def majors():
    out = {}
    for a in ("BTC", "ETH"):
        rows = json.load(open(ROOT / f"docs/research/majors_trend_20261009/{a}-USD_d1.json"))
        out[a] = {int(r[0]) // T.D: (float(r[1]), float(r[4])) for r in rows}
    return out
C = majors()
def run(state, start, last, candles=None, now=1.8e9):
    return T.main(["--state", str(state), "--start", start, "--last-day", last], candles=candles if candles is not None else C, now=now)
def lines(state, name):
    p = Path(state) / f"{name}.jsonl"; return p.read_text().splitlines() if p.exists() else []

def test_rule_constants_are_the_registered_ones():
    assert (T.L, T.VT, T.FEE, T.SLIP, T.ASSETS) == (28, 0.5, 0.005, 0.0005, ("BTC", "ETH"))

def test_parity_with_reviewed_harness_on_sunday_start(tmp_path):
    import datetime as dt
    from scripts.research.rerun_frozen_stress import load_frozen, run as hrun
    S = tmp_path / "s"; (S / "maj").mkdir(parents=True)
    for a in ("BTC", "ETH"):
        (S / "maj" / f"{a}-USD_d1.json").write_bytes((ROOT / f"docs/research/majors_trend_20261009/{a}-USD_d1.json").read_bytes())
    ns = load_frozen(S); days = ns["days"]
    lo = next(i for i, d in enumerate(days) if d >= 1578182400)          # 2020-01-05, a Sunday
    assert dt.datetime.fromtimestamp(days[lo], dt.timezone.utc).weekday() == 6
    hi = len(days) - 1
    start, last = T.iso(days[lo] // T.D), T.iso(days[hi] // T.D)
    recs = T.replay(C, days[lo] // T.D, days[hi] // T.D)
    for acct, kind, kw in (("rule", "rule", {}), ("hold_btc", "hold_btc", {}), ("mix_25_25_50", "fixed_mix", {"expo": 0.5})):
        curve, _ = hrun(ns, kind, lo, hi, fee=T.FEE, slip=T.SLIP, **kw)
        mine = [r["nav_usd"] for r in recs if r["ledger"] == "marks" and r["account"] == acct]
        assert len(mine) == len(curve) - 1
        assert max(abs(x - y) for x, y in zip(mine, curve[1:])) < 1e-5, acct

def test_rerun_is_idempotent(tmp_path):
    run(tmp_path, "2026-08-02", "2026-10-01"); before = {n: lines(tmp_path, n) for n in T.LEDGERS}
    run(tmp_path, "2026-08-02", "2026-10-01", now=1.9e9)
    assert {n: lines(tmp_path, n) for n in T.LEDGERS} == before

def test_incremental_runs_equal_single_run_and_never_rewrite(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    run(a, "2026-08-02", "2026-09-10"); first = {n: lines(a, n) for n in T.LEDGERS}
    run(a, "2026-08-02", "2026-10-01")
    run(b, "2026-08-02", "2026-10-01")
    for n in T.LEDGERS:
        assert lines(a, n)[:len(first[n])] == first[n]                     # earlier lines untouched
        strip = lambda ls: [{k: v for k, v in json.loads(x).items() if k != "recorded_utc"} for x in ls]
        assert strip(lines(a, n)) == strip(lines(b, n))                     # no duplicates, same history

def test_changed_history_halts_and_preserves(tmp_path):
    run(tmp_path, "2026-08-02", "2026-09-10"); before = {n: lines(tmp_path, n) for n in T.LEDGERS}
    bad = copy.deepcopy(C); d = min(k for k in bad["BTC"] if T.iso(k) == "2026-08-20"); bad["BTC"][d] = (bad["BTC"][d][0], bad["BTC"][d][1] * 1.01)
    with pytest.raises(T.Discrepancy): run(tmp_path, "2026-08-02", "2026-09-20", candles=bad)
    assert {n: lines(tmp_path, n) for n in T.LEDGERS} == before
    assert len(lines(tmp_path, "anomalies")) == 1

def test_missing_candle_writes_nothing(tmp_path):
    bad = copy.deepcopy(C); del bad["ETH"][min(k for k in bad["ETH"] if T.iso(k) == "2026-08-20")]
    with pytest.raises(T.DataGap): run(tmp_path, "2026-08-02", "2026-09-10", candles=bad)
    assert all(not lines(tmp_path, n) for n in T.LEDGERS)

def test_torn_line_refuses(tmp_path):
    run(tmp_path, "2026-08-02", "2026-09-10")
    with open(tmp_path / "marks.jsonl", "a") as f: f.write('{"ledger": "marks", "acc')
    with pytest.raises(T.Discrepancy): run(tmp_path, "2026-08-02", "2026-09-20")

def test_concurrent_run_refused(tmp_path):
    with open(tmp_path / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit): run(tmp_path, "2026-08-02", "2026-09-10")
    assert not lines(tmp_path, "marks")

def test_waits_before_first_sunday_and_initializes_in_cash(tmp_path):
    assert run(tmp_path, "2026-09-02", "2026-09-05") == 0 and not lines(tmp_path, "decisions")   # first Sunday is 09-06
    run(tmp_path, "2026-09-02", "2026-09-07")
    dec = [json.loads(x) for x in lines(tmp_path, "decisions")]
    assert {r["decision_day"] for r in dec} == {"2026-09-06"}
    ex = [json.loads(x) for x in lines(tmp_path, "executions")]
    assert {r["exec_day"] for r in ex} == {"2026-09-07"}


# ---- review round 3: write integrity, invalid prices, provenance labels ----
import math, os

def test_short_writes_are_completed(tmp_path, monkeypatch):
    real = os.write
    def short(fd, data): return real(fd, bytes(data[:7]))            # at most 7 bytes per call
    monkeypatch.setattr(T.os, "write", short)
    run(tmp_path, "2026-08-02", "2026-09-10")
    monkeypatch.setattr(T.os, "write", real)
    ref = tmp_path / "ref"; run(ref, "2026-08-02", "2026-09-10")
    strip = lambda ls: [{k: v for k, v in json.loads(x).items() if k not in T.META} for x in ls]
    for n in T.LEDGERS: assert strip(lines(tmp_path, n)) == strip(lines(ref, n))
    s = json.loads((tmp_path / "state.json").read_text())
    assert s["appended_this_run"] == sum(len(lines(tmp_path, n)) for n in T.LEDGERS)

def test_stalled_write_fails_loudly_and_next_run_refuses(tmp_path, monkeypatch):
    real = os.write; calls = {"n": 0}
    def stall(fd, data):
        calls["n"] += 1
        return real(fd, bytes(data[:50])) if calls["n"] == 1 else 0      # partial line, then no progress
    monkeypatch.setattr(T.os, "write", stall)
    with pytest.raises(T.WriteFailure): run(tmp_path, "2026-08-02", "2026-09-10")
    assert not (tmp_path / "state.json").exists()                       # no success summary
    monkeypatch.setattr(T.os, "write", real)
    with pytest.raises(T.Discrepancy): run(tmp_path, "2026-08-02", "2026-09-10")   # torn line -> refuse, operator inspects

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -1.0])
@pytest.mark.parametrize("field", [0, 1])                                # open, close
def test_invalid_price_writes_nothing(tmp_path, bad, field):
    c = copy.deepcopy(C); d = min(k for k in c["BTC"] if T.iso(k) == "2026-08-20")
    v = list(c["BTC"][d]); v[field] = bad; c["BTC"][d] = tuple(v)
    with pytest.raises(T.InvalidData): run(tmp_path, "2026-08-02", "2026-09-10", candles=c)
    assert all(not lines(tmp_path, n) for n in T.LEDGERS) and not (tmp_path / "state.json").exists()

def test_nonfinite_cannot_be_serialised():
    with pytest.raises(ValueError): json.dumps({"x": float("nan")}, allow_nan=False)
    src = (HERE / "tracker.py").read_text()
    assert src.count("allow_nan=False") >= 2                            # ledger lines and state.json

def test_provenance_labels(tmp_path):
    # last day 2026-09-10; "now" = 2026-09-11 00:47 UTC -> the 09-06 decision was recorded ~5 days late (reconstructed)
    now = 1789087620                                                    # 2026-09-11T00:47:00Z
    run(tmp_path, "2026-08-02", "2026-09-10", now=now)
    ex = [json.loads(x) for x in lines(tmp_path, "executions")]
    assert ex and all(r["observed_fill"] is False and r["execution_basis"].startswith("modelled") for r in ex)
    dec = {json.loads(x)["decision_day"]: json.loads(x) for x in lines(tmp_path, "decisions") if json.loads(x)["account"] == "rule"}
    assert dec["2026-09-06"]["reconstructed"] is True and dec["2026-09-06"]["recorded_lag_hours"] > 24
    marks = [json.loads(x) for x in lines(tmp_path, "marks") if json.loads(x)["day"] == "2026-09-10"]
    assert marks and all(m["reconstructed"] is False for m in marks)   # recorded 0.8 h after that day's close

def test_contemporaneous_monday_run_is_not_reconstructed(tmp_path):
    now = 1789087620 - 4 * 86400                                        # 2026-09-07T00:47Z, right after the 09-06 close
    run(tmp_path, "2026-09-02", "2026-09-06", now=now)
    dec = [json.loads(x) for x in lines(tmp_path, "decisions")]
    assert dec and all(r["reconstructed"] is False and r["recorded_lag_hours"] < 1 for r in dec)

def test_silently_lost_records_are_detected(tmp_path, monkeypatch):
    real = T.write_all
    def drop_tail(fd, data):                     # a writer that "succeeds" but persists only whole first lines
        keep = data[: data.rfind(b"\n", 0, len(data) // 2) + 1]
        real(fd, keep)
    monkeypatch.setattr(T, "write_all", drop_tail)
    with pytest.raises(T.WriteFailure): run(tmp_path, "2026-08-02", "2026-09-10")
    assert not (tmp_path / "state.json").exists()


# ---- rule_band10 (E9 forward tracking) ----
def test_band_constant_pinned():
    assert T.BAND == 0.10 and "rule_band10" in T.ACCOUNTS

def test_band_account_matches_e9_simulator(tmp_path):
    """rule_band10 marks must equal the E9 simulator (band.py) for the candidate with band 0.10 on a Sunday-start window."""
    import runpy, datetime as dt
    S = tmp_path / "s"; (S / "maj").mkdir(parents=True)
    for a in ("BTC", "ETH"):
        (S / "maj" / f"{a}-USD_d1.json").write_bytes((ROOT / f"docs/research/majors_trend_20261009/{a}-USD_d1.json").read_bytes())
    src = (ROOT / "docs/research/candidate_band_20261013/band.py").read_text()
    head = src[: src.index('out = {"artifact_type"')]
    g = {"__file__": str(ROOT / "docs/research/candidate_band_20261013/band.py"), "__name__": "band_head"}
    old = sys.argv; sys.argv = ["band.py", str(S)]
    try: exec(compile(head, "band_head", "exec"), g)
    finally: sys.argv = old
    days = g["days"]
    lo = next(i for i, d in enumerate(days) if d >= 1578182400)          # Sunday 2020-01-05
    hi = len(days) - 1
    _, curve = g["sim"](g["t_candidate"], lo, hi, T.FEE, band=0.10)
    recs = T.replay(C, days[lo] // T.D, days[hi] // T.D)
    mine = [r["nav_usd"] for r in recs if r["ledger"] == "marks" and r["account"] == "rule_band10"]
    assert len(mine) == len(curve) - 1
    assert max(abs(x - y) for x, y in zip(mine, curve[1:])) < 1e-5
    ex = [r for r in recs if r["ledger"] == "executions" and r["account"] == "rule_band10"]
    assert ex and all("assets_traded" in r and r["band"] == 0.10 for r in ex)
    assert any(not r["assets_traded"] for r in ex)                         # band actually skips some weeks

def test_band_boundary_is_inclusive():
    prices = {"BTC": 100.0, "ETH": 10.0}
    # current: 0 BTC, 0 ETH, $1000 cash -> current weight 0
    c, u, moved = T.banded_rebalance(1000.0, {}, prices, {"BTC": 0.10})
    assert moved == ["BTC"] and u.get("BTC", 0) > 0                     # gap exactly 0.10 -> traded
    c, u, moved = T.banded_rebalance(1000.0, {}, prices, {"BTC": 0.0999})
    assert moved == [] and u == {} and c == 1000.0                       # gap 0.0999 -> skipped

def test_band_executions_drop_zero_units():
    recs = T.replay(C, 1578182400 // T.D, max(C["BTC"]) - 2)
    ex = [r for r in recs if r["ledger"] == "executions" and r["account"] == "rule_band10"]
    assert ex and all(q > 0 for r in ex for q in r["units_after"].values())
