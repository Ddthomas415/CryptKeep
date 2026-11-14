from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/research/exit_variants_spec_20261114"
loader = importlib.util.spec_from_file_location("exit_variant_replay", SPEC / "replay_exit_variants.py")
replay = importlib.util.module_from_spec(loader)
loader.loader.exec_module(replay)
CONTRACT = json.loads((SPEC / "replay_contract.json").read_text())


def bars(closes):
    return [[i * replay.HOUR, c, c + 0.1, c - 0.1, c, 10] for i, c in enumerate(closes)]


def trade(*, i=1, exit_i=2, entry_px=100, exit_px=110, rule="signal"):
    return dict(i=i, exit_i=exit_i, entry_px=entry_px, exit_px=exit_px, rule=rule)


def metrics(rows, trades, fee=0.005):
    return replay.account_metrics(rows, trades, 1, fee, ["hold"] * len(rows), ["sell"] * len(rows), CONTRACT)


def test_fee_and_original_quantity_accounting():
    out = metrics(bars([100, 100, 110]), [trade()])
    assert out["net_quote"] == pytest.approx(8.95)
    assert out["fees_quote"] == pytest.approx(1.05)
    assert out["before_fee_after_slippage_quote"] == pytest.approx(10)
    assert out["bar_close_mtm_max_drawdown_quote"] == pytest.approx(0.5)
    assert out["blocked_sell_signal_bars_while_held"] == 1


def test_drawdown_includes_unrealized_loss_and_terminal_fee():
    out = metrics(bars([100, 40, 95]), [trade(exit_i=3, exit_px=95, rule="terminal")])
    assert out["bar_close_mtm_max_drawdown_quote"] == pytest.approx(60.5)
    assert out["net_quote"] == pytest.approx(-5.975)
    assert out["exposure_lower_bar_fraction"] == 1
    assert out["exposure_upper_bar_fraction"] == 1


def test_same_bar_exit_has_nonzero_exposure_upper_bound():
    out = metrics(bars([100, 100, 110]), [trade(exit_i=1, rule="trailing_stop")])
    assert out["exposure_lower_bar_fraction"] == 0
    assert out["exposure_upper_bar_fraction"] == 0.5
    assert out["blocked_sell_signal_bars_while_held"] == 0


def test_no_trade_account_and_affordability_guard():
    assert metrics(bars([100, 100]), [])["terminal_cash_quote"] == 1000
    low_cash = {**CONTRACT, "initial_cash_per_symbol_quote": 100}
    with pytest.raises(ValueError, match="unaffordable"):
        replay.account_metrics(bars([100, 100, 110]), [trade()], 1, 0.005, ["hold"] * 3, ["hold"] * 3, low_cash)


def test_legacy_helpers_do_not_execute_original_experiment_and_gap_fills_at_open():
    helpers = replay.legacy_helpers(CONTRACT)
    assert "db" not in helpers and "snap" not in helpers
    rows = [[0, 100, 100, 100, 100, 1], [replay.HOUR, 100, 101, 99, 100, 1],
            [2 * replay.HOUR, 80, 81, 79, 80, 1]]
    trades = helpers["simulate"](rows, ["hold", "hold", "hold"], 1,
                                 entry_rule="level", stack_mode="path", sid="ema_cross", forced_entries={1})
    assert len(trades) == 1
    assert trades[0]["rule"] == "stop_loss"
    assert trades[0]["exit_px"] == pytest.approx(80 * 0.9995)
    assert helpers["net_usd"](trades[0], 0.005) < -20


@pytest.mark.parametrize("filename,params", [
    ("breakout_donchian", {"donchian_len": 3, "min_volume_ratio": 10000}),
    ("ema_cross", {"ema_fast": 2, "ema_slow": 3, "min_volume_ratio": 10000}),
    ("mean_reversion_rsi", {"rsi_len": 3, "sma_len": 3, "min_volume_ratio": 10000}),
])
def test_triplet_parity_and_deadline(filename, params):
    current = replay.importlib.import_module("services.strategies." + filename)
    rows = bars([100 + (i % 8) * (-1 if i // 8 % 2 else 1) for i in range(60)])
    default, variant, raw, compared = replay.action_triplet(
        replay.before_module(filename), current, params, rows, 8, time.monotonic() + 10)
    assert compared == 52
    assert all((d == "buy") == (v == "buy") for d, v in zip(default, variant))
    assert all(v == "sell" for v, r in zip(variant, raw) if r == "sell")
    with pytest.raises(TimeoutError):
        replay.action_triplet(current, current, params, rows, 8, time.monotonic() - 1)


def test_input_and_output_guards(tmp_path):
    with pytest.raises(ValueError, match="legacy_source_changed"):
        replay.legacy_helpers({**CONTRACT, "legacy_sha256": "0" * 64})
    with pytest.raises(FileExistsError, match="output_must_be_new"):
        replay.run(tmp_path)
    helper = replay.legacy_helpers(CONTRACT)
    with pytest.raises(ValueError, match="saved_trade_count_mismatch"):
        replay.check_saved([trade()], {"trades": []}, bars([100, 100, 110]), helper)
    saved = {"trades": [{"ts_ms": replay.HOUR, "price": 100},
                         {"ts_ms": 0, "price": 110, "terminal": False, "net_quote_pnl": 9.475}]}
    with pytest.raises(ValueError, match="saved_exit_time_mismatch"):
        replay.check_saved([trade()], saved, bars([100, 100, 110]), helper)


@pytest.mark.parametrize("index,field,bad,reason", [
    (0, "side", "sell", "saved_trade_side_mismatch"),
    (1, "side", "buy", "saved_trade_side_mismatch"),
    (0, "qty", 999, "saved_trade_quantity_mismatch"),
    (1, "qty", 999, "saved_trade_quantity_mismatch"),
    (0, "fee", 999, "saved_entry_fee_mismatch"),
    (1, "fee", 999, "saved_exit_fee_mismatch"),
])
def test_saved_ledger_sides_quantities_and_fees(index, field, bad, reason):
    helpers = replay.legacy_helpers(CONTRACT)
    saved = {"trades": [
        {"ts_ms": replay.HOUR, "side": "buy", "qty": 1, "price": 100, "fee": 0.25},
        {"ts_ms": 2 * replay.HOUR, "side": "sell", "qty": 1, "price": 110, "fee": 0.275,
         "terminal": False, "net_quote_pnl": 9.475},
    ]}
    replay.check_saved([trade()], saved, bars([100, 100, 110]), helpers)
    saved["trades"][index][field] = bad
    with pytest.raises(ValueError, match=reason):
        replay.check_saved([trade()], saved, bars([100, 100, 110]), helpers)
