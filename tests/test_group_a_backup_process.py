"""Real owned Python workers/signals only; no downloaded native clients."""
import os
import signal
import time

import pytest

from services.control import group_a_backup_process as owned


def _value():
    return {'synthetic': True}


def _sleep():
    time.sleep(10)


def test_real_worker_returns_and_kills_before_reap(monkeypatch):
    events = []
    killpg, waitpid = os.killpg, os.waitpid
    def kill(pid, sig):
        events.append('signal')
        try:
            return killpg(pid, sig)
        except OSError as error:
            events.append(('signal_errno', error.errno))
            raise
    def wait(pid, flags):
        events.append('reap')
        return waitpid(pid, flags)
    monkeypatch.setattr(owned.os, 'killpg', kill)
    monkeypatch.setattr(owned.os, 'waitpid', wait)
    try:
        result = owned.OwnedProcessExecutor().call(_value, (), 1)
    except owned.ProcessRefused:
        pytest.fail('owned process result refused: ' + repr(events))
    assert result == {'synthetic': True}
    assert events[0] == 'signal'
    assert events.count('signal') == 1


@pytest.mark.parametrize('interrupt_signal', [signal.SIGINT, signal.SIGTERM])
def test_actual_signal_after_fork_does_not_leave_child_alive(interrupt_signal):
    pids = []
    original = os.fork
    old = signal.getsignal(signal.SIGINT)
    def interrupt(*args):
        raise KeyboardInterrupt
    def fork_then_interrupt():
        pid = original()
        if pid > 0:
            pids.append(pid)
            os.kill(os.getpid(), interrupt_signal)
        return pid
    signal.signal(signal.SIGINT, interrupt)
    try:
        with pytest.raises(KeyboardInterrupt):
            owned.OwnedProcessExecutor().call(_sleep, (), 1, fork=fork_then_interrupt)
        with pytest.raises(ChildProcessError):
            os.waitpid(pids[0], os.WNOHANG)
    finally:
        signal.signal(signal.SIGINT, old)


def test_timeout_reaps_owned_leader():
    pids = []
    original = os.fork
    def remember():
        pid = original()
        if pid > 0:
            pids.append(pid)
        return pid
    with pytest.raises(owned.ProcessRefused):
        owned.OwnedProcessExecutor().call(_sleep, (), 0.6, fork=remember)
    with pytest.raises(ChildProcessError):
        os.waitpid(pids[0], os.WNOHANG)


def test_child_function_not_called_before_parent_gate(monkeypatch):
    def stall():
        time.sleep(10)
    monkeypatch.setattr(owned.os, 'setsid', stall)
    with pytest.raises(owned.ProcessRefused):
        owned.OwnedProcessExecutor().call(_value, (), 0.6)


@pytest.mark.parametrize('timeout', [True, 0, -1, float('nan'), float('inf')])
def test_invalid_timeout_does_not_fork(timeout):
    def forbidden():
        pytest.fail('must not fork')
    with pytest.raises(owned.ProcessRefused):
        owned.OwnedProcessExecutor().call(_value, (), timeout, fork=forbidden)


@pytest.mark.parametrize('disposition', [signal.SIG_IGN, lambda *args: None])
def test_nondefault_sigchld_is_refused_before_fork(disposition):
    old = signal.getsignal(signal.SIGCHLD)
    calls = []
    def forbidden():
        calls.append(True)
        raise AssertionError('must refuse before fork')
    signal.signal(signal.SIGCHLD, disposition)
    try:
        with pytest.raises(owned.ProcessRefused):
            owned.OwnedProcessExecutor().call(_value, (), 1, fork=forbidden)
        assert calls == []
    finally:
        signal.signal(signal.SIGCHLD, old)
