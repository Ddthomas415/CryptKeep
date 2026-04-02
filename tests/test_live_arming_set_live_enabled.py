from services.execution.live_arming import set_live_enabled


def test_set_live_enabled_normalizes_all_live_enabled_shapes():
    cfg = {
        "live": {"enabled": False},
        "live_trading": {"enabled": False},
        "risk": {"enable_live": False},
        "execution": {"live_enabled": False},
    }

    out = set_live_enabled(cfg, True)

    assert out["execution"]["live_enabled"] is True
    assert out["live"]["enabled"] is True
    assert out["live_trading"]["enabled"] is True
    assert out["risk"]["enable_live"] is True
