import importlib.util
from pathlib import Path
import subprocess

import pytest

spec = importlib.util.spec_from_file_location("bounded_cycle", Path(__file__).with_name("bounded_cycle.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Child:
    pid = 12345
    def __init__(self, timeout=False):
        self.timeout = timeout
        self.returncode = None
        self.waits = 0
    def wait(self, timeout):
        self.waits += 1
        if self.timeout and self.waits == 1:
            raise subprocess.TimeoutExpired("synthetic", timeout)
        self.returncode = 0
        return 0
    def poll(self):
        return self.returncode


@pytest.mark.parametrize("timeout", [False, True])
def test_success_and_timeout_are_once_and_owned(monkeypatch, tmp_path, timeout):
    child = Child(timeout)
    calls, kills = [], []
    def launch(command, **kwargs):
        assert kwargs["start_new_session"] is True
        assert kwargs["env"] == {}
        calls.append(command)
        return child
    monkeypatch.setattr(runner.subprocess, "Popen", launch)
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: kills.append(pid))
    kwargs = dict(folder=tmp_path, cwd=str(tmp_path), env={})
    if timeout:
        with pytest.raises(subprocess.TimeoutExpired):
            runner.run_once(["synthetic"], **kwargs)
        assert kills == [child.pid]
    else:
        assert runner.run_once(["synthetic"], **kwargs)["ok"] is True
        assert not kills
    assert len(calls) == 1
    assert (tmp_path / "RUN_RECEIPT.json").exists()
    with pytest.raises(FileExistsError):
        runner.run_once(["synthetic"], **kwargs)
    assert len(calls) == 1


def test_launch_failure_is_not_retried_or_reported_written(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise OSError("synthetic")
    monkeypatch.setattr(runner.subprocess, "Popen", refuse)
    with pytest.raises(OSError):
        runner.run_once(["synthetic"], folder=tmp_path, cwd=str(tmp_path), env={})
    import json
    receipt = json.loads((tmp_path / "RUN_RECEIPT.json").read_bytes())
    assert receipt["persistence_may_have_occurred"] is False
    assert receipt["error_type"] == "OSError"


def test_cleanup_escalates_only_the_owned_group(monkeypatch):
    class Stuck(Child):
        def wait(self, timeout):
            raise subprocess.TimeoutExpired("synthetic", timeout)
    kills = []
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: kills.append((pid, sig)))
    with pytest.raises(TimeoutError):
        runner.stop_owned(Stuck())
    assert kills == [(12345, runner.signal.SIGTERM), (12345, runner.signal.SIGKILL)]
