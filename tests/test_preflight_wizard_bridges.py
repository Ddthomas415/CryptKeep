from services.app import preflight_wizard as pw


def test_wizard_guided_setup_state_delegates(monkeypatch):
    monkeypatch.setattr(
        pw,
        "guided_setup_state",
        lambda: {
            "summary": {"exchange": "kraken"},
            "preflight": {"ok": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.wizard_guided_setup_state()

    assert out == {
        "summary": {"exchange": "kraken"},
        "preflight": {"ok": True},
        "status": {"config_ok": True},
    }


def test_wizard_guided_setup_apply_state_delegates(monkeypatch):
    captured = {}

    def _guided_setup_apply_state(patch=None):
        captured["patch"] = patch
        return {
            "summary": {"exchange": "coinbase"},
            "preflight": {"ok": False},
            "status": {"config_ok": False},
        }

    monkeypatch.setattr(pw, "guided_setup_apply_state", _guided_setup_apply_state)

    out = pw.wizard_guided_setup_apply_state(
        {"symbols": ["BTC/USD"], "pipeline": {"exchange_id": "coinbase"}}
    )

    assert captured["patch"] == {
        "symbols": ["BTC/USD"],
        "pipeline": {"exchange_id": "coinbase"},
    }
    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False
    assert out["status"]["config_ok"] is False


def test_wizard_guided_setup_apply_preset_delegates(monkeypatch):
    captured = {}

    def _guided_setup_apply_preset(preset):
        captured["preset"] = preset
        return {"summary": {"exchange": "kraken"}, "preflight": {"ok": True}}

    monkeypatch.setattr(pw, "guided_setup_apply_preset", _guided_setup_apply_preset)

    out = pw.wizard_guided_setup_apply_preset("live_locked")

    assert captured["preset"] == "live_locked"
    assert out == {"summary": {"exchange": "kraken"}, "preflight": {"ok": True}}


def test_wizard_guided_setup_apply_preset_state_delegates(monkeypatch):
    calls = []

    monkeypatch.setattr(
        pw,
        "guided_setup_apply_preset",
        lambda preset: calls.append(("preset", preset)),
    )
    monkeypatch.setattr(
        pw,
        "guided_setup_state",
        lambda: {
            "summary": {"exchange": "kraken", "symbol_count": 1},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.wizard_guided_setup_apply_preset_state("safe_paper")

    assert calls == [("preset", "safe_paper")]
    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 1},
        "preflight": {"ok": True, "ready": True},
        "status": {"config_ok": True},
    }
