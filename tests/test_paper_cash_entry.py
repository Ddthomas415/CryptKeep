"""Offline, opt-in paper sizing; no account access or market requests."""
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

import pytest

from tests.test_runner_multi_symbol_integration import harness, PRICES


def policy(**changes):
    return {"live_enabled": False, "armed": False, "enabled": True,
            "quote_currency": "USD", "fee_bps": 50, "slippage_bps": 0,
            "require_fresh_snapshot_quotes": True, "use_ccxt_fallback": False,
            **changes}


def rules(symbol="BTC/USD", **changes):
    from services.markets.models import MarketRules
    native = symbol.replace("/", "-")
    return MarketRules("coinbase", native, native, True, min_notional=1, min_qty=.01,
                       qty_step=.01, meta={"coinbase_product": {
                           "product_id": native, "status": "online", "trading_disabled": False,
                           "cancel_only": False, "limit_only": False, "post_only": False,
                           "auction_mode": False}}, **changes)


def prepare(h, monkeypatch, symbol="BTC/USD"):
    h.cfg.update(symbol=symbol, symbols=[symbol], paper_entry_sizing="available_cash_v1",
                 _paper_entry_policy=policy())
    h.paper.set_state("cash_quote", "1000")
    h.paper.set_state("quote_currency", "USD")
    h.signal_action = "buy"
    monkeypatch.setattr(h, "consume", lambda: None)
    from services.market_data import tick_reader
    from services.os.app_paths import data_dir
    snapshot = h.tmp / "quote.json"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    price = PRICES[symbol]
    snapshot.write_text(json.dumps({"ts_ms": now_ms, "ticks": [{
        "source": "public_ticker", "venue": "coinbase", "symbol": symbol,
        "symbol_mapped": symbol, "ticker_symbol": symbol,
        "bid": price, "ask": price, "ts_ms": now_ms}]}))
    monkeypatch.setattr(tick_reader, "LATEST", snapshot)
    db = data_dir() / "execution.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    from dataclasses import asdict
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE market_rules_cache(venue TEXT, canonical_symbol TEXT, updated_ts REAL, rules_json TEXT)")
        con.execute("INSERT INTO market_rules_cache VALUES(?,?,?,?)",
                    ("coinbase", symbol.replace("/", "-"), now_ms / 1000, json.dumps(asdict(rules(symbol)))))
    return snapshot, db


@pytest.mark.parametrize("symbol", list(PRICES))
@pytest.mark.parametrize("strategy", ["breakout_default", "ema_cross_default", "mean_reversion_default"])
def test_runner_sizes_paper_entry_from_cash_not_fixed_quantity(harness, monkeypatch, symbol, strategy):
    h = harness
    prepare(h, monkeypatch, symbol)
    h.cfg["strategy_preset"] = strategy
    h.run(1)
    [intent] = h.intents("buy")
    expected = (Decimal("1000") / (Decimal(str(PRICES[symbol])) * Decimal("1.005"))
                / Decimal(".01")).to_integral_value(rounding="ROUND_FLOOR") * Decimal(".01")
    assert intent["qty"] == float(expected)
    assert intent["meta"]["paper_entry_sizing"]["policy"] == "available_cash_v1"
    assert Decimal(str(intent["qty"])) * Decimal(str(PRICES[symbol])) * Decimal("1.005") <= 1000


@pytest.mark.parametrize("failure", ["cash", "currency", "live", "quote", "rules", "pending"])
def test_runner_does_not_fall_back_to_fixed_qty_for_unknown_sizing(harness, monkeypatch, failure):
    h = harness
    snapshot, db = prepare(h, monkeypatch)
    if failure == "cash":
        h.paper.set_state("cash_quote", "NaN")
    elif failure == "currency":
        h.paper.set_state("quote_currency", "USDT")
    elif failure == "live":
        h.cfg["_paper_entry_policy"]["live_enabled"] = True
    elif failure == "quote":
        snapshot.write_text("{}")
    elif failure == "rules":
        db.unlink()
    else:
        from tests.test_paper_reconciler_recovery import _base_intent
        h.queue.upsert_intent(_base_intent("held-buy", status="held"))
    h.run(1)
    assert not [row for row in h.intents("buy") if row["intent_id"] != "held-buy"]
    assert any(row.get("note") == "paper_entry_sizing_refused" for row in h.statuses)


