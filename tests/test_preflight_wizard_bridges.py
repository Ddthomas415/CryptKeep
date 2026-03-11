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

def test_wizard_guided_setup_page_data_splits_state(monkeypatch):
    monkeypatch.setattr(
        pw,
        "wizard_guided_setup_state",
        lambda: {
            "summary": {"exchange": "kraken", "symbol_count": 2},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.wizard_guided_setup_page_data()

    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
        "status": {"config_ok": True},
    }


def test_render_guided_setup_panel_populates_ui_dict(monkeypatch):
    ui = {}

    monkeypatch.setattr(
        pw,
        "wizard_guided_setup_page_data",
        lambda: {
            "summary": {"exchange": "kraken", "symbol_count": 2},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.render_guided_setup_panel(ui)

    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
        "status": {"config_ok": True},
    }
    assert ui["summary"]["exchange"] == "kraken"
    assert ui["preflight"]["ok"] is True
    assert ui["status"]["config_ok"] is True


def test_render_guided_setup_panel_apply_preset_action(monkeypatch):
    ui = {"action": "apply_preset", "preset": "live_locked"}

    captured = {}

    def _apply_preset_state(preset):
        captured["preset"] = preset
        return {
            "summary": {"exchange": "kraken", "symbol_count": 1},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        }

    monkeypatch.setattr(pw, "wizard_guided_setup_apply_preset_state", _apply_preset_state)

    out = pw.render_guided_setup_panel(ui)

    assert captured["preset"] == "live_locked"
    assert out["summary"]["exchange"] == "kraken"
    assert ui["last_action"] == "apply_preset"
    assert ui["preflight"]["ok"] is True


def test_render_guided_setup_panel_apply_patch_action(monkeypatch):
    ui = {
        "action": "apply_patch",
        "patch": {
            "symbols": ["ETH/USD", "BTC/USD"],
            "pipeline": {"exchange_id": "kraken"},
        },
    }

    captured = {}

    def _apply_state(patch=None):
        captured["patch"] = patch
        return {
            "summary": {"exchange": "kraken", "symbol_count": 2},
            "preflight": {"ok": False, "ready": False},
            "status": {"config_ok": False},
        }

    monkeypatch.setattr(pw, "wizard_guided_setup_apply_state", _apply_state)

    out = pw.render_guided_setup_panel(ui)

    assert captured["patch"] == {
        "symbols": ["ETH/USD", "BTC/USD"],
        "pipeline": {"exchange_id": "kraken"},
    }
    assert out["summary"]["symbol_count"] == 2
    assert ui["last_action"] == "apply_patch"
    assert ui["status"]["config_ok"] is False


def test_render_guided_setup_panel_refresh_action(monkeypatch):
    ui = {"action": "refresh"}

    monkeypatch.setattr(
        pw,
        "wizard_guided_setup_page_data",
        lambda: {
            "summary": {"exchange": "coinbase", "symbol_count": 1},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.render_guided_setup_panel(ui)

    assert out["summary"]["exchange"] == "coinbase"
    assert ui["last_action"] == "refresh"
    assert ui["preflight"]["ok"] is True
    assert ui["status"]["config_ok"] is True


def test_render_guided_setup_panel_default_load_action(monkeypatch):
    ui = {}

    monkeypatch.setattr(
        pw,
        "wizard_guided_setup_page_data",
        lambda: {
            "summary": {"exchange": "coinbase", "symbol_count": 1},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = pw.render_guided_setup_panel(ui)

    assert out["summary"]["exchange"] == "coinbase"
    assert ui["summary"]["symbol_count"] == 1
    assert ui["preflight"]["ok"] is True
    assert ui["status"]["config_ok"] is True
    assert ui["last_action"] == "load"

