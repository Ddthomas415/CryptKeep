"""Default-off paper entry sizing. No network, order submission or cash mutation."""
from decimal import Decimal, DecimalException, ROUND_FLOOR, localcontext
import hashlib
import math
from pathlib import Path
import sqlite3
from urllib.parse import quote as uri_quote

from services.execution.intent_ttl import _parse_created_epoch
from services.market_data.paper_snapshot_quote import paper_quote_fill_price, read_paper_quote
from services.markets.math_utils import decimal_value
from services.markets.models import MarketRules
from services.markets.rules import DEFAULT_TTL_S, _coinbase_mode_code
from services.markets.symbols import canonicalize
from services.os.app_paths import data_dir
from storage.exit_event_journal import _decode_payload

POLICY = "available_cash_v1"


def _number(value, name, *, positive=False):
    if isinstance(value, bool) or value is None:
        raise ValueError(name)
    value = decimal_value(value, name=name)
    approximate = float(value)
    if (value < 0 or (positive and value == 0) or not math.isfinite(approximate)
            or (value != 0 and approximate == 0)):
        raise ValueError(name)
    return value


def cash_quantity(*, cash, ask, modeled_price, fee_bps, slippage_bps, qty_step, min_qty, min_notional):
    """Reserve against ask, not the engine's mid-price model; round down only."""
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            cash = _number(cash, "cash", positive=True)
            ask = _number(ask, "ask", positive=True)
            modeled = _number(modeled_price, "modeled_price", positive=True)
            fee = _number(fee_bps, "fee") / 10000
            slip = _number(slippage_bps, "slippage") / 10000
            step = _number(qty_step, "qty_step", positive=True)
            minimum = _number(min_qty, "min_qty")
            notional = _number(min_notional, "min_notional")
            if fee >= 1 or slip >= 1:
                raise ValueError("cost_range")
            price = ask * (1 + slip)
            if modeled > price:
                raise ValueError("reservation_below_modeled_price")
            unit_cost = price * (1 + fee)
            if not math.isfinite(float(unit_cost)):
                raise ValueError("cost_float_range")
            quantity = (cash / unit_cost / step).to_integral_value(rounding=ROUND_FLOOR) * step
            # The consumer uses floats. Refuse unrepresentable precision and
            # leave a step if its cost arithmetic rounds beyond available cash.
            for _ in range(2):
                q = float(quantity)
                total = q * float(price) * (1 + float(fee))
                if not math.isfinite(q) or Decimal(str(q)) != quantity:
                    raise ValueError("quantity_float_precision")
                if total <= float(cash) and quantity * unit_cost <= cash:
                    break
                quantity -= step
            else:
                raise ValueError("float_affordability")
            if (quantity <= 0 or quantity < minimum or quantity * modeled < notional
                    or q * float(modeled) < float(notional)):
                raise ValueError("below_market_minimum")
            return {"qty": q, "estimated_total": total, "cash": str(cash),
                    "ask": str(ask), "modeled_price": str(modeled), "fee_bps": str(fee * 10000),
                    "slippage_bps": str(slip * 10000), "qty_step": str(step)}
    except (DecimalException, OverflowError, TypeError) as exc:
        raise ValueError("invalid_sizing_number") from exc


def _cached_rules(venue, symbol, now, *, cache_path=None):
    """Read only this account's existing public metadata; never refresh it."""
    path = data_dir() / "execution.sqlite" if cache_path is None else Path(cache_path)
    uri = "file:" + uri_quote(str(path.resolve()), safe="/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        rows = con.execute(
            "SELECT updated_ts,rules_json FROM market_rules_cache "
            "WHERE venue=? AND canonical_symbol=? LIMIT 2", (venue, canonicalize(symbol)),
        ).fetchall()
    finally:
        con.close()
    if len(rows) != 1:
        raise ValueError("market_rules_missing_or_ambiguous")
    stamp, raw = rows[0]
    epoch = _parse_created_epoch(now)
    if (type(stamp) not in (float, int) or not math.isfinite(stamp) or epoch is None
            or not 0 <= epoch - stamp <= DEFAULT_TTL_S):
        raise ValueError("market_rules_stale_or_future")
    if type(raw) is not str or len(raw.encode()) > 65536:
        raise ValueError("market_rules_invalid")
    rules = MarketRules(**_decode_payload(raw))
    if (rules.venue != venue or rules.canonical_symbol != canonicalize(symbol)
            or rules.native_symbol != canonicalize(symbol) or rules.active is not True
            or _coinbase_mode_code(rules, "market") is not None):
        raise ValueError("market_rules_identity_or_mode")
    return rules, {"updated_ts": stamp, "sha256": hashlib.sha256(raw.encode()).hexdigest()}


def size_paper_entry(*, cfg, qdb, pdb, venue, symbol, now):
    """Return an explicit refusal, never a fallback to configured fixed quantity."""
    try:
        policy = cfg.get("_paper_entry_policy")
        if cfg.get("paper_entry_sizing") != POLICY or type(policy) is not dict:
            raise ValueError("invalid_policy")
        if (policy.get("live_enabled") is not False or policy.get("armed") is not False
                or policy.get("enabled") is not True
                or policy.get("require_fresh_snapshot_quotes") is not True
                or policy.get("use_ccxt_fallback") is not False):
            raise ValueError("paper_only_guards")
        if (venue != "coinbase" or cfg.get("symbols") != [symbol]
                or cfg.get("auto_select_best_venue") is not False
                or cfg.get("position_aware") is not True or cfg.get("order_type") != "market"):
            raise ValueError("unsupported_account_layout")
        if symbol.count("/") != 1 or symbol.split("/")[1] != policy.get("quote_currency"):
            raise ValueError("quote_currency_mismatch")
        budget = pdb.entry_cash_snapshot()
        if (budget["quote_currency"] != policy.get("quote_currency")
                or budget["nonflat_positions"] != 0 or budget["open_orders"] != 0):
            raise ValueError("account_not_flat_or_unknown")
        if qdb.list_pending_paper_buys() or qdb.has_open_strategy_intent(symbol):
            raise ValueError("pending_intent")
        quote, reason = read_paper_quote(venue, symbol, clock=lambda: now)
        if quote is None or canonicalize(quote["symbol_mapped"]) != canonicalize(symbol):
            raise ValueError("quote_" + str(reason or "mapping"))
        rules, evidence = _cached_rules(venue, symbol, now)
        modeled = paper_quote_fill_price(quote, side="buy", order_type="market", limit=None,
                                        slippage_bps=policy.get("slippage_bps"))
        result = cash_quantity(cash=budget["cash_quote"], ask=quote["ask"],
                               modeled_price=modeled,
                               fee_bps=policy.get("fee_bps"), slippage_bps=policy.get("slippage_bps"),
                               qty_step=rules.qty_step, min_qty=rules.min_qty, min_notional=rules.min_notional)
        return {"ok": True, "qty": result["qty"], "evidence": {
            "policy": POLICY, "basis": "ask_reservation_not_execution", "observed_at": now,
            "quote_currency": budget["quote_currency"], "quote": quote,
            "market_rules": evidence, **result}}
    except Exception as exc:
        # Only fixed vocabulary/error types are retained; never configuration or SQL text.
        reason = str(exc) if type(exc) is ValueError and str(exc).replace("_", "").isalnum() else type(exc).__name__
        return {"ok": False, "reason": reason[:96]}
