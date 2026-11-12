"""Owned POSIX worker fence for explicit backup preparation/probe actions.

The parent never reaps the leader until group signalling is finished. A gated
child may not call the supplied trusted function before ownership is recorded.
The function and its subprocesses must retain this process group.
"""
import json
import math
import os
import select
import signal
import struct
import threading
import time


class ProcessRefused(RuntimeError):
    pass


def _read(fd, size, deadline):
    result = bytearray()
    while len(result) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            raise ProcessRefused('backup_worker_deadline')
        raw = os.read(fd, size - len(result))
        if not raw:
            raise ProcessRefused('backup_worker_incomplete')
        result.extend(raw)
    return bytes(result)


def _child(read_fd, write_fd, gate_read, gate_write, fn, args, mask, deadline):
    os.close(read_fd)
    os.close(gate_write)
    try:
        os.setsid()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        null = os.open('/dev/null', os.O_WRONLY)
        os.dup2(null, 1)
        os.dup2(null, 2)
        os.close(null)
        os.write(write_fd, b'R')
        if _read(gate_read, 1, deadline) != b'G':
            os._exit(1)
        try:
            value = fn(*args)
            raw = json.dumps([True, value], allow_nan=False).encode()
            if len(raw) > 1 << 20:
                raw = b'[false,null]'
        except BaseException:
            raw = b'[false,null]'
        frame = memoryview(struct.pack('!I', len(raw)) + raw)
        while frame:
            frame = frame[os.write(write_fd, frame):]
        # Keep a live leader (and its ownership credentials) until the parent
        # signals the group. EOF also releases this hold if the parent dies.
        _read(gate_read, 1, deadline)
    except BaseException:
        pass
    finally:
        os._exit(0)


class OwnedProcessExecutor:
    def call(self, fn, args, timeout, *, fork=os.fork):
        if (type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0.5
                or threading.current_thread() is not threading.main_thread() or threading.active_count() != 1
                or signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL):
            raise ProcessRefused('invalid_backup_worker_context')
        end = time.monotonic() + timeout
        operation_end = end - min(5.0, max(0.2, timeout / 10))
        read_fd = write_fd = gate_read = gate_write = None
        pid = None
        group_owned = False
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        cleanup_failed = False
        def cancel(*args):
            raise KeyboardInterrupt
        try:
            for sig in handlers:
                signal.signal(sig, cancel)
            read_fd, write_fd = os.pipe()
            gate_read, gate_write = os.pipe()
            pid = fork()
            if pid == 0:
                _child(read_fd, write_fd, gate_read, gate_write, fn, args, mask, operation_end)
            os.close(write_fd)
            write_fd = None
            os.close(gate_read)
            gate_read = None
            # Signals are unblocked only after pid and cleanup ownership exist.
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            if _read(read_fd, 1, operation_end) != b'R':
                raise ProcessRefused('backup_worker_gate_missing')
            group_owned = True
            os.write(gate_write, b'G')
            size = struct.unpack('!I', _read(read_fd, 4, operation_end))[0]
            if not 0 < size <= 1 << 20:
                raise ProcessRefused('backup_worker_receipt_limit')
            success, result = json.loads(_read(read_fd, size, operation_end))
            if success is not True:
                raise ProcessRefused('backup_worker_failed')
            return result
        finally:
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
            try:
                if pid is not None and pid > 0:
                    # No wait/reap has occurred: leader pid fences the group ID.
                    try:
                        if group_owned:
                            os.killpg(pid, signal.SIGKILL)
                        else:
                            os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except OSError:
                        cleanup_failed = True
                    # Signalling is now disabled. Only now may leader be reaped.
                    while True:
                        observed, _ = os.waitpid(pid, os.WNOHANG)
                        if observed == pid:
                            break
                        if time.monotonic() >= end:
                            cleanup_failed = True
                            break
                        time.sleep(0.005)
            finally:
                for fd in (read_fd, write_fd, gate_read, gate_write):
                    if fd is not None:
                        os.close(fd)
                for sig, handler in handlers.items():
                    signal.signal(sig, handler)
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
            if cleanup_failed:
                raise ProcessRefused('backup_worker_cleanup_uncertain')
