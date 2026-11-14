"""Pure ED-002 signal adapters; no fetching, persistence or trading authority."""
from bisect import bisect_right
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import statistics

from services.backtest import shared_cash_research as ledger
from services.backtest.next_open_research import validate_bars
from services.strategies.strategy_registry import compute_signal


HOUR, DAY = 3600000, 86400000
SNAPSHOT_SHA256 = "709149a916da94c4edd99065f2f70b456ef7e8fc95b130e5420cc17aab998cfc"
POLICY = "ed002-event-close-weights-entry-1of25-v1"
FAMILIES = {"breakout_default", "ema_cross_default", "mean_reversion_default"}


def digest(value):
    def exact(item):
        if isinstance(item, Fraction):
            return {"fraction": [item.numerator, item.denominator]}
        raise TypeError("unsupported_fingerprint_type")
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        allow_nan=False, default=exact).encode()).hexdigest()


def event_targets(context, actions, marks):
    """Adopted close-weight policy, not exact-unit preservation at the next open."""
    quantities = {s: ledger.number(q) for s, q in context["units"].items()}
    if set(actions) != set(quantities) or any(a not in ("buy", "sell", "hold") for a in actions.values()):
        raise ledger.Incomplete("invalid_strategy_actions")
    cash = ledger.number(context["cash"])
    if any(q and s not in marks for s, q in quantities.items()):
        raise ledger.Incomplete("unknown_decision_valuation")
    values = {s: q * ledger.number(marks[s], positive=True) if q else Fraction(0)
              for s, q in quantities.items()}
    nav = cash + sum(values.values())
    if nav != context["marked_nav"]:
        raise ledger.Incomplete("decision_nav_mismatch")
    if not nav:
        return None
    sells = {s for s, q in quantities.items() if q and actions[s] == "sell"}
    buys = {s for s, q in quantities.items() if not q and actions[s] == "buy"}
    if not sells and not buys:
        return None
    target = {s: values[s] / nav if quantities[s] and s not in sells else Fraction(0)
              for s in quantities}
    remaining = 1 - sum(target.values())
    allocation = min(Fraction(1, 25), remaining / len(buys)) if buys else Fraction(0)
    if not sells and not allocation:
        return None
    for symbol in buys:
        target[symbol] = allocation
    return target


class HourlyPanel:
    """Copied caller records: {row: [ts,o,h,l,c,v], known_at_ms: int}."""

    def __init__(self, observations, recent_listings=None):
        self.rows, self.times = {}, {}
        self.listings = deepcopy(recent_listings or {})
        for symbol, records in deepcopy(observations).items():
            ordered = sorted(records, key=lambda r: ledger.timestamp(r["row"][0]))
            times = [ledger.timestamp(r["row"][0]) for r in ordered]
            if len(times) != len(set(times)) or any(t % HOUR for t in times):
                raise ValueError("duplicate_or_unaligned_panel_timestamp")
            for record in ordered:
                ledger.timestamp(record["known_at_ms"])
            self.rows[symbol], self.times[symbol] = ordered, times

    def window(self, symbol, close_ms, count, *, available_by_ms=None):
        cutoff = close_ms if available_by_ms is None else ledger.timestamp(available_by_ms)
        if cutoff < close_ms:
            raise ValueError("availability_precedes_window_close")
        last, first = close_ms - HOUR, close_ms - count * HOUR
        times = self.times.get(symbol, [])
        end = bisect_right(times, last)
        records = self.rows.get(symbol, [])[max(0, end - count):end]
        listing = self.listings.get(symbol)
        if listing is not None:
            listed = ledger.timestamp(listing["first_bar_ms"])
            known = ledger.timestamp(listing["known_at_ms"])
            if known <= cutoff and first < listed <= last:
                first = listed
        wanted = list(range(first, last + HOUR, HOUR))
        records = [r for r in records if r["row"][0] >= first]
        if [r["row"][0] for r in records] != wanted or any(r["known_at_ms"] > cutoff for r in records):
            raise ledger.Incomplete("missing_or_unavailable_ohlcv:" + symbol)
        rows = [deepcopy(r["row"]) for r in records]
        try:
            validate_bars(rows, interval_ms=HOUR)
        except (ValueError, TypeError, IndexError):
            raise ledger.Incomplete("invalid_ohlcv:" + symbol) from None
        return rows if len(rows) == count else None

    def prefix(self, cutoff):
        return {"observations": {s: [r for r in rows if r["row"][0] + HOUR <= cutoff
                and r["known_at_ms"] <= cutoff] for s, rows in self.rows.items()},
            "listings": {s: r for s, r in self.listings.items() if r["known_at_ms"] <= cutoff}}


