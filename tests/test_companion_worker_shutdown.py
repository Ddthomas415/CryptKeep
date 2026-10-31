"""Synthetic procfs/pidfd/clock and Docker fakes only; no real process signals."""
from dataclasses import replace
import hashlib
import json
import os
import socket
import subprocess
from types import SimpleNamespace

import pytest

from scripts.research import companion_worker_shutdown as worker
from scripts.research import companion_installer as install
from scripts.research import companion_existing_controller as core
from tests.test_companion_running_backend import backend
from tests.test_companion_running_storage import running_manifest


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("worker test attempted real native/network/signal work")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "kill", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def v6_manifest():
    data = running_manifest()
    data["schema"] = "companion-worker-staged-update-v6"
    for app in data["applications"]:
        app["command"] = worker.replacement_command(app["name"])
    return data


def load(data):
    raw = install.canonical(data)
    return install.Plan.load(raw, hashlib.sha256(raw).hexdigest())


def test_v6_is_explicit_and_legacy_manifest_unchanged():
    assert load(v6_manifest()).worker_shutdown is True
    assert load(v6_manifest()).staged is True
    assert load(running_manifest()).worker_shutdown is False


def test_new_worker_source_is_required_in_v6_continuation_bindings():
    from scripts.research import companion_cutover_continuation as continuation
    path = "scripts/research/companion_worker_shutdown.py"
    assert path in continuation.consumer_paths(load(v6_manifest()))
    assert path not in continuation.consumer_paths(load(running_manifest()))


@pytest.mark.parametrize("change", ["shell", "wrong_module", "wrong_port", "entrypoint"])
def test_v6_requires_direct_expected_replacement_launch(change):
    data = v6_manifest()
    app = data["applications"][0]
    if change == "shell": app["command"] = ["sh", "-c", "exec uvicorn anything:app"]
    elif change == "wrong_module": app["command"][3] = "orchestrator.main:app"
    elif change == "wrong_port": app["command"][-1] = "1"
    else: app["create_options"] += ["--entrypoint", "sh"]
    with pytest.raises(core.Refused):
        load(data)


@pytest.fixture
def proc():
    namespace = {}
    exec(compile(worker.WORKER_SOURCE, "<fixed-worker-source>", "exec"), namespace)
    state = SimpleNamespace(epoch=1000.0, mono=100.0, events=[], after_open=lambda: None)
    shell = b"uvicorn ${SERVICE_MODULE}:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"
    def status(pid, name, parent, caught=0, ignored=0, blocked=0):
        return (f"Name:\t{name}\nPid:\t{pid}\nPPid:\t{parent}\nSigCgt:\t{caught:x}\n"
                f"SigIgn:\t{ignored:x}\nSigBlk:\t{blocked:x}\n").encode()
    fields = ["S", "1"] + ["0"] * 17 + ["1234"] + ["0"] * 5
    state.files = {
        "/proc/1/status": status(1, "sh", 0),
        "/proc/1/cmdline": b"sh\0-c\0" + shell + b"\0",
        "/proc/1/task/1/children": b"27 ",
        "/proc/27/status": status(27, "uvicorn", 1, 1 << 14),
        "/proc/27/cmdline": b"\0".join([b"/usr/local/bin/python", b"/usr/local/bin/uvicorn",
            b"orchestrator.main:app", b"--host", b"0.0.0.0", b"--port", b"8002", b""]),
        "/proc/27/stat": ("27 (uvicorn) " + " ".join(fields)).encode(),
    }
    state.status = status
    def opened(pid, flags):
        state.events.append(("open", pid, flags))
        state.after_open()
        return 90
    def sent(fd, sig, info, flags):
        state.events.append(("signal", fd, sig, info, flags))
    state.os = SimpleNamespace(pidfd_open=opened, close=lambda fd: state.events.append(("close", fd)))
    state.sig = SimpleNamespace(SIGTERM=15, pidfd_send_signal=sent)
    state.clock = SimpleNamespace(time=lambda: state.epoch, monotonic=lambda: state.mono)
    def read(path):
        assert "environ" not in path
        return state.files[path]
    state.read = read
    state.run = lambda: namespace["terminate_worker"]("orchestrator.main", "8002", 1000., 1009.,
                                                       state.os, state.sig, state.clock, state.read)
    return state


def test_single_sigterm_uses_dynamic_worker_pidfd_and_closes_handle(proc):
    proc.run()
    assert proc.events == [("open", 27, 0), ("signal", 90, 15, None, 0), ("close", 90)]


@pytest.mark.parametrize("change", ["multiple", "missing", "parent", "name", "module", "port",
                                   "handler", "ignored", "blocked", "zombie", "shell", "oversized_pid"])
def test_bad_or_ambiguous_identity_never_signals(proc, change):
    if change == "multiple": proc.files["/proc/1/task/1/children"] = b"27 28"
    elif change == "missing": del proc.files["/proc/27/status"]
    elif change == "parent": proc.files["/proc/27/status"] = proc.status(27, "uvicorn", 4, 1 << 14)
    elif change == "name": proc.files["/proc/27/status"] = proc.status(27, "python", 1, 1 << 14)
    elif change == "module": proc.files["/proc/27/cmdline"] = proc.files["/proc/27/cmdline"].replace(b"orchestrator", b"risk_stub")
    elif change == "port": proc.files["/proc/27/cmdline"] = proc.files["/proc/27/cmdline"].replace(b"8002", b"8008")
    elif change == "handler": proc.files["/proc/27/status"] = proc.status(27, "uvicorn", 1)
    elif change == "ignored": proc.files["/proc/27/status"] = proc.status(27, "uvicorn", 1, 1 << 14, 1 << 14)
    elif change == "blocked": proc.files["/proc/27/status"] = proc.status(27, "uvicorn", 1, 1 << 14, blocked=1 << 14)
    elif change == "zombie": proc.files["/proc/27/stat"] = proc.files["/proc/27/stat"].replace(b") S ", b") Z ")
    elif change == "shell": proc.files["/proc/1/cmdline"] = b"sh\0-c\0something else\0"
    else: proc.files["/proc/1/task/1/children"] = b"99999999999999999999"
    with pytest.raises((ValueError, KeyError)):
        proc.run()
    assert not any(e[0] == "signal" for e in proc.events)


