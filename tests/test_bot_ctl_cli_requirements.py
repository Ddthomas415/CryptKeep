from unittest.mock import patch
import pytest
import scripts.bot_ctl as bot_ctl


def test_bot_ctl_start_requires_venue_and_symbols():
    with patch("sys.argv", ["bot_ctl.py", "start"]):
        with pytest.raises(SystemExit) as exc:
            bot_ctl.main()
    assert exc.value.code == 2


def test_bot_ctl_start_accepts_explicit_venue_and_symbols(monkeypatch, tmp_path):
    monkeypatch.setattr(bot_ctl, "_load_state", lambda: {})
    monkeypatch.setattr(bot_ctl, "ensure_dirs", lambda: None)

    monkeypatch.setattr(bot_ctl, "LOG_PATH", tmp_path / "dummy.log")
    monkeypatch.setattr(bot_ctl, "PROC_PATH", tmp_path / "dummy_proc.json")
    monkeypatch.setattr(bot_ctl, "_save_state", lambda state: None)
    monkeypatch.setattr(bot_ctl, "_emit", lambda obj: None)
    monkeypatch.setattr(bot_ctl, "_pid_alive", lambda pid: False)
    monkeypatch.setattr(bot_ctl, "state_root", lambda: tmp_path)

    class DummyPopen:
        def __init__(self, *args, **kwargs):
            self.pid = 12345

    monkeypatch.setattr(bot_ctl.subprocess, "Popen", DummyPopen)

    with patch(
        "sys.argv",
        ["bot_ctl.py", "start", "--venue", "coinbase", "--symbols", "BTC/USD"],
    ):
        rc = bot_ctl.main()

    assert rc == 0


def test_bot_ctl_stop_all_does_not_require_venue_or_symbols(monkeypatch):
    monkeypatch.setattr(bot_ctl, "_load_state", lambda: {})
    monkeypatch.setattr(bot_ctl, "_emit", lambda obj: None)

    with patch("sys.argv", ["bot_ctl.py", "stop_all"]):
        rc = bot_ctl.main()

    assert rc == 0


def test_bot_ctl_status_emits_compatibility_metadata(monkeypatch):
    monkeypatch.setattr(bot_ctl, "_load_state", lambda: {})
    captured: dict[str, object] = {}
    monkeypatch.setattr(bot_ctl, "_emit", lambda obj: captured.update(obj))

    with patch("sys.argv", ["bot_ctl.py", "status"]):
        rc = bot_ctl.main()

    assert rc == 0
    assert captured["compatibility_only"] is True
    assert captured["control_plane"] == "legacy_compatibility"
    assert captured["canonical_surface"] == {
        "start": "scripts/start_bot.py",
        "stop": "scripts/stop_bot.py",
        "status": "scripts/bot_status.py",
    }