class FrozenSignalBridge:
    """State comes from actual ledger holdings; missed intents are never latched."""

    def __init__(self, *, symbols, observations, rules, venue, quote,
                 snapshot_bytes=None, family=None, incumbent=None,
                 recent_listings=None, valuation_marks=None):
        self.symbols = tuple(sorted(symbols))
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("explicit_unique_symbols_required")
        self.panel = HourlyPanel(observations, recent_listings)
        self.rules, self.marks = deepcopy(rules), deepcopy(valuation_marks or {})
        self.venue, self.quote, self.trace = venue, quote, []
        if incumbent is not None:
            if family is not None or len(incumbent) != 2 or len(set(incumbent)) != 2 or set(incumbent) - set(self.symbols):
                raise ValueError("explicit_incumbent_pair_required")
            self.pair, self.config = tuple(incumbent), None
            self.identity = {"policy": "incumbent-28d-vol30-sunday-v1", "pair": self.pair}
        else:
            if not isinstance(snapshot_bytes, bytes) or hashlib.sha256(snapshot_bytes).hexdigest() != SNAPSHOT_SHA256:
                raise ValueError("frozen_snapshot_mismatch")
            snapshot = json.loads(snapshot_bytes)
            if set(snapshot["strategies"]) != FAMILIES or family not in FAMILIES:
                raise ValueError("unknown_frozen_family")
            self.pair = None
            self.config = {"strategy": {**snapshot["strategies"][family], "emit_evidence": False}}
            self.identity = {"policy": POLICY, "family": family, "snapshot_sha256": SNAPSHOT_SHA256}
        self._config_digest = digest(self.config)

    def binding(self, cutoff):
        return digest({"identity": self.identity, "symbols": self.symbols,
            "panel": self.panel.prefix(cutoff),
            "rules": {s: [r for r in rows if r["known_at_ms"] <= cutoff] for s, rows in self.rules.items()},
            "marks": {s: [m for m in rows if m["ts_ms"] <= cutoff and m["known_at_ms"] <= cutoff]
                      for s, rows in self.marks.items()}})

    def __call__(self, context):
        close = ledger.timestamp(context["close_ms"])
        frame = context["history"][-1]
        if close != frame["ts_ms"] + HOUR or set(context["units"]) != set(self.symbols):
            raise ledger.Incomplete("bridge_clock_or_universe_mismatch")
        marks = ledger.marks_at(frame["close"], self.marks, self.symbols, close)
        actions, readiness = {}, {}
        if digest(self.config) != self._config_digest:
            raise ValueError("frozen_strategy_config_changed")
        if context["marked_nav"] == 0 and not context["cash"] and not any(context["units"].values()):
            actions = dict.fromkeys(self.symbols, "hold")
            readiness = dict.fromkeys(self.symbols, "exhausted_account")
            target = None
        elif self.pair is not None:
            target = self._incumbent(close, frame)
        else:
            for symbol in self.symbols:
                rule = ledger.rule_at(self.rules, symbol, close, close, self.venue, self.quote)
                if not rule["eligible"]:
                    actions[symbol], readiness[symbol] = "hold", "known_ineligible"
                    continue
                rows = self.panel.window(symbol, close, 300)
                if rows is None:
                    if context["units"][symbol]:
                        raise ledger.Incomplete("held_symbol_not_signal_ready:" + symbol)
                    actions[symbol], readiness[symbol] = "hold", "documented_recent_listing"
                    continue
                if (symbol not in frame["close"] or symbol not in frame["open"]
                        or ledger.number(rows[-1][4]) != ledger.number(frame["close"][symbol])
                        or ledger.number(rows[-1][1]) != ledger.number(frame["open"][symbol])):
                    raise ledger.Incomplete("signal_execution_frame_mismatch:" + symbol)
                try:
                    signal = compute_signal(cfg=deepcopy(self.config), symbol=symbol, ohlcv=rows)
                except (ValueError, TypeError, ArithmeticError):
                    raise ledger.Incomplete("frozen_signal_error:" + symbol) from None
                if not isinstance(signal, dict) or signal.get("ok") is not True or signal.get("action") not in ("buy", "sell", "hold"):
                    raise ledger.Incomplete("invalid_frozen_signal:" + symbol)
                try:
                    json.dumps(signal, allow_nan=False)
                except (ValueError, TypeError):
                    raise ledger.Incomplete("invalid_frozen_signal_values:" + symbol) from None
                actions[symbol], readiness[symbol] = signal["action"], "ready"
            target = event_targets(context, actions, marks)
        self.trace.append({"signal_bar_ts_ms": frame["ts_ms"], "actions": actions,
            "readiness": readiness, "targets": deepcopy(target),
            "held_without_sell": [] if self.pair is not None else
                [s for s in self.symbols if context["units"][s] and actions.get(s) != "sell"]})
        return target

    def _incumbent(self, close, frame):
        for symbol in self.pair:
            if symbol not in frame["open"] and symbol not in frame["close"]:
                continue
            current = self.panel.window(symbol, close, 1)
            if current is None:
                raise ledger.Incomplete("missing_incumbent_current_bar:" + symbol)
            if any(symbol in frame[side] and ledger.number(current[-1][column]) != ledger.number(frame[side][symbol])
                   for side, column in (("open", 1), ("close", 4))):
                raise ledger.Incomplete("signal_execution_frame_mismatch:" + symbol)
        if close % DAY or datetime.fromtimestamp((close - DAY) / 1000, timezone.utc).weekday() != 6:
            return None
        target = dict.fromkeys(self.symbols, Fraction(0))
        for symbol in self.pair:
            rule = ledger.rule_at(self.rules, symbol, close, close, self.venue, self.quote)
            if not rule["eligible"]:
                continue
            rows = self.panel.window(symbol, close, 61 * 24)
            if rows is None:
                raise ledger.Incomplete("insufficient_incumbent_history:" + symbol)
            if (symbol not in frame["close"] or symbol not in frame["open"]
                    or ledger.number(rows[-1][4]) != ledger.number(frame["close"][symbol])
                    or ledger.number(rows[-1][1]) != ledger.number(frame["open"][symbol])):
                raise ledger.Incomplete("signal_execution_frame_mismatch:" + symbol)
            prices = [float(rows[i][4]) for i in range(23, len(rows), 24)]
            if prices[-1] / prices[-29] - 1 > 0:
                returns = [prices[i] / prices[i - 1] - 1 for i in range(len(prices) - 30, len(prices))]
                vol = statistics.pstdev(returns) * math.sqrt(365)
                if not math.isfinite(vol) or vol <= 0:
                    raise ledger.Incomplete("undefined_incumbent_volatility:" + symbol)
                target[symbol] = ledger.number(.5 * min(1, .5 / vol))
        return target


