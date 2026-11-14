"""Approved retrospective contrast. No fetch, runtime configuration or trading."""
from __future__ import annotations

import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.backtest.next_open_research import validate_bars
from services.backtest.research_prefix_freeze import verify_prefix
from services.risk.exit_controls import evaluate_strategy_exit_stack

HERE = Path(__file__).resolve().parent
BEFORE = ROOT / "docs/review_artifacts/exit_unblocked_variants_20261114/before"
BASE = ROOT / "research/multisymbol_baseline_v1"
HOUR = 3600000
MODULES = {"breakout_default": "breakout_donchian", "ema_cross_default": "ema_cross",
           "mean_reversion_default": "mean_reversion_rsi"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_seals(path, root):
    seals = {}
    for line in path.read_text().splitlines():
        expected, relative = line.split(maxsplit=1)
        target = root / relative
        if sha(target) != expected:
            raise ValueError(f"source_seal_mismatch:{relative}")
        seals[relative] = expected
    return seals


def legacy_helpers(contract):
    """Reuse only reviewed function definitions; never execute the old experiment's top level."""
    path = HERE / "legacy_exit_parity_replay.py"
    if sha(path) != contract["legacy_sha256"]:
        raise ValueError("legacy_source_changed")
    names = {"path_points", "stack_check", "walk_bar", "simulate", "net_usd"}
    nodes = [node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise ValueError("missing_legacy_helper")
    namespace = {"math": math, "STACK": dict(contract["stack"]), "SLIP": contract["slippage_bps_per_side"] / 10000,
                 "NOTIONAL": contract["entry_notional_quote"], "evaluate_strategy_exit_stack": evaluate_strategy_exit_stack}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def before_module(filename):
    name = "services.strategies._historical_before_" + filename
    spec = importlib.util.spec_from_file_location(name, BEFORE / (filename + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def action_triplet(old, current, params, rows, start, deadline):
    old_actions, actions, variant, raw = (["hold"] * len(rows) for _ in range(4))
    for i in range(start - 1, len(rows) - 1):
        if time.monotonic() >= deadline:
            raise TimeoutError("historical_computation_deadline")
        window = rows[max(0, i - 299):i + 1]
        old_events, events, variant_events = [], [], []
        previous = old.signal_from_ohlcv(ohlcv=window, observer=old_events.append, **params)
        default = current.signal_from_ohlcv(ohlcv=window, observer=events.append, **params)
        treatment = current.signal_from_ohlcv(
            ohlcv=window, observer=variant_events.append, filters_apply_to_sell=False, **params)
        if previous != default or old_events != events:
            raise ValueError("historical_default_parity_failed")
        if not default.get("ok") or not treatment.get("ok") or len(events) != 1 or events != variant_events:
            raise ValueError("missing_or_changed_raw_signal")
        if default["ind"] != treatment["ind"]:
            raise ValueError("indicator_parity_failed")
        old_actions[i], actions[i], variant[i], raw[i] = (
            previous["action"], default["action"], treatment["action"], events[0]["raw_action"])
        if (actions[i] == "buy") != (variant[i] == "buy"):
            raise ValueError("buy_signal_changed")
        if raw[i] == "sell":
            if variant[i] != "sell":
                raise ValueError("variant_sell_still_filtered")
        elif default != treatment:
            raise ValueError("nonsell_signal_changed")
    return actions, variant, raw, len(rows) - start


def check_saved(trades, saved, rows, helpers):
    stored = saved["trades"]
    if len(stored) != 2 * len(trades):
        raise ValueError("saved_trade_count_mismatch")
    for k, trade in enumerate(trades):
        buy, sell = stored[2 * k:2 * k + 2]
        if buy["ts_ms"] != rows[trade["i"]][0] or not math.isclose(buy["price"], trade["entry_px"], rel_tol=1e-10):
            raise ValueError("saved_entry_mismatch")
        terminal = trade["exit_i"] == len(rows)
        exit_ts = rows[-1][0] + HOUR if terminal else rows[trade["exit_i"]][0]
        if sell["ts_ms"] != exit_ts or bool(sell.get("terminal")) != terminal:
            raise ValueError("saved_exit_time_mismatch")
        if buy.get("side") != "buy" or sell.get("side") != "sell":
            raise ValueError("saved_trade_side_mismatch")
        quantity = helpers["NOTIONAL"] / trade["entry_px"]
        if any(not math.isclose(row["qty"], quantity, rel_tol=1e-10, abs_tol=1e-12) for row in (buy, sell)):
            raise ValueError("saved_trade_quantity_mismatch")
        if not math.isclose(buy["fee"], helpers["NOTIONAL"] * 0.0025, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("saved_entry_fee_mismatch")
        if not math.isclose(sell["fee"], quantity * trade["exit_px"] * 0.0025, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("saved_exit_fee_mismatch")
        if not math.isclose(sell["price"], trade["exit_px"], rel_tol=1e-10):
            raise ValueError("saved_exit_mismatch")
        if not math.isclose(sell["net_quote_pnl"], helpers["net_usd"](trade, 0.0025), abs_tol=1e-6):
            raise ValueError("saved_net_pnl_mismatch")


def account_metrics(rows, trades, start, fee, actions, raw, contract):
    """Close-marked independent sleeve; use actual modeled quantity, not exit-price ratios."""
    initial = contract["initial_cash_per_symbol_quote"]
    notional = contract["entry_notional_quote"]
    cash, peak, dd, minimum_cash = initial, initial, 0.0, initial
    entries = {t["i"]: t for t in trades}
    exits = {t["exit_i"]: t for t in trades}
    if len(entries) != len(trades) or len(exits) != len(trades):
        raise ValueError("overlapping_or_duplicate_trade")
    active, fees, gross_pnl, blocked = None, 0.0, 0.0, 0
    curve = []
    for i in range(start, len(rows) + 1):
        if i in entries:
            if active is not None or cash + 1e-8 < notional * (1 + fee):
                raise ValueError("fixed_notional_unaffordable_or_overlapping")
            active = entries[i]
            cash -= notional * (1 + fee)
            fees += notional * fee
            minimum_cash = min(minimum_cash, cash)
        if i in exits:
            trade = exits[i]
            if active is not trade:
                raise ValueError("unmatched_exit")
            proceeds = notional / trade["entry_px"] * trade["exit_px"]
            cash += proceeds * (1 - fee)
            fees += proceeds * fee
            gross_pnl += proceeds - notional
            active = None
        value = cash if active is None else cash + notional / active["entry_px"] * rows[i][4]
        peak = max(peak, value)
        dd = max(dd, peak - value)
        curve.append(value)
        if i < len(rows) and active is not None and raw[i] == "sell" and actions[i] == "hold":
            blocked += 1
    if active is not None or not math.isclose(cash - initial, gross_pnl - fees, abs_tol=1e-7):
        raise ValueError("account_reconciliation_failed")
    n = len(rows) - start
    lower = sum(t["exit_i"] - t["i"] for t in trades) / n
    upper = sum(min(len(rows), t["exit_i"] + 1) - t["i"] for t in trades) / n
    return {"trades": len(trades), "net_quote": cash - initial, "before_fee_after_slippage_quote": gross_pnl,
            "fees_quote": fees, "terminal_cash_quote": cash, "minimum_cash_quote": minimum_cash,
            "bar_close_mtm_max_drawdown_quote": dd, "blocked_sell_signal_bars_while_held": blocked,
            "exposure_lower_bar_fraction": lower, "exposure_upper_bar_fraction": upper,
            "positive_trades": sum(notional / t["entry_px"] * t["exit_px"] * (1 - fee) > notional * (1 + fee) for t in trades)}


def run(output):
    contract = json.loads((HERE / "replay_contract.json").read_text())
    if output.exists():
        raise FileExistsError("output_must_be_new")
    pins = dict(contract["input_sha256"])
    pins.update({"docs/research/exit_variants_spec_20261114/" + name: sha(HERE / name)
                 for name in ("replay_contract.json", "replay_exit_variants.py", "legacy_exit_parity_replay.py")})
    pins.update({name: sha(ROOT / name) for name in (
        "services/risk/exit_controls.py", "services/backtest/next_open_research.py",
        "services/backtest/research_prefix_freeze.py", "tests/test_exit_variants_replay.py")})
    pins.update(read_seals(ROOT / "docs/review_artifacts/exit_unblocked_variants_20261114/SOURCE_SHA256SUMS", ROOT))
    before = read_seals(BEFORE / "SHA256SUMS", BEFORE)
    pins.update({str((BEFORE / name).relative_to(ROOT)): value for name, value in before.items()})
    for name, expected in pins.items():
        if sha(ROOT / name) != expected:
            raise ValueError("input_pin_mismatch:" + name)
    helpers = legacy_helpers(contract)
    snapshot = json.loads((BASE / "strategies.snapshot.json").read_text())
    freeze = json.loads((BASE / "dataset.freeze.json").read_text())
    final = json.loads((BASE / "final_20261008.json").read_text())
    deadline = time.monotonic() + contract["historical_replay_max_seconds"]
    result = {"contract": contract, "pins": pins, "qualification": contract["qualification"], "cases": [], "parity": []}
    csv_rows = []
    with sqlite3.connect((BASE / "public_archive.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        for symbol in contract["symbols"]:
            rows = [list(row) for row in db.execute(
                "SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange='okx' AND symbol=? AND timeframe='1h' ORDER BY ts_ms",
                (symbol,)).fetchall()]
            validate_bars(rows, interval_ms=HOUR)
            verify_prefix(freeze, symbol=symbol, phase="final", rows=rows,
                          plan_sha256=contract["input_sha256"]["research/multisymbol_baseline_v1/plan.json"],
                          snapshot_sha256=contract["input_sha256"]["research/multisymbol_baseline_v1/strategies.snapshot.json"])
            start = contract["warmup_bars"]
            if rows[start][0] != 1767225600000 or rows[-1][0] + HOUR != 1790812800000:
                raise ValueError("evaluation_date_mismatch")
            for strategy in contract["strategies"]:
                filename = MODULES[strategy]
                current = importlib.import_module("services.strategies." + filename)
                params = {k: v for k, v in snapshot["strategies"][strategy].items() if k not in {"name", "trade_enabled"}}
                default, variant, raw, compared = action_triplet(before_module(filename), current, params, rows, start, deadline)
                for arm in ("S", "R"):
                    for variant_name, actions in (("default", default), ("unblocked", variant)):
                        trades = helpers["simulate"](rows, actions, start, sid=snapshot["strategies"][strategy]["name"], **contract[arm])
                        if arm == "S" and variant_name == "default":
                            check_saved(trades, final["markets"][symbol]["results"][strategy]["25"], rows, helpers)
                        for bps in contract["fee_bps_per_side"]:
                            metrics = account_metrics(rows, trades, start, bps / 10000, actions, raw, contract)
                            result["cases"].append(dict(symbol=symbol, strategy=strategy, arm=arm, variant=variant_name, fee_bps=bps, **metrics))
                            for trade in trades:
                                csv_rows.append(dict(symbol=symbol, strategy=strategy, arm=arm, variant=variant_name, fee_bps=bps,
                                                     entry_ts_ms=rows[trade["i"]][0],
                                                     exit_bar_ts_ms=rows[trade["exit_i"]][0] if trade["exit_i"] < len(rows) else rows[-1][0] + HOUR,
                                                     entry_px=trade["entry_px"], exit_px=trade["exit_px"],
                                                     qty=contract["entry_notional_quote"] / trade["entry_px"],
                                                     net_quote=helpers["net_usd"](trade, bps / 10000), exit_rule=trade["rule"]))
                result["parity"].append(dict(symbol=symbol, strategy=strategy, prefixes=compared, default_full_output_equal=True,
                                             buy_signals_equal=True, variant_filtered_raw_sells=0, saved_S_trades_equal=True))
                print(json.dumps({"completed": symbol + "|" + strategy, "prefixes": compared}), flush=True)
    for name, expected in pins.items():
        if sha(ROOT / name) != expected:
            raise ValueError("input_changed_during_run:" + name)
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    output.mkdir()
    with (output / "exit_variants_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    with (output / "trades.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    with (output / "SHA256SUMS").open("x") as stream:
        for name in ("exit_variants_result.json", "trades.csv"):
            stream.write(f"{sha(output / name)}  {name}\n")


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())
