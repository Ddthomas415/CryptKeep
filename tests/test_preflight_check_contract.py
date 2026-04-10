from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts import preflight_check as pc


def test_preflight_check_blocks_when_root_requirements_missing(monkeypatch, tmp_path) -> None:
    emitted: list[dict[str, object]] = []

    monkeypatch.setattr(pc, "_REPO", tmp_path)
    monkeypatch.setattr(pc, "emit", lambda ok, msg, **extra: emitted.append({"ok": bool(ok), "msg": msg, **extra}))
    monkeypatch.setattr(
        pc.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="{}", stderr=""),
    )

    out = pc.main()

    assert out == 2
    assert any(row["msg"] == "requirements.txt missing" for row in emitted)
    assert any(row["msg"] == "preflight failed (root baseline requirements.txt missing)" for row in emitted)


def test_preflight_check_accepts_root_requirements_presence(monkeypatch, tmp_path) -> None:
    emitted: list[dict[str, object]] = []

    (tmp_path / "requirements.txt").write_text("streamlit>=1.30\n", encoding="utf-8")
    monkeypatch.setattr(pc, "_REPO", tmp_path)
    monkeypatch.setattr(pc, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(pc, "emit", lambda ok, msg, **extra: emitted.append({"ok": bool(ok), "msg": msg, **extra}))
    monkeypatch.setattr(
        pc.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="{}", stderr=""),
    )

    out = pc.main()

    assert out == 0
    assert any(row["msg"] == "requirements.txt present" for row in emitted)
    assert any(row["msg"] == "runtime trading config available" for row in emitted)
    assert emitted[-1]["msg"] == "preflight complete"


def test_preflight_check_reports_missing_runtime_config_without_failing(monkeypatch, tmp_path) -> None:
    emitted: list[dict[str, object]] = []

    (tmp_path / "requirements.txt").write_text("streamlit>=1.30\n", encoding="utf-8")
    monkeypatch.setattr(pc, "_REPO", tmp_path)
    monkeypatch.setattr(pc, "runtime_trading_config_available", lambda: False)
    monkeypatch.setattr(pc, "emit", lambda ok, msg, **extra: emitted.append({"ok": bool(ok), "msg": msg, **extra}))
    monkeypatch.setattr(
        pc.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="{}", stderr=""),
    )

    out = pc.main()

    assert out == 0
    assert any(row["msg"] == "runtime trading config missing" for row in emitted)
    assert emitted[-1]["msg"] == "preflight complete"
