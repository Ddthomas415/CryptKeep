"""Offline-reviewed building blocks for ONE existing-stack attempt.

No CLI, daemon discovery, credential reader or runtime adapter is supplied.
Importing this module does nothing operational. A separately reviewed adapter
must implement Backend using pinned installed identities and real read-only
checks; synthetic test results are not such an adapter or authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import select
import signal
import struct
import threading
import time
from typing import Callable, Protocol

TARGETS = ("phase1-timescaledb", "phase1-qdrant", "phase1-minio",
           "phase1-audit-log", "phase1-risk-stub", "phase1-memory", "phase1-orchestrator")
PROTOCOL = "single-cited-query-v1"
QUESTION = "What news explains Bitcoin liquidations?"
COMPATIBILITY = frozenset({"installed_source", "effective_config", "recipient_bindings",
                          "zero_retries", "no_proxy_redirect", "read_only_startup",
                          "no_model", "no_trading", "entrypoint_side_effects"})
EVIDENCE = frozenset({"persisted_identity", "article_view_mapping", "content_hash",
                      "topical_support", "causal_limits"})
_CHILD_CONTEXT = False
NEVER_STARTED = ("", "0001-01-01T00:00:00Z")


def start_state_allowed(name, state, started_at, restarts):
    """Storage must have exited; only never-started applications may be created."""
    return state == "exited" or (
        name in TARGETS[3:] and state == "created" and started_at in NEVER_STARTED
        and type(restarts) is int and restarts == 0
    )


class Refused(RuntimeError):
    """Fixed reason codes only; never include backend exception messages."""


@dataclass(frozen=True)
class Container:
    name: str
    id: str
    image: str
    state: str
    started_at: str
    restarts: int
    restart_policy: str
    preservation_digest: str

    def identity(self):
        # Digest is of reviewed mount/network/port/entrypoint metadata ONLY,
        # never an environment, credential or full-inspect dump.
        return (self.id, self.image, self.restart_policy, self.preservation_digest)


class Backend(Protocol):
    """Trusted adapter contract; all calls run in bounded disposable children.

    Must not create/recreate/pull/build, migrate, ingest, discover alternate
    endpoints, retry, print secrets, or start background descendants. inventory
    returns all containers, with only the allowlisted Container fields. Checks
    must derive evidence, not echo operator-supplied booleans. No implementation
    of this interface is certified by the synthetic controller tests.
    """

    def inventory(self) -> dict[str, Container]: ...
    def compatibility(self, baseline: dict[str, Container]) -> dict[str, bool]: ...
    def start(self, container_id: str) -> None: ...
    def storage_checks(self) -> dict[str, bool]: ...
    def health_checks(self) -> dict[str, bool]: ...
    def explain(self) -> dict: ...
    def verify_evidence(self, raw: dict) -> dict[str, bool]: ...
    def stop(self, container_id: str, grace: int) -> None: ...


def _child(read_fd, write_fd, fn, args, deadline):
    global _CHILD_CONTEXT
    _CHILD_CONTEXT = True
    os.close(read_fd)
    os.setsid()
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        if time.monotonic() >= deadline:
            raise Refused("operation_timeout")
        value = fn(*args)
        def encode(value):
            if type(value) is Container:
                return {"__container__": dict(vars(value))}
            raise TypeError("unsupported_result_type")
        data = json.dumps([True, value], default=encode, allow_nan=False).encode("utf-8")
        if len(data) > 1_048_576:
            data = b"[false,null]"
    except BaseException:
        # Even exception class names can be attacker-controlled; use one code.
        data = b"[false,null]"
    try:
        frame = memoryview(struct.pack("!I", len(data)) + data)
        while frame:
            written = os.write(write_fd, frame)
            frame = frame[written:]
    finally:
        os.close(write_fd)


class ProcessExecutor:
    """POSIX-only hard wall cap, including result transfer; no automatic retry."""

    def call(self, fn: Callable, args: tuple, timeout: float):
        if _CHILD_CONTEXT:
            raise Refused("nested_executor_refused")
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise Refused("invalid_operation_timeout")
        if threading.active_count() != 1:
            raise Refused("multithreaded_parent")
        ctx = multiprocessing.get_context("fork")
        read_fd, write_fd = os.pipe()
        end = time.monotonic() + timeout
        process = ctx.Process(target=_child, args=(read_fd, write_fd, fn, args, end))
        process.start()
        os.close(write_fd)
        os.set_blocking(read_fd, False)
        try:
            frame = bytearray()
            expected = None
            while expected is None or len(frame) < expected + 4:
                remaining = end - time.monotonic()
                if remaining <= 0 or not select.select([read_fd], [], [], remaining)[0]:
                    raise Refused("operation_timeout")
                chunk = os.read(read_fd, 65_536)
                if not chunk:
                    raise Refused("operation_failed")
                frame.extend(chunk)
                if expected is None and len(frame) >= 4:
                    expected = struct.unpack("!I", frame[:4])[0]
                    if expected > 1_048_576:
                        raise Refused("oversized_operation_result")
            # Only bounded JSON builtins cross the channel. Never reconstruct
            # arbitrary Python objects (__reduce__/pickle can execute code).
            success, result = json.loads(frame[4:])
            process.join(max(0, end - time.monotonic()))
            if process.is_alive() or time.monotonic() > end:
                raise Refused("operation_timeout")
            if not success:
                raise Refused("operation_failed")
            return result
        except (EOFError, OSError):
            raise Refused("operation_failed") from None
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                if process.is_alive():
                    process.kill()
            process.join(0.1)
            os.close(read_fd)


class Receipt:
    """Exclusive, secret-free append-only receipt; fail before startup if unavailable."""

    def __init__(self, path: Path):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self.file = os.fdopen(fd, "w", encoding="ascii")

    def write(self, event: dict):
        self.file.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        self.file.close()


def _all_true(result, keys):
    return isinstance(result, dict) and set(result) == set(keys) and all(result[k] is True for k in keys)


def explanation_gates(probe: dict) -> dict:
    """Transport identity and safety only. This does not verify source relevance."""
    raw = probe.get("raw")
    normal = probe.get("normalized")
    if not isinstance(raw, dict) or not isinstance(normal, dict):
        raise Refused("invalid_explanation")
    data = raw.get("data", raw)
    if not isinstance(data, dict):
        raise Refused("invalid_explanation")
    status = data.get("assistant_status")
    execution = data.get("execution")
    risk = data.get("risk_posture")
    if (probe.get("http_status") != 200 or data.get("asset") != "BTC"
            or data.get("probe_protocol") != PROTOCOL
            or not isinstance(status, dict) or status.get("provider") not in {"phase1_copilot", "fallback"}
            or data.get("execution_disabled") is not True
            or not isinstance(execution, dict) or execution.get("enabled") is not False
            or not isinstance(risk, dict) or risk.get("gate") != "NO_TRADING"
            or risk.get("allow_trading") is not False or risk.get("execution_mode") != "DISABLED"
            or normal.get("asset") != "BTC"
            or normal.get("assistant_status", {}).get("provider") != status.get("provider")
            or not any(isinstance(data.get(k), str) and data[k].strip()
                       for k in ("current_cause", "past_precedent", "future_catalyst"))):
        raise Refused("explanation_safety_or_provenance")
    evidence = data.get("evidence")
    ids = [r["document_id"] for r in evidence if isinstance(r, dict)
           and type(r.get("document_id")) is int and r["document_id"] > 0] if isinstance(evidence, list) else []
    if not ids:
        raise Refused("no_persisted_document_id")
    return {"document_id_sha256": sorted({hashlib.sha256(str(i).encode()).hexdigest() for i in ids})}


def dashboard_probe(token: str) -> dict:
    """Called ONLY inside a future bounded child, with a privately supplied token.

    Raw response is returned to the evidence verifier in memory, not to a file.
    The normal dashboard companion transport/normalizer/asset guard are retained.
    """
    from dashboard.services.views._explain_diagnostics import capture_explain_diagnostics, sanitize_events
    from dashboard.services.views._shared_http import companion_probe_request
    from dashboard.services.views.market_view import get_research_explain

    if not _CHILD_CONTEXT:
        raise Refused("probe_requires_bounded_child")
    with capture_explain_diagnostics() as events:
        with companion_probe_request(token, base="http://127.0.0.1:8002") as state:
            normal = get_research_explain("BTC", QUESTION)
            return {"raw": state.raw_response, "normalized": normal,
                    "http_status": state.status, "diagnostics": sanitize_events(events)}


class ExistingStackController:
    """Enforcement state machine; NOT an installed-image preflight implementation.

    Runtime callers must supply a reviewed backend and explicit fresh permission.
    The default refuses before even inventory. This module grants no permission.
    """

    def __init__(self, backend: Backend, receipt: Receipt, *, executor=None, clock=time.monotonic, sleep=time.sleep):
        self.backend, self.receipt = backend, receipt
        self.executor = executor or ProcessExecutor()
        self.clock, self.sleep = clock, sleep
        self.used = False
        self.owned: dict[str, Container] = {}

    def _record(self, phase, name=None, *, container=None, **flags):
        event = {"phase": phase}
        if name in TARGETS:
            event["target"] = name
        if isinstance(container, Container) and container.name == name and name in TARGETS:
            # Inventory has already validated these public identity digests.
            event["container_id"] = container.id
            event["image_id"] = container.image
        # Never copy arbitrary backend fields or exception text into the receipt.
        event.update({k: v for k, v in flags.items() if type(v) is bool})
        if flags.get("operation") in {"inventory", "compatibility", "start", "storage_checks",
                                      "health_checks", "explain", "verify_evidence", "stop"}:
            event["operation"] = flags["operation"]
        self._write_receipt(event)

    def _write_receipt(self, event):
        remaining = self.final_deadline - self.clock()
        if remaining <= 0:
            raise Refused("receipt_deadline")
        # Storage stalls must not strand the controller or consume its cleanup
        # reserve. Writes/flush/fsync happen in the same bounded child mechanism.
        self.executor.call(self.receipt.write, (event,), min(2, remaining))

    def _call(self, method, *args, cap=10, cleanup=False):
        end = self.final_deadline if cleanup else self.verification_deadline
        if not cleanup:
            self._record("operation", operation=method)
        remaining = end - self.clock()
        if remaining <= 0:
            raise Refused("attempt_deadline")
        return self.executor.call(getattr(self.backend, method), args, min(cap, remaining))

    def _inventory(self, cleanup=False):
        rows = self._call("inventory", cleanup=cleanup)
        if not isinstance(rows, dict) or not set(TARGETS).issubset(rows):
            raise Refused("incomplete_inventory")
        for name, row in rows.items():
            if isinstance(row, dict) and set(row) == {"__container__"}:
                fields = row["__container__"]
                if not isinstance(fields, dict) or set(fields) != set(Container.__dataclass_fields__):
                    raise Refused("invalid_inventory")
                rows[name] = Container(**fields)
        for name, row in rows.items():
            if (not isinstance(row, Container) or name != row.name
                    or re.fullmatch(r"[0-9a-f]{64}", row.id) is None
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", row.image) is None
                    or re.fullmatch(r"[0-9a-f]{64}", row.preservation_digest) is None
                    or type(row.restarts) is not int or row.restarts < 0):
                raise Refused("invalid_inventory")
        if len({row.id for row in rows.values()}) != len(rows):
            raise Refused("ambiguous_identity")
        return rows

    def _start(self, name):
        before = self._inventory()[name]
        if before != self.baseline[name]:
            raise Refused("prestart_state_changed")
        self._record("start_intended", name, container=before)
        self._call("start", before.id, cap=15)
        after = self._inventory()[name]
        if (after.identity() != before.identity() or after.state != "running"
                or not after.started_at or after.started_at in NEVER_STARTED or after.started_at == before.started_at
                or after.restarts != before.restarts):
            raise Refused("start_ownership_unverified")
        self.owned[name] = after
        self._record("start_confirmed", name, container=after)

    def _settle(self, seconds):
        if self.clock() + seconds >= self.verification_deadline:
            raise Refused("attempt_deadline")
        self.sleep(seconds)

    def _cleanup(self):
        complete = True
        for name in reversed(TARGETS):
            if name not in self.owned:
                continue
            try:
                current = self._inventory(cleanup=True)[name]
                if current == self.owned[name]:
                    try:
                        self._record("stop_intended", name, container=current)
                    except Exception:
                        complete = False
                    self._call("stop", current.id, 8, cap=12, cleanup=True)
                elif (current.state != "exited" or current.identity() != self.owned[name].identity()
                      or current.started_at != self.owned[name].started_at):
                    complete = False
            except Exception:
                complete = False
        try:
            final = self._inventory(cleanup=True)
            for name, before in self.baseline.items():
                after = final.get(name)
                if name in self.owned:
                    complete &= after is not None and after.state == "exited" and after.identity() == before.identity()
                else:
                    complete &= after == before
            complete &= set(final) == set(self.baseline)
        except Exception:
            complete = False
        return complete

    def run(self, *, authorized=False):
        if authorized is not True or self.used:
            raise Refused("runtime_not_authorized_or_already_used")
        self.used = True
        start = self.clock()
        self.verification_deadline, self.final_deadline = start + 420, start + 600
        self.baseline = {}
        success = False
        cleanup_verified = False
        diagnostics = []
        try:
            self._record("reserved")
            self.baseline = self._inventory()
            if any(not start_state_allowed(n, self.baseline[n].state, self.baseline[n].started_at,
                                           self.baseline[n].restarts)
                   or self.baseline[n].restart_policy != "no" for n in TARGETS):
                raise Refused("targets_not_stopped")
            if not _all_true(self._call("compatibility", self.baseline), COMPATIBILITY):
                raise Refused("compatibility_unverified")
            if self._inventory() != self.baseline:
                raise Refused("baseline_changed")
            for name in TARGETS[:3]:
                self._start(name)
            self._settle(15)
            if not _all_true(self._call("storage_checks"), {"postgres", "qdrant", "minio", "namespaces"}):
                raise Refused("storage_unverified")
            for name in TARGETS[3:]:
                self._start(name)
            self._settle(10)
            if not _all_true(self._call("health_checks"), set(TARGETS[3:])):
                raise Refused("health_unverified")
            self._record("query_intended")
            probe = self._call("explain", cap=45)
            from dashboard.services.views._explain_diagnostics import sanitize_events
            diagnostics = sanitize_events(probe.get("diagnostics")) if isinstance(probe, dict) else []
            self._write_receipt({"phase": "query_diagnostics", "events": diagnostics})
            # Record the sanitized transport receipt BEFORE any acceptance assertion.
            explanation_gates(probe)
            if not _all_true(self._call("verify_evidence", probe["raw"], cap=10), EVIDENCE):
                raise Refused("evidence_unverified")
            final = self._inventory()
            if set(final) != set(self.baseline) or any(
                final[n] != self.owned[n] if n in self.owned else final[n] != self.baseline[n]
                for n in self.baseline
            ):
                raise Refused("final_state_changed")
            # This receipt is provisional, NOT a successful terminal record. A
            # write may reach disk before fsync reports failure or its child dies.
            self._record("checks_passed_pending_return")
            success = True
        except Exception:
            try:
                self._record("attempt_failed")
            except Exception:
                pass
        finally:
            if not success and self.baseline:
                cleanup_verified = self._cleanup()
            if not success:
                try:
                    self._record("finished", success=False, cleanup_verified=cleanup_verified)
                except Exception:
                    pass
        return {"state": "READY_FOR_INDEPENDENT_REVIEW" if success else "INCOMPLETE",
                "query_passed": success, "cleanup_verified": cleanup_verified, "diagnostics": diagnostics}
