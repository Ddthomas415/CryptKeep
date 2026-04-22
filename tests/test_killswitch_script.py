from __future__ import annotations

import json

from scripts import killswitch as script


def test_killswitch_status_uses_admin_state(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["killswitch.py", "--status"])
    monkeypatch.setattr(
        script,
        "get_state",
        lambda: {"armed": True, "note": "manual", "ts": "2026-04-18T00:00:00Z"},
    )
    monkeypatch.setattr(
        script,
        "set_armed",
        lambda state, note="": (_ for _ in ()).throw(AssertionError("should not mutate")),
    )

    out = script.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["killswitch"] is True
    assert payload["state"]["armed"] is True


def test_killswitch_arm_sets_admin_state(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["killswitch.py", "--arm"])
    calls: list[tuple[bool, str]] = []
    monkeypatch.setattr(script, "get_state", lambda: (_ for _ in ()).throw(AssertionError("should not read state")))

    def _set_armed(state: bool, note: str = "") -> dict:
        calls.append((bool(state), str(note)))
        return {"armed": bool(state), "note": str(note), "ts": "2026-04-18T00:00:00Z"}

    monkeypatch.setattr(script, "set_armed", _set_armed)

    out = script.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls == [(True, "scripts.killswitch:arm")]
    assert payload["killswitch"] is True
    assert payload["state"]["armed"] is True


def test_killswitch_disarm_sets_admin_state(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["killswitch.py", "--disarm"])
    calls: list[tuple[bool, str]] = []
    monkeypatch.setattr(script, "get_state", lambda: (_ for _ in ()).throw(AssertionError("should not read state")))

    def _set_armed(state: bool, note: str = "") -> dict:
        calls.append((bool(state), str(note)))
        return {"armed": bool(state), "note": str(note), "ts": "2026-04-18T00:00:00Z"}

    monkeypatch.setattr(script, "set_armed", _set_armed)

    out = script.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls == [(False, "scripts.killswitch:disarm")]
    assert payload["killswitch"] is False
    assert payload["state"]["armed"] is False


def test_killswitch_legacy_on_alias_maps_to_arm(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["killswitch.py", "--on"])
    calls: list[tuple[bool, str]] = []
    monkeypatch.setattr(script, "get_state", lambda: (_ for _ in ()).throw(AssertionError("should not read state")))

    def _set_armed(state: bool, note: str = "") -> dict:
        calls.append((bool(state), str(note)))
        return {"armed": bool(state), "note": str(note), "ts": "2026-04-18T00:00:00Z"}

    monkeypatch.setattr(script, "set_armed", _set_armed)

    out = script.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls == [(True, "scripts.killswitch:arm")]
    assert payload["killswitch"] is True


def test_killswitch_legacy_off_alias_maps_to_disarm(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script.sys, "argv", ["killswitch.py", "--off"])
    calls: list[tuple[bool, str]] = []
    monkeypatch.setattr(script, "get_state", lambda: (_ for _ in ()).throw(AssertionError("should not read state")))

    def _set_armed(state: bool, note: str = "") -> dict:
        calls.append((bool(state), str(note)))
        return {"armed": bool(state), "note": str(note), "ts": "2026-04-18T00:00:00Z"}

    monkeypatch.setattr(script, "set_armed", _set_armed)

    out = script.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert calls == [(False, "scripts.killswitch:disarm")]
    assert payload["killswitch"] is False