def size(**changes):
    from services.execution.paper_cash_entry import cash_quantity
    return cash_quantity(cash=changes.pop("cash", 1000), ask=changes.pop("ask", 100),
                         modeled_price=changes.pop("modeled_price", 100),
                         fee_bps=changes.pop("fee_bps", 50), slippage_bps=changes.pop("slippage_bps", 0),
                         qty_step=changes.pop("qty_step", .01), min_qty=changes.pop("min_qty", .01),
                         min_notional=changes.pop("min_notional", 1), **changes)


def test_runner_minimum_uses_modeled_mid_not_ask_reservation(harness, monkeypatch):
    h = harness
    snapshot, db = prepare(h, monkeypatch)
    h.paper.set_state("cash_quote", "100")
    h.cfg["_paper_entry_policy"]["fee_bps"] = 0
    payload = json.loads(snapshot.read_text())
    payload["ticks"][0].update(bid=98, ask=100)
    snapshot.write_text(json.dumps(payload))
    with sqlite3.connect(db) as con:
        data = json.loads(con.execute("SELECT rules_json FROM market_rules_cache").fetchone()[0])
        data.update(qty_step=1, min_qty=1, min_notional=100)
        con.execute("UPDATE market_rules_cache SET rules_json=?", (json.dumps(data),))
    h.run(1)
    assert not h.intents("buy"), "ask=100 must not mask modeled fill notional 99 below minimum 100"


@pytest.mark.parametrize("cash,expected", [(1000, 9.95), (900, 8.95), (1100, 10.94)])
def test_cash_carry_forward_and_fee_inclusive_round_down(cash, expected):
    result = size(cash=cash)
    assert result["qty"] == expected
    assert result["estimated_total"] <= cash


@pytest.mark.parametrize("field", ["cash", "ask", "modeled_price", "fee_bps", "slippage_bps", "qty_step", "min_qty", "min_notional"])
@pytest.mark.parametrize("value", [None, True, "NaN", float("inf"), -1])
def test_invalid_number_is_refused(field, value):
    with pytest.raises(ValueError):
        size(**{field: value})


def test_zero_cost_is_valid_but_zero_precision_and_tiny_cash_are_not():
    assert size(fee_bps=0, slippage_bps=0)["qty"] == 10
    for data in ({"qty_step": 0}, {"cash": 0}, {"ask": 0}, {"cash": .001}):
        with pytest.raises(ValueError):
            size(**data)


def test_conservative_ask_cost_leaves_no_overdraft():
    result = size(ask=101, slippage_bps=25)
    assert result["qty"] == 9.82
    assert result["qty"] * 101 * 1.0025 * 1.005 <= 1000


def test_minimum_notional_is_execution_relative_with_nonzero_spread():
    with pytest.raises(ValueError, match="below_market_minimum"):
        size(cash=100, ask=100, modeled_price=99, fee_bps=0, qty_step=1, min_qty=1, min_notional=100)
    assert size(cash=100, ask=100, modeled_price=99, fee_bps=0,
                qty_step=1, min_qty=1, min_notional=99)["qty"] == 1


@pytest.mark.parametrize("value", ["1e1000", "1e-1000", 10 ** 400])
def test_unrepresentable_float_boundary_is_refused(value):
    with pytest.raises(ValueError):
        size(cash=value)


@pytest.mark.parametrize("failure", ["future", "stale", "wrong_market", "limit_only", "precision", "corrupt"])
def test_metadata_failures_refuse_new_runner_buy(harness, monkeypatch, failure):
    h = harness
    _, db = prepare(h, monkeypatch)
    with sqlite3.connect(db) as con:
        stamp, raw = con.execute("SELECT updated_ts,rules_json FROM market_rules_cache").fetchone()
        data = json.loads(raw)
        if failure == "future":
            stamp += 60
        elif failure == "stale":
            stamp -= 6 * 3600 + 60
        elif failure == "wrong_market":
            data["native_symbol"] = "ETH-USD"
        elif failure == "limit_only":
            data["meta"]["coinbase_product"]["limit_only"] = True
        elif failure == "precision":
            data["qty_step"] = None
        con.execute("UPDATE market_rules_cache SET updated_ts=?,rules_json=?",
                    (stamp, "{bad" if failure == "corrupt" else json.dumps(data)))
    h.run(1)
    assert not h.intents("buy")
    assert h.state.get(h.key("entry_price", "BTC/USD")) is None


@pytest.mark.parametrize("field,value", [("armed", None), ("enabled", "true"),
    ("require_fresh_snapshot_quotes", False), ("use_ccxt_fallback", True)])
