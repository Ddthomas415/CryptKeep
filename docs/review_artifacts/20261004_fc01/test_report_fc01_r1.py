import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("fc01_report", Path(__file__).with_name("report_fc01_r1.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_flat_price_fees_both_legs():
    result = module.trade([1, "", 100, 100], [2, "", 100, 100])
    assert result["net_usd"] == -1
    assert result["midpoint_bps"] == 0


def test_spread_not_deducted_twice():
    result = module.trade([1, "", 99, 100], [2, "", 99, 100])
    assert result["net_usd"] == pytest.approx(-1.995)
    assert result["midpoint_bps"] == 0


def test_exit_fee_uses_exit_notional():
    result = module.trade([1, "", 100, 100], [2, "", 110, 110])
    assert result["fees_usd"] == pytest.approx(1.05)
    assert result["net_usd"] == pytest.approx(8.95)


def test_changed_inputs_refused():
    with pytest.raises(ValueError, match="changed"):
        module.report({"inputs": {}, "input_content_sha256": module.EXPECTED_INPUT_HASH})


def test_bootstrap_constant_and_reproducible():
    result = module.bootstrap([[4, 4, -4]] * 10, 1)
    assert result["incremental_bps_per_window_ci95"] == [100, 100]
    assert result["absolute_bps_per_window_ci95"] == [-100, -100]
    assert result == module.bootstrap([[4, 4, -4]] * 10, 1)
