import pytest

from scripts.research.corrected_research_math import (
    corrected_event_exit, corrected_forward, gap_aware_stop, paired_block_sharpe, purged_training, rebalance,
)


def test_gap_beyond_stop_is_not_capped():
    assert gap_aware_stop(100, 95, 80, 75) == pytest.approx(-.2)
    assert gap_aware_stop(100, 95, 100, 94) == pytest.approx(-.05)
    assert gap_aware_stop(100, 95, 100, 96) is None


def test_boundary_labels_are_purged():
    assert purged_training([(1, 9), (2, 10), (3, 12), (11, 13)], 10) == [(1, 9)]


def test_full_allocation_pays_buy_and_sell_costs():
    cash, units = rebalance(1000, {}, {"BTC": 100}, {"BTC": 1}, .005, .001)
    assert cash == 0
    assert units["BTC"] == pytest.approx(1000 / (100 * 1.001 * 1.005))
    cash, units = rebalance(cash, units, {"BTC": 100}, {}, .005, .001)
    assert cash == pytest.approx(1000 * .999 * .995 / (1.001 * 1.005))
    assert units["BTC"] == 0


def test_paired_blocks_preserve_identical_paths():
    values = [.02, -.01, .003] * 30
    result = paired_block_sharpe(values, values, block=7, repeats=30)
    assert result["observed"] == result["p05"] == result["p95"] == 0


@pytest.mark.parametrize("left,right", [([.1], [.2]), ([.1] * 60, [.2] * 59),
                                       ([float("nan")] * 60, [.1] * 60)])
def test_invalid_bootstrap_inputs_fail(left, right):
    with pytest.raises(ValueError):
        paired_block_sharpe(left, right)


def test_event_entry_next_open_and_gap_stop():
    rows = [[0, 100, 100, 100, 100, 1], [3600, 110, 112, 109, 111, 1],
            [7200, 80, 85, 75, 82, 1]]
    result = corrected_event_exit(rows, 0, None, .05, 24)
    assert result[0] == pytest.approx(80 / 110 - 1)


def test_missing_or_immature_event_not_given_a_return():
    rows = [[0, 100, 100, 100, 100, 1], [3600, 110, 112, 109, 111, 1]]
    assert corrected_forward(rows, 0, 24) is None
    rows.append([10800, 110, 112, 109, 111, 1])
    assert corrected_forward(rows, 0, 1) is None


def test_event_wrapper_handles_incomplete_label_before_subscript():
    import ast
    from scripts.research.rerun_frozen_events import Corrections, event_return

    tree = ast.parse("def run_events():\n for i in [0]:\n  g = simulate_exit([], i, None, None, 24)[0]\n  return g\n return 'missing'\n")
    tree = ast.fix_missing_locations(Corrections(.005).visit(tree))
    namespace = {"event_return": event_return}
    exec(compile(tree, "probe", "exec"), namespace)
    assert namespace["run_events"]() == "missing"
def test_bootstrap_constant_resamples_report_incomplete():
    from scripts.research.corrected_research_math import paired_block_sharpe

    result = paired_block_sharpe([0.0] * 59 + [0.01], [-0.001, 0.001] * 30)
    assert result["status"] == "INCOMPLETE"
    assert result["undefined_replicates"] > 0
    assert result["p05"] is None and result["p95"] is None
