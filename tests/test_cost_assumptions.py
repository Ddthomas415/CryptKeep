from __future__ import annotations

import json

from services.analytics import cost_assumptions as ca


def _by_name(report: dict, name: str) -> dict:
    return next(item for item in report["checks"] if item["name"] == name)


def test_configured_plausible_costs_are_ok_when_surfaces_match(monkeypatch):
    monkeypatch.setattr(ca, "evidence_service_cost_defaults", lambda: {"fee_bps": 7.5, "slippage_bps": 5.0, "derivable": True})
    monkeypatch.setattr(ca, "backtest_cost_defaults", lambda: {"fee_bps": 7.5, "slippage_bps": 5.0, "derivable": True})

    report = ca.evaluate_cost_assumptions(
        {"paper_trading": {"fee_bps": 7.5, "slippage_bps": 5.0}, "execution": {"paper_fee_bps": 7.5}}
    )

    assert report["overall"] == ca.OK
    assert report["round_trip_bps"] == 25.0
    assert _by_name(report, "engine_costs_configured")["status"] == ca.OK
    assert _by_name(report, "round_trip_plausible")["status"] == ca.OK


def test_code_defaults_warn_not_fail():
    report = ca.evaluate_cost_assumptions({})

    assert report["overall"] == ca.WARN
    assert report["surfaces"]["paper_engine"]["fee_status"] == "missing"
    assert report["surfaces"]["paper_engine"]["slippage_status"] == "missing"
    assert _by_name(report, "engine_costs_configured")["status"] == ca.WARN
    assert _by_name(report, "round_trip_plausible")["status"] == ca.OK


def test_invalid_or_nonfinite_engine_costs_fail():
    for bad in ("nan", "inf", "-inf", "garbage"):
        report = ca.evaluate_cost_assumptions({"paper_trading": {"fee_bps": bad, "slippage_bps": 5.0}})
        assert report["overall"] == ca.FAIL
        assert _by_name(report, "engine_costs_valid")["status"] == ca.FAIL


def test_negative_engine_costs_fail():
    report = ca.evaluate_cost_assumptions({"paper_trading": {"fee_bps": -1.0, "slippage_bps": 5.0}})

    assert report["overall"] == ca.FAIL
    assert _by_name(report, "engine_costs_valid")["status"] == ca.FAIL


def test_implausible_round_trip_fails():
    report = ca.evaluate_cost_assumptions(
        {"paper_trading": {"fee_bps": 0.0, "slippage_bps": 0.0}, "execution": {"paper_fee_bps": 0.0}}
    )

    assert report["overall"] == ca.FAIL
    assert _by_name(report, "round_trip_plausible")["status"] == ca.FAIL
    assert "segment historical evidence" in report["interpretation"]


def test_policy_floor_is_configurable(monkeypatch):
    monkeypatch.setenv("CBP_MIN_PLAUSIBLE_ROUND_TRIP_BPS", "40")

    report = ca.evaluate_cost_assumptions(
        {"paper_trading": {"fee_bps": 7.5, "slippage_bps": 5.0}, "execution": {"paper_fee_bps": 7.5}}
    )

    assert report["policy_floor_bps"] == 40.0
    assert _by_name(report, "round_trip_plausible")["status"] == ca.FAIL


def test_bad_policy_floor_falls_back(monkeypatch):
    monkeypatch.setenv("CBP_MIN_PLAUSIBLE_ROUND_TRIP_BPS", "not-a-number")

    assert ca.min_plausible_round_trip_bps() == ca.DEFAULT_MIN_PLAUSIBLE_ROUND_TRIP_BPS


def test_zero_fee_and_slippage_are_operator_warnings_when_round_trip_is_plausible():
    report = ca.evaluate_cost_assumptions({"paper_trading": {"fee_bps": 0.0, "slippage_bps": 5.0}})

    assert _by_name(report, "round_trip_plausible")["status"] == ca.OK
    assert _by_name(report, "fee_modeled")["status"] == ca.WARN

    report = ca.evaluate_cost_assumptions({"paper_trading": {"fee_bps": 7.5, "slippage_bps": 0.0}})
    assert _by_name(report, "slippage_modeled")["status"] == ca.WARN


def test_unreadable_config_is_own_state(monkeypatch):
    import services.admin.config_editor as config_editor

    def _boom(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(config_editor, "load_user_yaml", _boom)

    report = ca.check_cost_assumptions()

    assert report["overall"] == ca.CONFIG_UNREADABLE
    assert report["overall"] not in {ca.OK, ca.WARN, ca.FAIL}
    assert "not verified" in report["interpretation"]


def test_backtest_cost_surface_is_derived_and_scoped():
    report = ca.evaluate_cost_assumptions(
        {"paper_trading": {"fee_bps": 7.5, "slippage_bps": 5.0}, "execution": {"paper_fee_bps": 7.5}}
    )

    check = _by_name(report, "backtest_cost_surface")
    assert check["status"] == ca.WARN
    assert "walk_forward defaults fee=10.0, slippage=5.0" in check["detail"]
    assert "does not verify archive-sweep cost policy" in check["detail"]
    assert report["surfaces"]["backtest_walk_forward"]["derivable"] is True


def test_cli_outputs_json(monkeypatch, capsys):
    from scripts.check_cost_assumptions import main

    monkeypatch.setattr(
        "scripts.check_cost_assumptions.check_cost_assumptions",
        lambda: {
            "overall": ca.WARN,
            "round_trip_bps": 25.0,
            "policy_floor_bps": 5.0,
            "surfaces": {},
            "checks": [],
            "interpretation": "warn",
        },
    )

    assert main(["--json"]) == 1
    assert json.loads(capsys.readouterr().out)["overall"] == ca.WARN
