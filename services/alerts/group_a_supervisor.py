"""Linux one-child watcher cadence; importing starts nothing."""

from contextlib import contextmanager
import ctypes
import fcntl
import math
import os
import secrets
import select
import signal
import stat
import sys
import time

from services.alerts.group_a_queue_readers import _single_linux_thread
from services.alerts.group_a_summary_protocol import (
    Suppression, bit_for, control, decode_control, decode_result, encode_control, encode_result,
)


class CycleFailure(RuntimeError):
    pass


class CycleStopped(CycleFailure):
    pass


def _same_lock(directory, fd, identity):
    info = os.fstat(fd)
    named = os.stat("supervisor.lock", dir_fd=directory, follow_symlinks=False)
    for value in (info, named):
        if (not stat.S_ISREG(value.st_mode) or value.st_uid != os.geteuid()
                or stat.S_IMODE(value.st_mode) != 0o600 or value.st_nlink != 1
                or (value.st_dev, value.st_ino) != identity):
            raise CycleFailure("unsafe_group_a_supervisor_lock")


@contextmanager
def lifetime_lock(directory):
    info = os.fstat(directory)
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise CycleFailure("unsafe_group_a_supervisor_directory")
    fd = os.open("supervisor.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        identity = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
        _same_lock(directory, fd, identity)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _same_lock(directory, fd, identity)
        yield fd, identity
    finally:
        # An explicit LOCK_UN would also unlock an inherited child's fence.
        os.close(fd)


def _parent_death(expected_parent):
    if sys.platform != "linux":
        raise CycleFailure("linux_parent_death_required")
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    if prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != expected_parent:
        raise CycleFailure("group_a_parent_death_unconfirmed")


def _read(fd, cap, deadline, cancelled, *, ready=False):
    output = bytearray()
    while True:
        if cancelled():
            raise CycleStopped("group_a_cycle_stopped")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CycleFailure("group_a_cycle_deadline")
        if not select.select([fd], [], [], min(0.05, remaining))[0]:
            continue
        chunk = os.read(fd, cap + 1 - len(output))
        if not chunk:
            if ready:
                raise CycleFailure("group_a_bootstrap_failed")
            return bytes(output)
        output.extend(chunk)
        if len(output) > cap:
            raise CycleFailure("group_a_cycle_output_limit")
        if ready:
            if output != b"R":
                raise CycleFailure("group_a_bootstrap_failed")
            return b"R"


def _status(pid):
    return os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)


def _cleanup(pid, *, deadline):
    # PID cannot be reused while the direct child has not been reaped.
    for sig, until in ((signal.SIGTERM, min(deadline, time.monotonic() + 1)), (signal.SIGKILL, deadline)):
        try:
            if os.getpgid(pid) == pid:
                os.killpg(pid, sig)
            else:
                os.kill(pid, sig)
        except ProcessLookupError:
            pass
        while time.monotonic() < until:
            result = _status(pid)
            if result is not None:
                os.waitpid(pid, 0)
                return
            time.sleep(min(0.01, max(0, until - time.monotonic())))
    raise CycleFailure("group_a_child_cleanup_unconfirmed")


