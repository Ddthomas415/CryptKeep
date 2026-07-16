from __future__ import annotations

import importlib


def _fresh_config_editor(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    from services.audit.operator_event_journal import load_operator_events, operator_event_journal_path
    from services.audit.operator_event_secret_scan import scan_operator_event_journal

    importlib.reload(app_paths)
    config_editor = importlib.reload(config_editor)
    return config_editor, load_operator_events, operator_event_journal_path, scan_operator_event_journal


def test_save_user_yaml_appends_metadata_only_operator_event(monkeypatch, tmp_path):
    config_editor, load_events, journal_path, scan_journal = _fresh_config_editor(monkeypatch, tmp_path)
    secret_value = "CONFIG_SECRET_DO_NOT_LOG"

    ok, message = config_editor.save_user_yaml(
        {
            "risk": {"max_daily_notional_quote": 100},
            "exchanges": {"coinbase": {"api_key": secret_value}},
        }
    )

    assert (ok, message) == (True, "Saved")
    events = load_events()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "runtime_config_save"
    assert event["target"] == "user.yaml"
    assert event["source"] == "services.admin.config_editor"
    assert event["pre_state"] == {"exists": False, "parse_ok": True, "mapping": True, "section_count": 0, "section_names": []}
    assert event["post_state"] == {
        "exists": True,
        "parse_ok": True,
        "mapping": True,
        "section_count": 2,
        "section_names": ["exchanges", "risk"],
    }
    assert event["extra"] == {"config_payload_logged": False}
    assert secret_value not in journal_path().read_text(encoding="utf-8")
    assert scan_journal(require_events=True)["ok"] is True


def test_save_user_yaml_dry_run_does_not_append_event(monkeypatch, tmp_path):
    config_editor, load_events, _journal_path, _scan_journal = _fresh_config_editor(monkeypatch, tmp_path)

    ok, message = config_editor.save_user_yaml({"risk": {"max_daily_notional_quote": 100}}, dry_run=True)

    assert (ok, message) == (True, "Dry run OK")
    assert load_events() == []
    assert not config_editor.CONFIG_PATH.exists()


def test_save_user_yaml_event_failure_rolls_back_new_file(monkeypatch, tmp_path):
    config_editor, _load_events, _journal_path, _scan_journal = _fresh_config_editor(monkeypatch, tmp_path)

    def _raise_operator_event(**_kwargs):
        raise PermissionError("journal read-only")

    monkeypatch.setattr(config_editor, "append_operator_event", _raise_operator_event)

    ok, message = config_editor.save_user_yaml({"execution": {"live_enabled": False}})

    assert (ok, message) == (False, "operator_event_write_failed_runtime_config_rolled_back")
    assert not config_editor.CONFIG_PATH.exists()


def test_save_user_yaml_event_failure_restores_previous_file(monkeypatch, tmp_path):
    config_editor, _load_events, _journal_path, _scan_journal = _fresh_config_editor(monkeypatch, tmp_path)

    ok, message = config_editor.save_user_yaml({"execution": {"live_enabled": False}})
    assert (ok, message) == (True, "Saved")

    def _raise_operator_event(**_kwargs):
        raise PermissionError("journal read-only")

    monkeypatch.setattr(config_editor, "append_operator_event", _raise_operator_event)

    ok, message = config_editor.save_user_yaml({"execution": {"live_enabled": True}})

    assert (ok, message) == (False, "operator_event_write_failed_runtime_config_rolled_back")
    assert config_editor.load_user_yaml()["execution"]["live_enabled"] is False
