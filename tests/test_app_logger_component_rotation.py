import json
import logging
from pathlib import Path

import pytest

from services.logging import app_logger


@pytest.fixture
def logs(tmp_path, monkeypatch):
    monkeypatch.setattr(app_logger.app_paths, "runtime_dir", lambda: tmp_path)
    monkeypatch.setattr(app_logger, "_component_handlers", {})
    monkeypatch.setattr(app_logger, "_json_mode", False)
    monkeypatch.setattr(app_logger, "COMPONENT_LOG_MAX_BYTES", 512)
    monkeypatch.setattr(logging.Logger.manager, "loggerDict", {})
    monkeypatch.delenv("CBP_LOG_COMPONENT", raising=False)
    yield tmp_path / "logs"
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in logger.handlers:
                handler.close()


def test_opt_in_loggers_share_one_bounded_component_file(logs, monkeypatch):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "strategy_runner")
    first, second = (app_logger.get_logger(name) for name in ("r5_a", "r5_b"))
    assert first.handlers[0] is second.handlers[0]
    for i in range(150):
        (first if i % 2 else second).info("entry=%d %s", i, "\u2603" * 60)
    paths = sorted(logs.glob("strategy_runner.bounded.log*"))
    assert [p.name for p in paths] == ["strategy_runner.bounded.log"] + [
        f"strategy_runner.bounded.log.{i}" for i in range(1, 4)
    ]
    assert all(0 < p.stat().st_size <= 512 for p in paths)
    assert "entry=149" in paths[0].read_text()
    assert not (logs / "app.log").exists()


def test_oversize_and_json_switch_preserve_bound_and_redaction(logs, monkeypatch):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "paper_engine")
    logger = app_logger.get_logger("r5_json")
    app_logger.configure_json_logging(enable=True)
    logger.warning("order=%d token=%s", 123, "DO_NOT_STORE")
    logger.warning("%s", "\u2603" * 900)
    path = logs / "paper_engine.bounded.log"
    content = path.read_text()
    rows = [json.loads(line) for line in content.splitlines()]
    assert rows[0]["msg"] == "order=123 token=***REDACTED***"
    assert rows[1]["msg"] == "log_record_omitted_size_limit"
    assert "DO_NOT_STORE" not in content and path.stat().st_size <= 512


def test_legacy_destination_is_unchanged(logs):
    logger = app_logger.get_logger("r5_legacy")
    logger.info("ordinary log")
    assert Path(logger.handlers[0].baseFilename) == logs / "app.log"
    assert "ordinary log" in (logs / "app.log").read_text()
    assert not list(logs.glob("*.bounded.log*"))


def test_component_name_cannot_escape_the_account_log_directory(logs, monkeypatch):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "../../shared")
    with pytest.raises(ValueError, match="invalid_log_component"):
        app_logger.get_logger("r5_invalid")
    assert not logs.exists()


@pytest.mark.parametrize("json_mode", [False, True])
def test_bounded_record_omits_exception_and_untrusted_fields(logs, monkeypatch, json_mode):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "paper_engine")
    logger = app_logger.get_logger("r5_fields")
    app_logger.configure_json_logging(enable=json_mode)
    try:
        raise ValueError("token=FAKE_EXCEPTION")
    except ValueError:
        logger.exception("account=%d", 7, extra={"token": "FAKE_EXTRA", "nested": {"password": "FAKE_NESTED"}})
    line = (logs / "paper_engine.bounded.log").read_text()
    assert "account=7" in line
    assert all(value not in line for value in ("FAKE_EXCEPTION", "FAKE_EXTRA", "FAKE_NESTED", "Traceback"))
    if json_mode:
        assert json.loads(line)["msg"] == "account=7"


def test_bad_format_never_emits_raw_record_to_stderr(logs, monkeypatch, capsys):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "paper_engine")
    monkeypatch.setattr(logging, "raiseExceptions", True)
    logger = app_logger.get_logger("r5_bad_format")
    logger.warning("token=%d", "FAKE_STDERR")
    assert capsys.readouterr().err == "component_log_write_failed\n"


def test_rotation_measures_the_same_rendering_it_writes(logs, monkeypatch):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "paper_engine")
    logger = app_logger.get_logger("r5_once")

    class ChangesOnRender:
        calls = 0

        def __str__(self):
            self.calls += 1
            return "short" if self.calls == 1 else "x" * 260

    logger.info("%s", "a" * 350)
    value = ChangesOnRender()
    logger.info("%s", value)
    path = logs / "paper_engine.bounded.log"
    assert path.stat().st_size <= 512
    assert value.calls == 1
    assert "short" in path.read_text()


def test_log_open_failure_is_fixed_and_contains_no_record_details(logs, monkeypatch, capsys):
    monkeypatch.setenv("CBP_LOG_COMPONENT", "paper_engine")
    logger = app_logger.get_logger("r5_disk_error")

    def unavailable():
        raise OSError("FAKE_IO_DETAIL")

    monkeypatch.setattr(logger.handlers[0], "_open", unavailable)
    logger.error("token=%s", "FAKE_RECORD")
    assert capsys.readouterr().err == "component_log_write_failed\n"
    assert not list(logs.glob("*.bounded.log*"))