def test_ambiguous_or_incompatible_policy_refuses_only_entry(harness, monkeypatch, field, value):
    h = harness
    prepare(h, monkeypatch)
    h.cfg["_paper_entry_policy"][field] = value
    h.run(1)
    assert not h.intents("buy")


def test_all_account_holdings_are_checked_beyond_default_position_window(harness, monkeypatch):
    h = harness
    prepare(h, monkeypatch)
    with sqlite3.connect(h.runner.PaperTradingSQLite.get_state.__globals__["DB_PATH"]) as con:
        for index in range(240):
            con.execute("INSERT INTO paper_positions VALUES(?,?,?,?,?)",
                        (f"OTHER{index}/USD", .01 if index == 239 else 0, 100, 0, str(index)))
    h.run(1)
    assert not h.intents("buy")


def test_sizing_refusal_does_not_block_a_protective_exit(harness, monkeypatch):
    h = harness
    prepare(h, monkeypatch)
    h.cfg["paper_entry_sizing"] = "invalid"
    h.paper.upsert_position("BTC/USD", 1, 100, 0)
    h.state.set(h.key("entry_price", "BTC/USD"), "100")
    h.quotes["BTC/USD"] = [90]
    h.signal_action = "hold"
    h.run(1)
    [intent] = h.intents("sell")
    assert intent["qty"] == 1
    assert "paper_entry_sizing" not in intent["meta"]


def test_actual_paper_fill_charges_fees_and_next_budget_uses_remaining_cash(harness, monkeypatch):
    h = harness
    snapshot, _ = prepare(h, monkeypatch)
    h.run(1)
    [intent] = h.intents("buy")
    import services.execution.paper_engine as module
    from tests.test_paper_reconciler_recovery import _allow_submit_gates
    monkeypatch.setattr(module, "load_user_yaml", lambda: {"paper_trading": policy()})
    _allow_submit_gates(monkeypatch, module)
    engine = module.PaperEngine()
    placed = engine.submit_order(client_order_id="sized-fixture", venue="coinbase", symbol="BTC/USD",
                                 side="buy", order_type="market", qty=intent["qty"])
    assert placed["ok"]
    assert engine.evaluate_open_orders()["filled"] == 1
    assert engine.cash_quote() == pytest.approx(.025)
    [fill] = engine.db.list_fills()
    assert fill["fee"] == pytest.approx(4.975)
    # Real ledger sell at a new synthetic quote: cash, not initial capital, carries forward.
    payload = json.loads(snapshot.read_text())
    payload["ticks"][0].update(bid=120, ask=120)
    snapshot.write_text(json.dumps(payload))
    placed = engine.submit_order(client_order_id="sized-sell-fixture", venue="coinbase", symbol="BTC/USD",
                                 side="sell", order_type="market", qty=intent["qty"])
    assert placed["ok"]
    assert engine.evaluate_open_orders()["filled"] == 1
    assert engine.cash_quote() == pytest.approx(1188.055)
    assert h.queue.update_status(intent["intent_id"], "submitted")
    assert h.queue.update_status(intent["intent_id"], "filled")
    from services.execution.paper_cash_entry import size_paper_entry
    next_entry = size_paper_entry(cfg=h.cfg, qdb=h.queue, pdb=engine.db,
                                 venue="coinbase", symbol="BTC/USD", now=h.runner._now())
    assert next_entry["ok"], next_entry
    assert next_entry["qty"] == 9.85


def test_configuration_resolves_only_explicit_opt_in_and_never_mutates_it(harness, monkeypatch):
    import copy
    import services.execution.strategy_runner as runner
    raw = {"strategy_runner": {"paper_entry_sizing": "available_cash_v1"},
           "execution": {"live_enabled": False}, "live_execution": {"armed": False},
           "paper_trading": policy()}
    saved = copy.deepcopy(raw)
    monkeypatch.setattr(runner, "load_user_yaml", lambda **kw: raw)
    cfg = runner._cfg()
    assert cfg["paper_entry_sizing"] == "available_cash_v1"
    assert cfg["_paper_entry_policy"] == policy()
    assert raw == saved
    raw["execution"] = ["malformed"]
    assert runner._cfg()["_paper_entry_policy"]["live_enabled"] is None
    raw["strategy_runner"].pop("paper_entry_sizing")
    assert "paper_entry_sizing" not in runner._cfg()