class LinuxCycle:
    def __init__(self, directory, lock_fd, identity, cycle):
        self.directory, self.lock_fd, self.identity, self.cycle = directory, lock_fd, identity, cycle

    def run(self, request, deadline, cancelled):
        if not _single_linux_thread():
            raise CycleFailure("dedicated_linux_supervisor_required")
        _same_lock(self.directory, self.lock_fd, self.identity)
        incoming = outgoing = None
        descriptors = []
        pid = None
        reaped = False
        cleanup_started = False
        try:
            incoming = os.pipe()
            descriptors.extend(incoming)
            outgoing = os.pipe()
            descriptors.extend(outgoing)
            if any(fd <= 2 for fd in descriptors):
                raise CycleFailure("group_a_standard_descriptors_required")
            parent = os.getpid()
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(incoming[1])
                    os.close(outgoing[0])
                    signal.signal(signal.SIGTERM, signal.SIG_DFL)
                    signal.signal(signal.SIGINT, signal.SIG_DFL)
                    os.setsid()
                    _parent_death(parent)
                    _same_lock(self.directory, self.lock_fd, self.identity)
                    null = os.open(os.devnull, os.O_RDWR)
                    for fd in (0, 1, 2):
                        os.dup2(null, fd)
                    if null > 2:
                        os.close(null)
                    os.write(outgoing[1], b"R")
                    raw = _read(incoming[0], 2048, min(deadline, time.monotonic() + 2), lambda: False)
                    value = decode_control(raw, request["release"], request["generation"])
                    result = self.cycle(value, deadline)
                    encoded = encode_result(result, value)
                    if os.write(outgoing[1], encoded) != len(encoded):
                        os._exit(1)
                    os._exit(0)
                except BaseException:
                    os._exit(1)
            os.close(incoming[0])
            descriptors.remove(incoming[0])
            os.close(outgoing[1])
            descriptors.remove(outgoing[1])
            _read(outgoing[0], 1, min(deadline, time.monotonic() + 2), cancelled, ready=True)
            if os.getpgid(pid) != pid or cancelled():
                raise CycleStopped("group_a_launch_cancelled")
            _same_lock(self.directory, self.lock_fd, self.identity)
            raw = encode_control(request)
            if os.write(incoming[1], raw) != len(raw):
                raise CycleFailure("group_a_launch_gate_failed")
            os.close(incoming[1])
            descriptors.remove(incoming[1])
            output = _read(outgoing[0], 1024, deadline, cancelled)
            status = None
            while status is None:
                if cancelled():
                    raise CycleStopped("group_a_cycle_stopped")
                if time.monotonic() >= deadline:
                    raise CycleFailure("group_a_cycle_deadline")
                status = _status(pid)
                if status is None:
                    time.sleep(0.01)
            result = decode_result(output, request)
            if status.si_code != os.CLD_EXITED or status.si_status != 0:
                raise CycleFailure("group_a_child_failed")
            cleanup_started = True
            _cleanup(pid, deadline=time.monotonic() + 5)
            reaped = True
            return result
        finally:
            try:
                if pid is not None and pid > 0 and not reaped and not cleanup_started:
                    _cleanup(pid, deadline=time.monotonic() + 5)
            finally:
                for fd in descriptors:
                    os.close(fd)


def run_cadence(release, worker, *, cancelled, clock=time.monotonic, pause=time.sleep, max_cycles=None):
    state = Suppression()
    origin = clock()
    slot = 0
    count = 0
    while not cancelled() and (max_cycles is None or count < max_cycles):
        due = origin + slot * 30
        while clock() < due and not cancelled():
            pause(min(0.1, due - clock()))
        if cancelled():
            return 0
        started = clock()
        request = control(release, secrets.token_hex(16), state.mask(started))
        try:
            result = worker.run(request, started + 40, cancelled)
            finished = clock()
            if not math.isfinite(finished) or not started <= finished <= started + 40:
                return 1
            state.accept(result, request, finished)
        except CycleStopped:
            return 0 if cancelled() else 1
        except (CycleFailure, OSError, ValueError):
            return 1
        if (result["outcome"] == "fault" or result["present"] & (
                bit_for(release, "cursor_unavailable") | bit_for(release, "cursor_capacity"))):
            return 1
        if result["outcome"] == "unconfirmed":
            print("group_a_alert_delivery_unconfirmed", file=sys.stderr)
        count += 1
        slot = max(slot + 1, math.floor((finished - origin) / 30) + 1)
    return 0


def supervise(release, directory, cycle):
    if not _single_linux_thread():
        raise CycleFailure("dedicated_linux_supervisor_required")
    stopped = [False]
    def stop(signum, frame):
        stopped[0] = True
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        for sig in previous:
            signal.signal(sig, stop)
        with lifetime_lock(directory) as (fd, identity):
            return run_cadence(release, LinuxCycle(directory, fd, identity, cycle), cancelled=lambda: stopped[0])
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
