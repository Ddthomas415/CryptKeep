from services.execution.live_arming import is_live_enabled


def test_is_live_enabled_prefers_execution_live_enabled_true_over_false_legacy():
    cfg = {
        "execution": {"live_enabled": True},
        "live": {"enabled": False},
        "live_trading": {"enabled": False},
        "risk": {"enable_live": False},
    }
    assert is_live_enabled(cfg) is True


def test_is_live_enabled_prefers_execution_live_enabled_false_over_true_legacy():
    cfg = {
        "execution": {"live_enabled": False},
        "live": {"enabled": True},
        "live_trading": {"enabled": True},
        "risk": {"enable_live": True},
    }
    assert is_live_enabled(cfg) is False


def test_is_live_enabled_falls_back_when_execution_live_enabled_absent():
    cfg = {
        "live": {"enabled": False},
        "live_trading": {"enabled": False},
        "risk": {"enable_live": True},
    }
    assert is_live_enabled(cfg) is True
