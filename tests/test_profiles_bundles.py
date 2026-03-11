from __future__ import annotations

from services.profiles import bundles


def test_list_and_get_bundle_returns_copy():
    names = bundles.list_bundles()
    assert "STRAT_MEAN_REVERSION_5M" in names

    b1 = bundles.get_bundle("STRAT_MEAN_REVERSION_5M")
    assert b1 is not None
    b1["runtime"]["mode"] = "live"

    b2 = bundles.get_bundle("STRAT_MEAN_REVERSION_5M")
    assert b2 is not None
    assert b2["runtime"]["mode"] == "paper"


def test_merge_bundle_applies_overrides():
    base = {"risk": {"max_order_quote": 11.0}, "strategy": {"name": "noop"}}
    out = bundles.merge_bundle(
        base,
        "STRAT_BREAKOUT_5M",
        overrides={"risk": {"max_order_quote": 33.0}, "strategy": {"trade_enabled": False}},
    )

    assert out["runtime"]["mode"] == "paper"
    assert out["risk"]["max_order_quote"] == 33.0
    assert out["strategy"]["name"] == "breakout_donchian"
    assert out["strategy"]["trade_enabled"] is False


def test_register_bundle_validation():
    created = bundles.register_bundle("TEST_BUNDLE_X", {"runtime": {"mode": "paper"}}, replace=True)
    assert created["runtime"]["mode"] == "paper"

    try:
        bundles.register_bundle("TEST_BUNDLE_X", {"runtime": {"mode": "live"}}, replace=False)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError when replacing without replace=True")
