"""Opt-in lifecycle v6: fixed worker identity and pidfd-only graceful shutdown.

Importing this module never reads procfs, contacts Docker or sends a signal.
The embedded program runs only through the separately authorized backend.
"""
from __future__ import annotations

import math

APP_SPEC = {
    "phase1-audit-log": ("audit_log.main", "8009"),
    "phase1-risk-stub": ("risk_stub.main", "8008"),
    "phase1-memory": ("memory_retrieval.main", "8007"),
    "phase1-orchestrator": ("orchestrator.main", "8002"),
}
ACK = b"worker_sigterm_sent_v1\n"


def replacement_command(name):
    module, port = APP_SPEC[name]
    return ["python", "-m", "uvicorn", module + ":app", "--host", "0.0.0.0", "--port", port]


# One source is used by the container command and injected offline unit tests.
# A pidfd, not a second numeric-PID lookup, is the only signal target.
WORKER_SOURCE = r'''
def terminate_worker(module, port, issued, expires, os_api, signal_api, clock, read):
    def require(ok):
        if not ok:
            raise ValueError("worker_shutdown_refused")

    now = clock.time()
    require(0 < expires - issued <= 10 and issued <= now < expires)
    monotonic_end = clock.monotonic() + expires - now

    def in_budget():
        require(now <= clock.time() < expires and clock.monotonic() < monotonic_end)

    def status(pid):
        fields = dict(line.split(b":", 1) for line in read("/proc/%d/status" % pid).splitlines()
                      if b":" in line)
        require(int(fields[b"Pid"]) == pid)
        return fields

    def children():
        ids = read("/proc/1/task/1/children").split()
        require(len(ids) == 1 and ids[0].isdigit() and 1 < int(ids[0]) < 2**31)
        return int(ids[0])

    pid = children()
    original_shell = b"uvicorn ${SERVICE_MODULE}:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"

    def identity():
        root, worker = status(1), status(pid)
        require(root[b"Name"].strip() == b"sh" and int(root[b"PPid"]) == 0)
        require(read("/proc/1/cmdline") == b"sh\0-c\0" + original_shell + b"\0")
        require(children() == pid and int(worker[b"PPid"]) == 1
                and worker[b"Name"].strip() == b"uvicorn")
        bit = 1 << (int(signal_api.SIGTERM) - 1)
        require(int(worker[b"SigCgt"], 16) & bit
                and not (int(worker[b"SigIgn"], 16) & bit)
                and not (int(worker[b"SigBlk"], 16) & bit))
        args = read("/proc/%d/cmdline" % pid).split(b"\0")
        interpreters = {b"/usr/local/bin/python", b"/usr/local/bin/python3"}
        interpreters.update(("/usr/local/bin/python3.%d" % v).encode() for v in range(8, 16))
        require(len(args) == 8 and args[0] in interpreters
                and args[1:] == [b"/usr/local/bin/uvicorn", (module + ":app").encode(),
                                b"--host", b"0.0.0.0", b"--port", port.encode(), b""])
        # stat field22 is starttime; rsplit tolerates spaces/parentheses in comm.
        stat = read("/proc/%d/stat" % pid)
        require(stat.startswith((str(pid) + " (").encode()))
        fields = stat.rsplit(b")", 1)[1].split()
        require(fields[0] not in {b"Z", b"X"} and int(fields[1]) == 1)
        return int(fields[19]), read("/proc/%d/cmdline" % pid)

    first = identity()
    in_budget()
    fd = os_api.pidfd_open(pid, 0)
    try:
        require(identity() == first)
        in_budget()
        signal_api.pidfd_send_signal(fd, signal_api.SIGTERM, None, 0)
    finally:
        os_api.close(fd)
'''

WORKER_PROGRAM = WORKER_SOURCE + r'''
import os, signal, sys, time
def bounded_read(path):
    with open(path, "rb") as stream:
        raw = stream.read(16385)
    if len(raw) > 16384:
        raise ValueError("worker_shutdown_refused")
    return raw
try:
    terminate_worker(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]),
                     os, signal, time, bounded_read)
except BaseException:
    sys.exit(1)
sys.stdout.write("worker_sigterm_sent_v1\n")
sys.stdout.flush()
'''


def command(container_id, name, *, issued, remaining):
    if (type(issued) not in (int, float) or not math.isfinite(issued)
            or type(remaining) not in (int, float) or not math.isfinite(remaining)
            or not 0 < remaining <= 10):
        raise ValueError("worker_shutdown_refused")
    module, port = APP_SPEC[name]
    return ("container", "exec", container_id, "python", "-I", "-S", "-B", "-c",
            WORKER_PROGRAM, module, port, str(issued), str(issued + remaining))
