"""Research-only forward tracker v2 for the BTC+ETH 28-day trend rule. Places NO orders, reads no keys, touches no CryptKeep
config, state or account. It reads public Coinbase daily candles and appends records in its own --state directory.

Matches the reviewed corrected harness (scripts/research/rerun_frozen_stress.py):
  * target: per asset, if 28-day close return > 0: weight 0.5 * min(1, 0.50 / annualised 30-day vol), else 0 (rest cash)
  * decide at the close of each Sunday daily candle (UTC); execute at the NEXT day's open; mark at daily closes
  * accounting: scripts/research/corrected_research_math.rebalance, fee 0.50% + slippage 0.05% per side
  * benchmarks with identical timing and costs: hold_btc (bought once), mix_25_25_50 (25% BTC, 25% ETH, 50% cash, weekly), cash
  * rule_band10 (E9, forward-tracked): same decisions as rule; at the execution open an asset is traded only if
    |target - current weight| >= BAND (0.10), via banded_rebalance (identical to docs/research/candidate_band_20261013/band.py)
Initialization (differs from the harness, which also decides on a period's first day whatever the weekday): every account holds
$1,000 cash until the first Sunday close on or after --start; all decisions are Sundays only.

Ledger guarantees: decisions.jsonl, executions.jsonl, marks.jsonl are append-only. Each run replays the rules from public data
and appends only records whose key is absent. A recomputed record that differs from an existing one is appended to
anomalies.jsonl; the run then HALTS without writing anything else and never rewrites history. A missing candle in the needed
range raises an error (no price fill). A non-blocking lock refuses concurrent runs. state.json is a derived summary view only.
Usage: python3 tracker.py --state DIR [--start 2026-10-18]"""
import argparse, fcntl, json, math, os, ssl, statistics, sys, time, urllib.request, datetime as dt
from pathlib import Path
import certifi  # pinned in requirements-pinned.txt and installed in the repo .venv that the schedule runs
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from scripts.research.corrected_research_math import rebalance  # noqa: E402

D = 86400; ASSETS = ("BTC", "ETH"); L = 28; VT = 0.5; FEE = 0.005; SLIP = 0.0005
ACCOUNTS = ("rule", "rule_band10", "hold_btc", "mix_25_25_50", "cash")
BAND = 0.10   # rule_band10: trade an asset only if |target - current weight| >= BAND (E9, forward-tracked)
LEDGERS = ("decisions", "executions", "marks")

class DataGap(Exception): pass
class InvalidData(Exception): pass
class WriteFailure(Exception): pass
class Discrepancy(Exception): pass

def iso(day): return dt.datetime.fromtimestamp(day * D, dt.timezone.utc).date().isoformat()
def is_sunday(day): return dt.datetime.fromtimestamp(day * D, dt.timezone.utc).weekday() == 6

def rule_target(C, i):
    """C: {asset: [closes]} aligned by index; i: decision index. Identical to the frozen stress target (VOL over 30 returns)."""
    w = {}
    for a in ASSETS:
        if C[a][i] / C[a][i - L] - 1 > 0:
            rets = [C[a][k] / C[a][k - 1] - 1 for k in range(i - 29, i + 1)]
            w[a] = 0.5 * min(1.0, VT / (statistics.pstdev(rets) * math.sqrt(365)))
    return w

def banded_rebalance(cash, units, prices, tgt):
    """Identical to the E9 simulator (docs/research/candidate_band_20261013/band.py): assets whose |target - current weight|
    is below BAND are left untouched; the others are rebalanced with the shared helper over the sub-account (cash + those assets)."""
    nav = cash + sum(q * prices[a] for a, q in units.items())
    cur = {a: units.get(a, 0) * prices[a] / nav for a in ASSETS}
    move = [a for a in ASSETS if abs(tgt.get(a, 0) - cur[a]) >= BAND - 1e-12]
    if not move: return cash, dict(units), []
    sub = {a: units.get(a, 0) for a in move}
    eq_sub = cash + sum(sub[a] * prices[a] for a in move)
    want = {a: tgt.get(a, 0) * nav for a in move}
    tot = sum(want.values())
    scale = min(1.0, eq_sub / tot) if tot > 0 else 1.0
    wts = {a: (want[a] * scale) / eq_sub for a in move if want[a] > 0} if eq_sub > 0 else {}
    c2, u2 = rebalance(cash, sub, {a: prices[a] for a in move}, wts, FEE, SLIP)
    new = dict(units)
    for a in move:
        if u2.get(a, 0) > 0: new[a] = u2[a]
        else: new.pop(a, None)
    return c2, new, move

