"""Synthetic native-process fixtures only; no Docker control or trading APIs.

Run explicitly in a separately authorized disposable Linux environment. This
does not validate production namespaces, systemd units, queues or Slack receipt.
"""

import ctypes
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import signal
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


CASES = ("normal_cycle", "cycle_timeout", "active_cancellation", "parent_death_before_gate",
         "parent_death_after_gate", "inherited_lifetime_lock", "supervisor_sigterm")


def check_packet(root):
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    if type(manifest) is not dict or manifest.get("schema") != 1 or type(manifest.get("files")) is not dict:
        raise ValueError("invalid_native_probe_manifest")
    expected = set(manifest["files"])
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
    if actual != expected | {"MANIFEST.json"} or len(expected) != 21:
        raise ValueError("native_probe_packet_scope_changed")
    total = 0
    for name, info in manifest["files"].items():
        path = root / name
        if (Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink()
                or not path.resolve().is_relative_to(root.resolve()) or not name.endswith(".py")):
            raise ValueError("invalid_native_probe_member")
        raw = path.read_bytes()
        total += len(raw)
        if (len(raw) > 262144 or total > 524288 or len(raw) != info["bytes"]
                or sha256(raw).hexdigest() != info["sha256"]):
            raise ValueError("native_probe_packet_digest_changed")
    return len(expected)


def _forbid_network(*args, **kwargs):
    raise RuntimeError("native_process_probe_network_forbidden")


def _wait(pid, deadline):
    while time.monotonic() < deadline:
        observed, status = os.waitpid(pid, os.WNOHANG)
        if observed == pid:
            return status
        time.sleep(0.01)
    raise AssertionError("owned_fixture_child_did_not_exit")


