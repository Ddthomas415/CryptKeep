from __future__ import annotations

import json

from scripts import restore_paper_campaigns as script


def test_restore_paper_campaigns_defaults_to_read_only_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "load_campaign_specs", lambda *args, **kwargs: ("spec",))
    monkeypatch.setattr(
        script,
        "manage_campaigns",
        lambda specs, restore, selected_names: {
            "ok": True,
            "action": "restore" if restore else "status",
            "all_running": True,
            "campaigns": [],
        },
    )

    assert script.main([]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["action"] == "status"


def test_restore_paper_campaigns_forwards_restore_and_selection(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}
    monkeypatch.setattr(script, "load_campaign_specs", lambda *args, **kwargs: ("spec",))

    def _manage(specs, *, restore, selected_names):
        seen["specs"] = specs
        seen["restore"] = restore
        seen["selected_names"] = selected_names
        return {"ok": True, "action": "restore", "all_running": True, "campaigns": []}

    monkeypatch.setattr(script, "manage_campaigns", _manage)

    assert script.main(["--restore", "--campaign", "ema_cross_default"]) == 0
    json.loads(capsys.readouterr().out)
    assert seen == {
        "specs": ("spec",),
        "restore": True,
        "selected_names": ["ema_cross_default"],
    }


def test_restore_paper_campaigns_fails_closed_on_invalid_config(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "load_campaign_specs",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad config")),
    )

    assert script.main(["--restore"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["reason"] == "invalid_campaign_config:ValueError"