def simulate_bridge(frames, bridge, *, state=None, target_contract_id, decision_trade_context=False, **profile):
    """Run the existing ledger; incomplete first-decision evidence has no state."""
    if type(decision_trade_context) is not bool:
        raise ValueError("invalid_decision_trade_context")
    if profile.get("interval_ms") != HOUR or tuple(sorted(profile["symbols"])) != bridge.symbols:
        raise ValueError("bridge_profile_mismatch")
    if profile["venue"] != bridge.venue or profile["quote"] != bridge.quote or profile["rules"] != bridge.rules:
        raise ValueError("bridge_metadata_mismatch")
    if (profile.get("valuation_marks") or {}) != bridge.marks:
        raise ValueError("bridge_valuation_metadata_mismatch")
    old_trace = []
    if state is not None:
        cutoff = state["last_ts"] + HOUR
        old = state.get("signal_bridge")
        if not old or old["binding"] != bridge.binding(cutoff):
            raise ValueError("bridge_historical_inputs_or_policy_changed")
        old_trace = deepcopy(old["decisions"])
    bridge.trace = []
    try:
        simulate = ledger.simulate_shared_with_trade_context if decision_trade_context else ledger.simulate_shared_next_open
        result = simulate(frames, bridge, state=state,
            target_contract_id=target_contract_id + ":" + digest(bridge.identity), **profile)
    except ledger.Incomplete as error:
        if state is not None:
            raise
        return {"status": "INCOMPLETE", "reason": str(error), "state": None,
            "qualification": ledger.QUALIFICATION, "bootstrap_failure": True}
    combined = old_trace + deepcopy(bridge.trace)
    result["state"]["signal_bridge"] = {"binding": bridge.binding(result["state"]["last_ts"] + HOUR),
        "identity": deepcopy(bridge.identity), "decisions": combined}
    triggers = {d["signal_bar_ts_ms"]: d for d in combined}
    annotated = []
    for trade in result["state"]["trades"]:
        decision = triggers.get(trade["signal_bar_ts_ms"], {})
        incidental = not trade["terminal"] and trade["symbol"] in decision.get("held_without_sell", [])
        annotated.append({**trade, "incidental_rebalance": incidental,
                          "raw_action": decision.get("actions", {}).get(trade["symbol"])})
    result["bridge_trades"] = annotated
    result["incidental_turnover_quote"] = sum((t["qty"] * t["raw_price"] for t in annotated
                                               if t["incidental_rebalance"]), Fraction(0))
    return result