def replay(candles, start_day, last_day):
    """candles: {asset: {day: (open, close)}}. Returns the ordered list of ledger records (without recorded_utc)."""
    first_dec = start_day
    while not is_sunday(first_dec): first_dec += 1
    lo = first_dec - 31
    days = list(range(lo, last_day + 1))
    for a in ASSETS:
        missing = [iso(d) for d in days if d not in candles[a]]
        if missing: raise DataGap(f"{a} missing candles {missing[:5]}{'...' if len(missing) > 5 else ''}")
        bad = [iso(d) for d in days if not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in candles[a][d])]
        if bad: raise InvalidData(f"{a} non-finite or non-positive open/close on {bad[:5]}; nothing written")
    C = {a: [candles[a][d][1] for d in days] for a in ASSETS}
    O = {a: [candles[a][d][0] for d in days] for a in ASSETS}
    pos = {d: k for k, d in enumerate(days)}
    acct = {n: {"cash": 1000.0, "units": {}, "pending": None} for n in ACCOUNTS}
    out = []
    for day in range(first_dec, last_day + 1):
        k = pos[day]
        for n, s in acct.items():                      # 1) execute yesterday's decision at today's open
            if s["pending"] is not None:
                dec_day, tgt = s["pending"]
                prices = {a: O[a][k] for a in ASSETS}
                before = s["cash"] + sum(q * prices[a] for a, q in s["units"].items())
                extra = {}
                if n == "rule_band10":
                    s["cash"], s["units"], moved = banded_rebalance(s["cash"], s["units"], prices, tgt)
                    extra = {"band": BAND, "assets_traded": moved}
                else:
                    s["cash"], s["units"] = rebalance(s["cash"], s["units"], prices, tgt, FEE, SLIP)
                after = s["cash"] + sum(q * prices[a] for a, q in s["units"].items())
                out.append({"ledger": "executions", "account": n, "decision_day": iso(dec_day), "exec_day": iso(day), **extra,
                            "execution_basis": "modelled_next_open_from_public_daily_candle", "observed_fill": False,
                            "open_prices": prices, "cost_usd": round(before - after, 6), "cash_after": round(s["cash"], 6),
                            "units_after": {a: round(q, 12) for a, q in s["units"].items()}})
                s["pending"] = None
            if day > first_dec:                         # 2) mark at today's close, from the first execution day
                nav = s["cash"] + sum(q * C[a][k] for a, q in s["units"].items())
                out.append({"ledger": "marks", "account": n, "day": iso(day), "nav_usd": round(nav, 6)})
        if is_sunday(day):                              # 3) decide at today's close
            for n, s in acct.items():
                if n == "cash" or (n == "hold_btc" and day != first_dec): continue
                tgt = rule_target(C, k) if n in ("rule", "rule_band10") else ({"BTC": 1.0} if n == "hold_btc" else {"BTC": 0.25, "ETH": 0.25})
                rec = {"ledger": "decisions", "account": n, "decision_day": iso(day), "target": {a: round(w, 12) for a, w in tgt.items()}}
                if n == "rule":
                    rec["inputs"] = {a: {"close": C[a][k], "close_28d_ago": C[a][k - L],
                                         "vol30_annual": round(statistics.pstdev([C[a][j] / C[a][j - 1] - 1 for j in range(k - 29, k + 1)]) * math.sqrt(365), 12)} for a in ASSETS}
                if n == "rule_band10": rec["inputs_same_as"] = "rule"
                out.append(rec)
                s["pending"] = (day, tgt)
    return out

def key(r): return (r["ledger"], r["account"], r.get("decision_day") or r.get("day"))
META = ("recorded_utc", "recorded_lag_hours", "reconstructed")
def body(r): return {k: v for k, v in r.items() if k not in META}
def event_close_ts(r):
    """End of the UTC day the record describes: decision close, execution day close, or mark day close."""
    day = {"decisions": r.get("decision_day"), "executions": r.get("exec_day"), "marks": r.get("day")}[r["ledger"]]
    d = int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp()) // D
    return (d + 1) * D
def write_all(fd, data):
    """os.write may write fewer bytes than asked: loop until all are written; zero progress is a failure."""
    view = memoryview(data); done = 0
    while done < len(data):
        k = os.write(fd, view[done:])
        if not k or k < 0: raise WriteFailure(f"ledger write stalled after {done} of {len(data)} bytes; ledger may end in a torn line and the next run will refuse")
        done += k

def load_ledgers(state):
    have = {}
    for name in LEDGERS:
        p = state / f"{name}.jsonl"
        if not p.exists(): continue
        lines = p.read_text().splitlines()
        for n, line in enumerate(lines, 1):
            try: r = json.loads(line)
            except ValueError: raise Discrepancy(f"{p.name} line {n} is not valid JSON (torn write?) - operator must inspect; nothing written")
            if key(r) in have: raise Discrepancy(f"duplicate key {key(r)} in {p.name}")
            have[key(r)] = r
    return have

