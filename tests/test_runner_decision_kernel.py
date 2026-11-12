"""Compare the extraction with the saved pre-refactor runner, not a second model."""
import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from services.execution.runner_decision import select_exit_decision, signal_transition
from services.risk.exit_controls import evaluate_strategy_exit_stack


@pytest.fixture(scope="module")
def original_exit_selection():
    root = Path(__file__).resolve().parents[1]
    evidence = root / "docs/review_artifacts/paper_simulation_r6r9_20261103"
    raw = (evidence / "services__execution__strategy_runner.py.before").read_bytes()
    hashes = json.loads((evidence / "baseline_hashes.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == hashes["services/execution/strategy_runner.py"]
    tree = ast.parse(raw)
    body = None
    for parent in ast.walk(tree):
        statements = getattr(parent, "body", None)
        if not isinstance(statements, list):
            continue
        for i, node in enumerate(statements):
            if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "exit_action" and isinstance(node.value, ast.Constant)
                    and node.value.value is None):
                end = next(j for j in range(i + 1, len(statements))
                           if isinstance(statements[j], ast.Assign)
                           and isinstance(statements[j].targets[0], ast.Name)
                           and statements[j].targets[0].id == "kill_remaining")
                body = copy.deepcopy(statements[i:end])
                break
    assert body is not None
    wrapper = ast.parse("def original(cfg, signal, decision, changed, pos_qty, entry_price, trailing_peak_price, bars_held, m):\n action = None\n note = None\n").body[0]
    wrapper.body += body + ast.parse("return dict(action=action, changed=bool(changed), exit_action=exit_action, exit_reason=exit_reason, exit_out=exit_out)").body
    namespace = {"evaluate_strategy_exit_stack": evaluate_strategy_exit_stack}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[])), "<frozen-runner-exit-block>", "exec"), namespace)
    return namespace["original"]


def test_exit_extraction_matches_frozen_runner(original_exit_selection):
    for strategy, qty, entry, price, peak, bars, decision, changed in itertools.product(
        ("ema_cross", "breakout_donchian", "mean_reversion_rsi", "sma_200_trend"),
        (0.0, 1.0), (0.0, 100.0), (90.0, 100.0, 110.0), (100.0, 120.0),
        (0, 60), ("buy", "sell", "hold"), (False, True),
    ):
        cfg = dict(strategy_id=strategy, position_aware=True, stop_loss_pct=.03,
                   trailing_stop_pct=.02, take_profit_pct=.06, max_bars_hold=60,
                   min_volatility_pct=.01, min_trend_efficiency=.1, min_cross_gap_pct=.1)
        signal = {"action": decision, "ind": {"avg_range_pct": 0, "trend_efficiency": 0, "cross_gap_pct": 0}}
        args = dict(cfg=cfg, signal=signal, decision=decision, changed=changed,
                    pos_qty=qty, entry_price=entry, trailing_peak_price=peak, bars_held=bars)
        expected = original_exit_selection(**args, m=price)
        actual = select_exit_decision(**args, current_price=price)
        assert {key: actual[key] for key in expected} == expected


@pytest.mark.parametrize("warmed,last_action,decision,allow", list(itertools.product(
    (False, True), ("buy", "sell", "hold"), ("buy", "sell", "hold"), (False, True))))
def test_transition_matches_original_contract(warmed, last_action, decision, allow):
    result = signal_transition(strategy_id="breakout_donchian", decision=decision,
                               pos_qty=1, warmed=warmed, last_action=last_action,
                               allow_first_signal_trade=allow)
    expected_changed = decision != last_action if warmed else decision in ("buy", "sell") and allow
    assert result["changed"] == expected_changed
    assert result["last_action"] == (decision if not warmed or expected_changed else last_action)
    assert result["write_warm"] is (not warmed)


def test_all_competing_exit_predicates_not_just_chosen_one():
    result = select_exit_decision(
        cfg=dict(strategy_id="breakout_donchian", position_aware=True, stop_loss_pct=.03,
                 trailing_stop_pct=.02, take_profit_pct=.06, max_bars_hold=60),
        signal={"action": "sell"}, raw_signal={"raw_action": "sell"},
        decision="sell", changed=True, pos_qty=1, entry_price=100,
        current_price=90, trailing_peak_price=120, bars_held=60, observe=True)
    assert result["exit_out"]["stack_rule"] == "stop_loss"
    assert result["conditions"] == dict(stop=True, trailing=True, take_profit=False,
                                         time=True, strategy_sell=True, pre_filter_sell=True)


def test_ema_invalidation_keeps_existing_priority():
    result = select_exit_decision(
        cfg=dict(strategy_id="ema_cross", position_aware=True, stop_loss_pct=.03,
                 min_volatility_pct=1, min_trend_efficiency=1, min_cross_gap_pct=1),
        signal={"action": "sell", "ind": {}}, decision="sell", changed=True,
        pos_qty=1, entry_price=100, current_price=90, trailing_peak_price=120,
        bars_held=60, observe=True)
    assert result["exit_reason"] == "strategy_exit:ema_cross:low_volatility_invalidation"
    assert result["conditions"]["stop"]
    assert all(result["conditions"][key] for key in ("ema_low_vol", "ema_chop", "ema_cross_gap"))


def test_observation_failure_does_not_change_core_short_circuit(original_exit_selection):
    cfg = dict(strategy_id="ema_cross", position_aware=True, min_volatility_pct=1,
               stop_loss_pct="not-numeric")
    args = dict(cfg=cfg, signal={"action": "sell", "ind": {}}, decision="sell",
                changed=True, pos_qty=1, entry_price=100, trailing_peak_price=100, bars_held=0)
    expected = original_exit_selection(**args, m=90)
    actual = select_exit_decision(**args, current_price=90)
    assert actual["exit_reason"] == expected["exit_reason"]
    with pytest.raises(ValueError):
        select_exit_decision(**args, current_price=90, observe=True)