@pytest.mark.parametrize("change", ["starttime", "argv", "parent", "child", "gone", "expired", "backward", "monotonic"])
def test_identity_drift_or_deadline_after_pidfd_open_refuses_and_closes(proc, change):
    def mutate():
        if change == "starttime": proc.files["/proc/27/stat"] = proc.files["/proc/27/stat"].replace(b"1234", b"9999")
        elif change == "argv": proc.files["/proc/27/cmdline"] = b"private unexpected payload"
        elif change == "parent": proc.files["/proc/27/status"] = proc.status(27, "uvicorn", 2, 1 << 14)
        elif change == "child": proc.files["/proc/1/task/1/children"] = b"28"
        elif change == "gone": del proc.files["/proc/27/stat"]
        elif change == "expired": proc.epoch = 1010.
        elif change == "backward": proc.epoch = 999.
        else: proc.mono = 110.
    proc.after_open = mutate
    with pytest.raises((ValueError, KeyError)):
        proc.run()
    assert proc.events == [("open", 27, 0), ("close", 90)]


@pytest.mark.parametrize("capability", ["open", "send"])
def test_unsupported_pidfd_fails_without_numeric_pid_fallback(proc, capability):
    if capability == "open": del proc.os.pidfd_open
    else: del proc.sig.pidfd_send_signal
    with pytest.raises(AttributeError): proc.run()
    assert not any(e[0] == "signal" for e in proc.events)
    if capability == "send": assert proc.events[-1] == ("close", 90)


def test_pidfd_esrch_does_not_signal_reused_numeric_pid_or_retry(proc):
    def dead(*args): raise ProcessLookupError("synthetic_dead_handle")
    proc.sig.pidfd_send_signal = dead
    with pytest.raises(ProcessLookupError): proc.run()
    assert proc.events == [("open", 27, 0), ("close", 90)]


@pytest.mark.parametrize("remaining", [0, -1, 11, float("nan"), float("inf"), True])
def test_command_budget_invalid_before_dispatch(remaining):
    with pytest.raises(ValueError):
        worker.command("a" * 64, "phase1-orchestrator", issued=1000., remaining=remaining)


def test_program_compiles_without_execution_and_isolated_python_flags():
    command = worker.command("a" * 64, "phase1-orchestrator", issued=1000., remaining=5.)
    assert command[:8] == ("container", "exec", "a" * 64, "python", "-I", "-S", "-B", "-c")
    compile(command[8], "<container-program>", "exec")
    assert worker.WORKER_SOURCE in command[8]
    assert command[-4:] == ("orchestrator.main", "8002", "1000.0", "1005.0")


@pytest.mark.parametrize("failure", [None, "lost_ack", "bad_ack", "not_exited", "metadata"])
def test_v6_backend_still_requires_command_ack_and_fresh_stopped_inventory(backend, failure):
    native, commands, _ = backend
    native.plan = replace(native.plan, worker_shutdown=True)
    before = native.plan.baseline[-1]
    calls = []
    def command(args, **kwargs):
        if args[:2] != ("container", "exec"):
            return commands(args, **kwargs)
        calls.append(args)
        assert args[2] == before.id and args[-4:-2] == ("orchestrator.main", "8002")
        row = commands.rows[before.id]
        if failure != "not_exited":
            row["state"] = "exited"
            row["networks"]["synthetic"]["NetworkID"] = ""
        if failure == "metadata": row["image"] = "sha256:" + "f" * 64
        if failure == "lost_ack": raise TimeoutError("SYNTHETIC_PRIVATE_ERROR")
        return b"unexpected" if failure == "bad_ack" else worker.ACK
    native._command = command
    report = native.quiesce_report(before.id)
    assert report["confirmed"] is (failure is None)
    assert report["command_acknowledged"] is (failure not in {"lost_ack", "bad_ack"})
    assert len(calls) == 1 and commands.mutations() == []
    assert "SYNTHETIC_PRIVATE_ERROR" not in json.dumps(report)


@pytest.mark.parametrize("entrypoint", [False, None, True])
def test_v6_inherited_entrypoint_is_refused_before_environment_or_creation(backend, entrypoint):
    native, commands, _ = backend
    native.plan = replace(native.plan, worker_shutdown=True,
                          applications=({"name": native.plan.baseline[-1].name},))
    image = native.plan.baseline[-1].image
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        assert args[:2] == ("image", "inspect")
        return json.dumps({"id": image, "layers": [], "onbuild": None,
                           "entrypoint_empty": entrypoint}).encode()
    native._command = command
    if entrypoint is True:
        assert native._image(image)["entrypoint_empty"] is True
    else:
        with pytest.raises(core.Refused):
            native._create(native.plan.baseline[-1].name, image, "synthetic")
    assert len(calls) == 1
