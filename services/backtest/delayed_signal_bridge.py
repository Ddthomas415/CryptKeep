"""Synthetic ED-002 fixed one-hour execution delay; no market or order access."""
from bisect import bisect_left
from copy import deepcopy

from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger


class _ReceiptPanel(frozen.HourlyPanel):
    cutoff = None

    def window(self, symbol, close_ms, count):
        if self.cutoff is None:
            raise ValueError("receipt_cutoff_not_set")
        return super().window(symbol, close_ms, count, available_by_ms=self.cutoff)


class DelayedSignalBridge(frozen.FrozenSignalBridge):
    """Signal close T, receipt cutoff/fill T+1h; existing ledger is unchanged.

    Target weights use actual pre-fill units/cash valued at T, not the later
    bar's close. Signal eligibility must be known at T; the ledger separately
    checks permission effective at the T+1h fill. Outcome price validation is
    ex-post consistency checking, not evidence of availability to the signal.
    """

    def __init__(self, *, observations, recent_listings=None, **kwargs):
        super().__init__(observations=observations, recent_listings=recent_listings, **kwargs)
        self.panel = _ReceiptPanel(observations, recent_listings)
        self.identity = {**self.identity, "execution_delay_ms": frozen.HOUR,
            "allocation_clock": "signal_close_marks_actual_prefill_wallet",
            "signal_permission_clock": "signal_close"}

    def binding(self, cutoff):
        # Marking prices may arrive later; bind those ex-post inputs as well.
        return frozen.digest({"signal_binding": super().binding(cutoff),
            "outcome_rows": {s: [r for r in rows if r["row"][0] + frozen.HOUR <= cutoff]
                             for s, rows in self.panel.rows.items()}})

    def _check_outcome_frame(self, frame, required):
        for symbol in required:
            if symbol not in frame["open"] and symbol not in frame["close"]:
                continue
            times = self.panel.times.get(symbol, [])
            index = bisect_left(times, frame["ts_ms"])
            if index == len(times) or times[index] != frame["ts_ms"]:
                raise ledger.Incomplete("missing_delayed_outcome_bar:" + symbol)
            record = self.panel.rows[symbol][index]
            try:
                frozen.validate_bars([record["row"]], interval_ms=frozen.HOUR)
                if any(symbol in frame[side] and ledger.number(frame[side][symbol], positive=True)
                       != ledger.number(record["row"][column], positive=True)
                       for side, column in (("open", 1), ("close", 4))):
                    raise ledger.Incomplete("signal_execution_frame_mismatch:" + symbol)
            except (ValueError, TypeError, IndexError) as error:
                raise ledger.Incomplete("invalid_delayed_outcome_bar:" + symbol) from error

    def __call__(self, context):
        cutoff = ledger.timestamp(context["close_ms"])
        frame = context["history"][-1]
        if (cutoff != frame["ts_ms"] + frozen.HOUR or cutoff < 2 * frozen.HOUR
                or set(context["units"]) != set(self.symbols)):
            raise ledger.Incomplete("delayed_bridge_clock_mismatch")
        signal_close = cutoff - frozen.HOUR
        signal_frame = {"ts_ms": signal_close - frozen.HOUR, "open": {}, "close": {}}
        active = set(self.pair or self.symbols) | {s for s, q in context["units"].items() if q}
        exhausted = not context["cash"] and not any(context["units"].values())
        self.panel.cutoff = cutoff
        try:
            required = set()
            for symbol in sorted(active) if not exhausted else ():
                rule = ledger.rule_at(self.rules, symbol, signal_close, signal_close, self.venue, self.quote)
                if not rule["eligible"] and not context["units"].get(symbol):
                    continue
                required.add(symbol)
                rows = self.panel.window(symbol, signal_close, 1)
                if rows is None:
                    raise ledger.Incomplete("missing_delayed_signal_mark:" + symbol)
                signal_frame["open"][symbol] = rows[-1][1]
                signal_frame["close"][symbol] = rows[-1][4]
            self._check_outcome_frame(frame, required)
            signal_nav = ledger.number(context["cash"]) + sum(
                (ledger.number(q) * ledger.number(signal_frame["close"][s], positive=True)
                 for s, q in context["units"].items() if q), ledger.ZERO)
            signal_context = {**deepcopy(context), "close_ms": signal_close,
                "history": [signal_frame], "marked_nav": signal_nav}
            target = super().__call__(signal_context)
            trace = self.trace[-1]
            trace.update({"strategy_signal_bar_ts_ms": signal_frame["ts_ms"],
                "signal_close_ms": signal_close, "receipt_cutoff_ms": cutoff,
                "model_execution_ms": cutoff, "signal_bar_ts_ms": frame["ts_ms"]})
            return target
        finally:
            self.panel.cutoff = None


def simulate_delayed_bridge(frames, bridge, **kwargs):
    """Explicit delay opt-in; controls use these same frames/first execution open.

    The initial frame ends at T+1h, so the first eligible signal ends at T.
    Common endpoint is the last supplied close; no pending order is executed
    after that endpoint. Full/split use the existing ledger carry contract.
    """
    if not isinstance(bridge, DelayedSignalBridge):
        raise ValueError("explicit_delayed_bridge_required")
    result = frozen.simulate_bridge(frames, bridge, **kwargs)
    result["execution_timing"] = "SIGNAL_CLOSE_PLUS_ONE_HOUR_MODELLED_OPEN"
    decisions = {d["signal_bar_ts_ms"]: d for d in result.get("state", {}).get(
        "signal_bridge", {}).get("decisions", [])} if result.get("state") else {}
    for trade in result.get("bridge_trades", []):
        decision = decisions.get(trade["signal_bar_ts_ms"], {})
        trade["strategy_signal_bar_ts_ms"] = decision.get("strategy_signal_bar_ts_ms")
        trade["receipt_cutoff_ms"] = decision.get("receipt_cutoff_ms")
    return result
