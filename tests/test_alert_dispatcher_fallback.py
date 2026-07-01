from __future__ import annotations

from pathlib import Path

from services.alerts import alert_dispatcher


def test_send_alert_suppresses_persist_last_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(alert_dispatcher, "ALERT_LOG_PATH", tmp_path / "alerts.jsonl")
    monkeypatch.setattr(alert_dispatcher, "LAST_PATH", tmp_path / "last.json")
    monkeypatch.setattr(
        alert_dispatcher,
        "atomic_write",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk read-only")),
    )

    result = alert_dispatcher.send_alert(
        cfg={"alerts": {"enabled": False}},
        level="error",
        message="host health failed",
        payload={"check": "storage_health"},
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["local_written"] is True


def test_send_alert_suppresses_local_alert_write_failure(monkeypatch, tmp_path: Path) -> None:
    alert_log_directory = tmp_path / "alerts-dir"
    alert_log_directory.mkdir()
    monkeypatch.setattr(alert_dispatcher, "ALERT_LOG_PATH", alert_log_directory)
    monkeypatch.setattr(alert_dispatcher, "LAST_PATH", tmp_path / "last.json")

    result = alert_dispatcher.send_alert(
        cfg={"alerts": {"enabled": False}},
        level="error",
        message="host health failed",
        payload={"check": "storage_health"},
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["local_written"] is True


def test_read_alert_log_skips_invalid_json_lines(monkeypatch, tmp_path: Path) -> None:
    alert_log = tmp_path / "alerts.jsonl"
    alert_log.write_text(
        '{"level":"error","message":"valid"}\n'
        'not-json\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(alert_dispatcher, "ALERT_LOG_PATH", alert_log)

    rows = alert_dispatcher.read_alert_log()

    assert rows == [{"level": "error", "message": "valid"}]