def sync(state, records, now_utc, now_ts):
    """Append missing records; on any mismatch append an anomaly and halt. Returns count appended."""
    have = load_ledgers(state)
    new = {name: [] for name in LEDGERS}
    for r in records:
        old = have.get(key(r))
        if old is None:
            lag = (now_ts - event_close_ts(r)) / 3600
            new[r["ledger"]].append({**r, "recorded_utc": now_utc, "recorded_lag_hours": round(lag, 2),
                                     "reconstructed": lag > 24})   # recorded more than 24 h after the day it describes
        elif body(old) != r:
            with open(state / "anomalies.jsonl", "a") as f:
                f.write(json.dumps({"recorded_utc": now_utc, "key": list(key(r)), "existing": body(old), "recomputed": r}) + "\n"); f.flush(); os.fsync(f.fileno())
            raise Discrepancy(f"recomputed record differs from ledger for {key(r)}; halted, history unchanged")
    n = 0
    for name, rows in new.items():
        if not rows: continue
        buf = "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in rows)
        fd = os.open(state / f"{name}.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try: write_all(fd, buf.encode()); os.fsync(fd)
        finally: os.close(fd)
        n += len(rows)
    return n

def summary(state, records, last_day):
    marks = [r for r in records if r["ledger"] == "marks"]
    last = {}
    for r in marks: last[r["account"]] = r
    pend = [r for r in records if r["ledger"] == "decisions"]
    execd = {(r["account"], r["decision_day"]) for r in records if r["ledger"] == "executions"}
    return {"artifact_type": "research_only_forward_tracker_v2_derived_view", "places_orders": False,
            "last_completed_day": iso(last_day), "accounts": {a: {"nav_usd": round(r["nav_usd"], 2), "as_of": r["day"]} for a, r in last.items()},
            "pending_decisions": [r for r in pend if (r["account"], r["decision_day"]) not in execd],
            "note": "Derived from the append-only ledgers; the .jsonl files are the record."}

def tls_context():
    """Verified TLS with certifi's CA bundle, as in docs/research/cmc_trending_log/cmc_trending_logger_v3.py. The scheduled
    runtime (.venv on python.org Python 3.12) has no default CA roots, and the 2026-10-19 scheduled run failed with
    CERTIFICATE_VERIFY_FAILED. Verification stays on (CERT_REQUIRED, hostname check); there is no unverified fallback."""
    return ssl.create_default_context(cafile=certifi.where())

def fetch(start_day, last_day):
    out = {}; ctx = tls_context()
    for a in ASSETS:
        rows = {}; t = (start_day - 40) * D
        while t <= last_day * D:
            e = min(t + 299 * D, last_day * D)
            url = (f"https://api.exchange.coinbase.com/products/{a}-USD/candles?granularity=86400"
                   f"&start={dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()}&end={dt.datetime.fromtimestamp(e, dt.timezone.utc).isoformat()}")
            for attempt in range(4):
                try:
                    data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cryptkeep-research"}), timeout=30, context=ctx)); break
                except Exception:
                    if attempt == 3: raise
                    time.sleep(2 * (attempt + 1))
            for ts, lo_, hi_, op, cl, vol in data: rows[int(ts) // D] = (float(op), float(cl))   # API row: time, low, high, open, close, volume
            t = e + D; time.sleep(0.25)
        out[a] = rows
    return out

def main(argv=None, candles=None, now=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--state", required=True); ap.add_argument("--start", default="2026-10-18")
    ap.add_argument("--last-day", help="testing only: override last completed day (YYYY-MM-DD)")
    a = ap.parse_args(argv)
    state = Path(a.state); state.mkdir(parents=True, exist_ok=True)
    start_day = int(dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc).timestamp()) // D
    now = now or time.time()
    last_day = (int(dt.datetime.fromisoformat(a.last_day).replace(tzinfo=dt.timezone.utc).timestamp()) // D) if a.last_day else int(now) // D - 1
    lock = open(state / ".lock", "w")
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise SystemExit("another tracker run holds the lock; nothing written")
    first_dec = start_day
    while not is_sunday(first_dec): first_dec += 1
    if last_day < first_dec:
        print(json.dumps({"status": "waiting", "first_decision_close": iso(first_dec)})); return 0
    candles = candles if candles is not None else fetch(first_dec - 31, last_day)
    records = replay(candles, start_day, last_day)
    now_utc = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat(timespec="seconds")
    before = len(load_ledgers(state))
    sync(state, records, now_utc, now)
    persisted = load_ledgers(state)                      # summary is built from what is on disk, not from intentions
    lost = [k for k in map(key, records) if k not in persisted]
    if lost: raise WriteFailure(f"{len(lost)} replayed records not found on disk after write, e.g. {lost[:3]}")
    rows = sorted(persisted.values(), key=lambda r: (r.get("day") or r.get("exec_day") or r["decision_day"], r["ledger"], r["account"]))
    s = summary(state, rows, last_day); s["appended_this_run"] = len(persisted) - before; s["generated_utc"] = now_utc
    tmp = state / "state.json.tmp"; tmp.write_text(json.dumps(s, indent=2, allow_nan=False)); os.replace(tmp, state / "state.json")
    print(json.dumps(s, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