def _terminate(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        _wait(pid, time.monotonic() + 5)
    except ChildProcessError:
        pass


def _receive(fd, deadline):
    raw = bytearray()
    while time.monotonic() < deadline:
        if not select.select([fd], [], [], 0.05)[0]:
            continue
        value = os.read(fd, 65 - len(raw))
        if not value:
            break
        raw.extend(value)
        if len(raw) > 64:
            raise AssertionError("fixture_receipt_too_large")
        if raw.endswith(b"\n"):
            return int(raw)
    raise AssertionError("fixture_receipt_missing")


def _forever(*args):
    while True:
        time.sleep(0.05)


class NativeProcessCases(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="cbp-r3-native-")
        root = Path(self.directory.name)
        root.chmod(0o700)
        (root / "supervisor.lock").touch(mode=0o600)
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        self.release = "native42"
        self.owned = set()

    def tearDown(self):
        for pid in tuple(self.owned):
            _terminate(pid)
        os.close(self.fd)
        self.directory.cleanup()

    def _cycle(self, callback, *, seconds=0.25, cancelled=lambda: False):
        from services.alerts import group_a_supervisor as native
        from services.alerts.group_a_summary_protocol import control
        original = os.fork
        def tracked_fork():
            pid = original()
            if pid > 0:
                self.owned.add(pid)
            return pid
        with native.lifetime_lock(self.fd) as (lock, identity), patch.object(native.os, "fork", tracked_fork):
            worker = native.LinuxCycle(self.fd, lock, identity, callback)
            return worker.run(control(self.release, "a" * 32, 0), time.monotonic() + seconds, cancelled)

    def _no_unreaped_children(self):
        for pid in tuple(self.owned):
            with self.assertRaises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)
        self.owned.clear()

    def test_normal_cycle(self):
        from services.alerts.group_a_summary_protocol import Health, cycle_result
        result = self._cycle(lambda request, deadline: cycle_result(request, 1, "idle", Health()), seconds=2)
        self.assertEqual(result["outcome"], "idle")
        self._no_unreaped_children()

    def test_cycle_timeout(self):
        from services.alerts.group_a_supervisor import CycleFailure
        started = time.monotonic()
        with self.assertRaises(CycleFailure):
            self._cycle(_forever)
        self.assertLess(time.monotonic() - started, 6)
        self._no_unreaped_children()

    def test_active_cancellation(self):
        from services.alerts.group_a_supervisor import CycleStopped
        start = time.monotonic()
        with self.assertRaises(CycleStopped):
            self._cycle(_forever, seconds=3, cancelled=lambda: time.monotonic() - start >= 0.25)
        self.assertLess(time.monotonic() - start, 6)
        self._no_unreaped_children()

    def _parent_death(self, before_gate):
        from services.alerts import group_a_supervisor as native
        original_parent_death = native._parent_death
        report_read, report_write = os.pipe()
        outer = os.fork()
        if outer == 0:
            try:
                os.close(report_read)
                def report_then_wait(*args):
                    os.write(report_write, f"{os.getpid()}\n".encode("ascii"))
                    _forever()
                def pause_before_gate(parent):
                    original_parent_death(parent)
                    report_then_wait()
                with native.lifetime_lock(self.fd) as (lock, identity):
                    if before_gate:
                        native._parent_death = pause_before_gate
                    from services.alerts.group_a_summary_protocol import control
                    native.LinuxCycle(self.fd, lock, identity, report_then_wait).run(
                        control(self.release, "a" * 32, 0), time.monotonic() + 10, lambda: False,
                    )
                os._exit(1)
            except BaseException:
                os._exit(2)
        self.owned.add(outer)
        os.close(report_write)
        try:
            worker = _receive(report_read, time.monotonic() + 3)
            self.assertGreater(worker, 1)
            # A fixture receipt is received only from our owned supervisor's child.
            self.owned.add(worker)
            os.kill(outer, signal.SIGKILL)
            self.assertTrue(os.WIFSIGNALED(_wait(outer, time.monotonic() + 3)))
            self.owned.remove(outer)
            status = _wait(worker, time.monotonic() + 3)
            self.assertTrue(os.WIFSIGNALED(status))
            self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
            self.owned.remove(worker)
            with native.lifetime_lock(self.fd):
                pass
        finally:
            os.close(report_read)

    def test_parent_death_before_gate(self):
        self._parent_death(True)

    def test_parent_death_after_gate(self):
        self._parent_death(False)

    def test_inherited_lifetime_lock(self):
        from services.alerts import group_a_supervisor as native
        with native.lifetime_lock(self.fd):
            pid = os.fork()
            if pid == 0:
                _forever()
            self.owned.add(pid)
        with self.assertRaises(BlockingIOError):
            with native.lifetime_lock(self.fd):
                self.fail("inherited_fence_lost")
        _terminate(pid)
        self.owned.remove(pid)
        with native.lifetime_lock(self.fd):
            pass

    def test_supervisor_sigterm(self):
        from services.alerts import group_a_supervisor as native
        read, write = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(read)
                def active(request, deadline):
                    os.write(write, f"{os.getpid()}\n".encode("ascii"))
                    _forever()
                os._exit(native.supervise(self.release, self.fd, active))
            except BaseException:
                os._exit(2)
        self.owned.add(pid)
        os.close(write)
        try:
            child = _receive(read, time.monotonic() + 3)
            self.owned.add(child)
            os.kill(pid, signal.SIGTERM)
            status = _wait(pid, time.monotonic() + 6)
            self.owned.remove(pid)
            self.assertTrue(os.WIFEXITED(status))
            self.assertEqual(os.WEXITSTATUS(status), 0)
            with self.assertRaises(ChildProcessError):
                os.waitpid(child, os.WNOHANG)
            self.owned.remove(child)
            with native.lifetime_lock(self.fd):
                pass
        finally:
            os.close(read)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args == ["--describe"]:
        print(json.dumps({"scope": "synthetic_linux_processes_only", "cases": CASES,
                          "requires": "Linux/Python3.12/nonroot", "network": "forbidden"}))
        return 0
    root = Path(__file__).resolve().parents[2]
    if args == ["--check-packet"]:
        try:
            count = check_packet(root)
            socket.socket.connect = _forbid_network
            socket.socket.connect_ex = _forbid_network
            sys.path.insert(0, str(root))
            with tempfile.TemporaryDirectory(prefix="cbp-r3-native-import-") as state:
                os.environ.clear()
                os.environ.update({"HOME": state, "CBP_STATE_DIR": state, "PATH": "/usr/bin:/bin"})
                from services.alerts import group_a_supervisor
            print(json.dumps({"packet_files": count, "stdlib_import": "passed", "kernel_tests_run": 0}))
            return 0
        except Exception:
            print("native_probe_packet_check_failed", file=sys.stderr)
            return 1
    if args != ["--run-linux-fixtures"]:
        print("native_probe_explicit_mode_required", file=sys.stderr)
        return 2
    if sys.platform != "linux" or sys.version_info[:2] != (3, 12) or os.geteuid() == 0:
        print("native_probe_requires_nonroot_linux_python312", file=sys.stderr)
        return 2
    try:
        check_packet(root)
    except Exception:
        print("native_probe_packet_check_failed", file=sys.stderr)
        return 2
    # Subreaping is confined to this disposable fixture process and its children.
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    if prctl(36, 1, 0, 0, 0) != 0:
        print("native_probe_subreaper_unavailable", file=sys.stderr)
        return 2
    socket.socket.connect = _forbid_network
    socket.socket.connect_ex = _forbid_network
    sys.path.insert(0, str(root))
    with tempfile.TemporaryDirectory(prefix="cbp-r3-native-state-") as state:
        os.environ.clear()
        os.environ.update({"HOME": state, "CBP_STATE_DIR": state, "PATH": "/usr/bin:/bin"})
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeProcessCases)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    print(json.dumps({"scope": "synthetic_linux_processes_only", "tests": result.testsRun,
                      "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped)}))
    return 0 if result.wasSuccessful() and result.testsRun == len(CASES) and not result.skipped else 1


if __name__ == "__main__":
    sys.exit(main())
