from contextlib import contextmanager
import os
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from services.alerts import group_a_supervisor as supervisor
from services.alerts.group_a_summary_protocol import Health, bit_for, cycle_result


RELEASE = "frozen42"


class Clock:
    def __init__(self):
        self.now = 0.0
    def read(self):
        return self.now
    def pause(self, seconds):
        self.now += seconds


def test_cadence_skips_overrun_slot_without_catchup_or_overlap():
    clock, starts = Clock(), []
    class Worker:
        def run(self, request, deadline, cancelled):
            starts.append(clock.now)
            assert deadline == clock.now + 40
            clock.now += 35
            return cycle_result(request, 1, "idle", Health())
    assert supervisor.run_cadence(RELEASE, Worker(), cancelled=lambda: False, clock=clock.read,
                                  pause=clock.pause, max_cycles=3) == 0
    assert starts == [0, 60, 120]


def test_cadence_uses_account_scoped_suppression_and_recovery():
    clock, requests = Clock(), []
    a, b = 1 << 3, 1 << 4
    class Worker:
        def run(self, request, deadline, cancelled):
            requests.append(request)
            if len(requests) == 1:
                return cycle_result(request, 1, "slack_accepted", Health().with_state(a, "present"), a)
            if len(requests) == 2:
                assert request["suppressed"] == a
                return cycle_result(request, 2, "slack_accepted", Health().with_state(a | b, "present"), b)
            assert request["suppressed"] == a | b
            return cycle_result(request, 3, "idle", Health().with_state(a, "known_clear"))
    assert supervisor.run_cadence(RELEASE, Worker(), cancelled=lambda: False, clock=clock.read,
                                  pause=clock.pause, max_cycles=3) == 0
    assert len({request["generation"] for request in requests}) == 3


@pytest.mark.parametrize("failure", ["timeout", "wrong_generation", "fatal_health", "late"])
def test_cadence_fault_stops_without_implicit_retry(failure):
    clock, calls = Clock(), []
    class Worker:
        def run(self, request, deadline, cancelled):
            calls.append(1)
            if failure == "timeout":
                raise supervisor.CycleFailure("synthetic deadline")
            health = Health()
            if failure == "fatal_health":
                health = health.with_state(bit_for(RELEASE, "cursor_capacity"), "present")
            result = cycle_result(request, 1, "idle", health)
            if failure == "wrong_generation":
                result["generation"] = "wrong"
            if failure == "late":
                clock.now += 41
            return result
    assert supervisor.run_cadence(RELEASE, Worker(), cancelled=lambda: False, clock=clock.read,
                                  pause=clock.pause, max_cycles=3) == 1
    assert calls == [1]


def test_stop_between_slots_never_launches_again():
    clock, calls = Clock(), []
    class Worker:
        def run(self, request, deadline, cancelled):
            calls.append(1)
            return cycle_result(request, 1, "idle", Health())
    assert supervisor.run_cadence(RELEASE, Worker(), cancelled=lambda: clock.now >= 1,
                                  clock=clock.read, pause=clock.pause) == 0
    assert calls == [1]


def test_unconfirmed_transport_reports_fixed_diagnostic_on_planned_cycles(capsys):
    clock, starts = Clock(), []
    class Worker:
        def run(self, request, deadline, cancelled):
            starts.append(clock.now)
            return cycle_result(request, 1, "unconfirmed", Health())
    assert supervisor.run_cadence(RELEASE, Worker(), cancelled=lambda: False, clock=clock.read,
                                  pause=clock.pause, max_cycles=2) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "group_a_alert_delivery_unconfirmed\n" * 2
    assert starts == [0, 30]


@pytest.fixture
def lock_root(tmp_path):
    path = tmp_path / "cursor"
    path.mkdir(mode=0o700)
    lock = path / "supervisor.lock"
    lock.touch(mode=0o600)
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        yield fd, lock
    finally:
        os.close(fd)


def test_lifetime_lock_is_never_created_or_replaced_and_excludes_second_owner(lock_root):
    directory, lock = lock_root
    before = lock.stat().st_ino
    with supervisor.lifetime_lock(directory) as (fd, identity):
        with pytest.raises(BlockingIOError):
            with supervisor.lifetime_lock(directory):
                pytest.fail("second owner entered")
        lock.unlink()
        lock.touch(mode=0o600)
        with pytest.raises(supervisor.CycleFailure):
            supervisor._same_lock(directory, fd, identity)
    lock.unlink()
    with pytest.raises(FileNotFoundError):
        with supervisor.lifetime_lock(directory):
            pytest.fail("missing lock initialized")
    assert not lock.exists()


def test_inherited_lifetime_descriptor_blocks_replacement_until_child_exits(lock_root):
    directory, _ = lock_root
    child = None
    try:
        with supervisor.lifetime_lock(directory) as (fd, identity):
            child = subprocess.Popen([sys.executable, "-B", "-c", "import sys;sys.stdin.read()"],
                                     stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, pass_fds=(fd,), env={})
        with pytest.raises(BlockingIOError):
            with supervisor.lifetime_lock(directory):
                pytest.fail("surviving child fence lost")
        child.communicate(timeout=5)
        with supervisor.lifetime_lock(directory):
            pass
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.communicate(timeout=5)


@pytest.mark.parametrize("raw,cap", [(b"x" * 1025, 1024), (b"RR", 1)])
def test_child_output_caps_are_enforced_with_real_pipe(raw, cap):
    read, write = os.pipe()
    try:
        os.write(write, raw)
        os.close(write)
        write = None
        with pytest.raises(supervisor.CycleFailure):
            supervisor._read(read, cap, time.monotonic() + 1, lambda: False, ready=cap == 1)
    finally:
        os.close(read)
        if write is not None:
            os.close(write)


def test_cleanup_targets_only_owned_group_and_reaps_once(monkeypatch):
    calls = []
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(supervisor.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    monkeypatch.setattr(supervisor, "_status", lambda pid: SimpleNamespace(si_status=0))
    monkeypatch.setattr(supervisor.os, "waitpid", lambda pid, flags: calls.append((pid, "reaped")))
    supervisor._cleanup(123456, deadline=time.monotonic() + 1)
    assert calls == [(123456, signal.SIGTERM), (123456, "reaped")]


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux parent-death and WNOWAIT; not Mac proof")
def test_native_linux_cycle_launch_gate_result_and_reap(lock_root):
    directory, _ = lock_root
    from services.alerts.group_a_summary_protocol import control
    request = control(RELEASE, "a" * 32, 0)
    with supervisor.lifetime_lock(directory) as (fd, identity):
        worker = supervisor.LinuxCycle(directory, fd, identity,
                                       lambda value, deadline: cycle_result(value, 1, "idle", Health()))
        assert worker.run(request, time.monotonic() + 2, lambda: False)["outcome"] == "idle"


def test_parent_death_protocol_checks_prctl_result_and_parent_race(monkeypatch):
    monkeypatch.setattr(supervisor.sys, "platform", "linux")
    code = [0]
    def prctl(*args):
        assert args == (1, signal.SIGKILL, 0, 0, 0)
        return code[0]
    monkeypatch.setattr(supervisor.ctypes, "CDLL", lambda *a, **kw: SimpleNamespace(prctl=prctl))
    monkeypatch.setattr(supervisor.os, "getppid", lambda: 123)
    supervisor._parent_death(123)
    with pytest.raises(supervisor.CycleFailure):
        supervisor._parent_death(124)
    code[0] = -1
    with pytest.raises(supervisor.CycleFailure):
        supervisor._parent_death(123)
