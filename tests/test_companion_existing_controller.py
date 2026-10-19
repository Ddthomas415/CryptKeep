"""Synthetic controller tests: no Docker, live sockets, credentials or services."""
from dataclasses import replace
import hashlib
import io
import json
import os
import time
from types import SimpleNamespace

import pytest

from scripts.research import companion_existing_controller as c
from dashboard.services.views import _explain_diagnostics as diag
from dashboard.services.views import _shared_http as http
from dashboard.services.views import _shared_signals as signals
from dashboard.services.views import market_view


def response():
    return {"asset": "BTC", "probe_protocol": c.PROTOCOL, "current_cause": "BTC liquidation context; cause unknown.",
            "assistant_status": {"provider": "fallback", "fallback": True},
            "execution_disabled": True, "execution": {"enabled": False},
            "risk_posture": {"gate": "NO_TRADING", "allow_trading": False, "execution_mode": "DISABLED"},
            "evidence": [{"document_id": 42, "url": "https://fixture.invalid/private"}]}


def probe():
    return {"raw": response(), "normalized": response(), "http_status": 200, "diagnostics": []}


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Inline:
    def __init__(self):
        self.caps = []

    def call(self, fn, args, timeout):
        self.caps.append((fn.__name__, timeout))
        assert 0 < timeout <= 45
        return fn(*args)


class Fake:
    def __init__(self):
        self.rows = {n: c.Container(n, f"{i:064x}", "sha256:" + "a" * 64, "exited", "old", 0, "no", "b" * 64)
                     for i, n in enumerate(c.TARGETS, 1)}
        self.calls = []
        self.probe = probe()
        self.evidence = dict.fromkeys(c.EVIDENCE, True)
        self.compat = dict.fromkeys(c.COMPATIBILITY, True)

    def inventory(self):
        return self.rows.copy()

    def compatibility(self, baseline):
        self.calls.append("compatibility")
        return self.compat

    def start(self, container_id):
        name = next(n for n, r in self.rows.items() if r.id == container_id)
        self.calls.append(("start", name))
        self.rows[name] = replace(self.rows[name], state="running", started_at="new")

    def storage_checks(self):
        self.calls.append("storage")
        assert all(self.rows[n].state == "exited" for n in c.TARGETS[3:])
        return dict.fromkeys(("postgres", "qdrant", "minio", "namespaces"), True)

    def health_checks(self):
        self.calls.append("health")
        return dict.fromkeys(c.TARGETS[3:], True)

    def explain(self):
        self.calls.append("explain")
        return self.probe

    def verify_evidence(self, raw):
        self.calls.append("evidence")
        assert raw is self.probe["raw"]
        return self.evidence

    def stop(self, container_id, grace):
        assert grace == 8
        name = next(n for n, r in self.rows.items() if r.id == container_id)
        self.calls.append(("stop", name))
        self.rows[name] = replace(self.rows[name], state="exited")


@pytest.fixture
def harness(tmp_path):
    fake, clock, executor = Fake(), Clock(), Inline()
    receipt = c.Receipt(tmp_path / "attempt.jsonl")
    controller = c.ExistingStackController(fake, receipt, executor=executor, clock=clock, sleep=clock.sleep)
    yield fake, controller, clock, executor, tmp_path / "attempt.jsonl"
    receipt.close()


def test_no_authorization_no_inventory(harness):
    fake, controller, *_ = harness
    fake.inventory = lambda: pytest.fail("unauthorized inventory")
    with pytest.raises(c.Refused):
        controller.run()


def test_one_ordered_attempt_leaves_only_success_running(harness):
    fake, controller, clock, executor, path = harness
    result = controller.run(authorized=True)
    assert result["query_passed"] is True
    assert fake.calls.count("explain") == 1
    assert [x[1] for x in fake.calls if isinstance(x, tuple) and x[0] == "start"] == list(c.TARGETS)
    assert all(row.state == "running" for row in fake.rows.values())
    assert clock.now == 25
    assert ("explain", 45) in executor.caps
    assert ("verify_evidence", 10) in executor.caps
    with pytest.raises(c.Refused):
        controller.run(authorized=True)
    assert "private" not in path.read_text()


@pytest.mark.parametrize("key", sorted(c.COMPATIBILITY))
def test_each_missing_compatibility_gate_refuses_before_start(harness, key):
    fake, controller, *_ = harness
    del fake.compat[key]
    assert controller.run(authorized=True)["query_passed"] is False
    assert not any(isinstance(x, tuple) and x[0] == "start" for x in fake.calls)


@pytest.mark.parametrize("key", sorted(c.EVIDENCE))
def test_missing_evidence_never_passes(harness, key):
    fake, controller, _, _, path = harness
    fake.evidence[key] = False
    result = controller.run(authorized=True)
    assert result["query_passed"] is False and result["cleanup_verified"] is True
    assert [x[1] for x in fake.calls if isinstance(x, tuple) and x[0] == "stop"] == list(reversed(c.TARGETS))
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert next(i for i, e in enumerate(events) if e["phase"] == "query_diagnostics") < next(
        i for i, e in enumerate(events) if e["phase"] == "stop_intended")


def test_running_target_not_started_or_stopped(harness):
    fake, controller, *_ = harness
    fake.rows[c.TARGETS[0]] = replace(fake.rows[c.TARGETS[0]], state="running")
    assert controller.run(authorized=True)["query_passed"] is False
    assert not any(isinstance(x, tuple) for x in fake.calls)


@pytest.mark.parametrize("started", ["", "0001-01-01T00:00:00Z"])
def test_created_applications_complete_attempt(harness, started):
    fake, controller, *_ = harness
    for name in c.TARGETS[3:]:
        fake.rows[name] = replace(fake.rows[name], state="created", started_at=started)
    def storage():
        assert all(fake.rows[n].state == "created" for n in c.TARGETS[3:])
        return dict.fromkeys(("postgres", "qdrant", "minio", "namespaces"), True)
    fake.storage_checks = storage
    assert controller.run(authorized=True)["query_passed"] is True
    assert fake.calls.count("explain") == 1


@pytest.mark.parametrize("name", c.TARGETS[:3])
def test_created_storage_never_admitted(harness, name):
    fake, controller, *_ = harness
    fake.rows[name] = replace(fake.rows[name], state="created", started_at="")
    assert not controller.run(authorized=True)["query_passed"]
    assert not any(isinstance(x, tuple) for x in fake.calls)


@pytest.mark.parametrize("changes", [
    {"started_at": "previous-start"}, {"started_at": None}, {"restarts": 1},
    {"restarts": False}, {"restart_policy": "always"}, {"state": "paused"},
])
def test_invalid_created_application_never_admitted(harness, changes):
    fake, controller, *_ = harness
    row = replace(fake.rows[c.TARGETS[3]], state="created", started_at="")
    fake.rows[row.name] = replace(row, **changes)
    assert not controller.run(authorized=True)["query_passed"]
    assert not any(isinstance(x, tuple) for x in fake.calls)


def test_storage_failure_leaves_unstarted_created_apps_untouched(harness):
    fake, controller, *_ = harness
    for name in c.TARGETS[3:]:
        fake.rows[name] = replace(fake.rows[name], state="created", started_at="")
    original = fake.rows.copy()
    fake.storage_checks = lambda: {"namespaces": False}
    result = controller.run(authorized=True)
    assert not result["query_passed"] and result["cleanup_verified"]
    assert all(fake.rows[n] == original[n] for n in c.TARGETS[3:])
    assert [x[1] for x in fake.calls if isinstance(x, tuple) and x[0] == "start"] == list(c.TARGETS[:3])


@pytest.mark.parametrize("started", ["", "0001-01-01T00:00:00Z"])
def test_created_start_requires_nonzero_ownership_timestamp(harness, started):
    fake, controller, *_ = harness
    name = c.TARGETS[3]
    fake.rows[name] = replace(fake.rows[name], state="created", started_at="")
    fake.storage_checks = lambda: dict.fromkeys(("postgres", "qdrant", "minio", "namespaces"), True)
    start = fake.start
    def unknown_start(container_id):
        start(container_id)
        if container_id == fake.rows[name].id:
            fake.rows[name] = replace(fake.rows[name], started_at=started)
    fake.start = unknown_start
    result = controller.run(authorized=True)
    assert not result["query_passed"] and not result["cleanup_verified"]
    assert ("stop", name) not in fake.calls


def test_baseline_change_aborts_without_taking_ownership(harness):
    fake, controller, *_ = harness
    def compatibility(_):
        fake.rows[c.TARGETS[0]] = replace(fake.rows[c.TARGETS[0]], preservation_digest="c" * 64)
        return fake.compat
    fake.compatibility = compatibility
    result = controller.run(authorized=True)
    assert not result["query_passed"] and not result["cleanup_verified"]
    assert not any(isinstance(x, tuple) for x in fake.calls)


def test_timeout_after_start_is_not_ownership_proof(harness):
    fake, controller, *_ = harness
    start = fake.start
    def ambiguous(container_id):
        start(container_id)
        raise TimeoutError("FIXTURE_SECRET")
    fake.start = ambiguous
    result = controller.run(authorized=True)
    assert result["cleanup_verified"] is False
    assert not any(x[0] == "stop" for x in fake.calls if isinstance(x, tuple))


def test_namespaces_fail_before_application_start(harness):
    fake, controller, *_ = harness
    fake.storage_checks = lambda: {"namespaces": False}
    assert controller.run(authorized=True)["cleanup_verified"] is True
    assert [x[1] for x in fake.calls if isinstance(x, tuple) and x[0] == "start"] == list(c.TARGETS[:3])


def test_deadline_prevents_query_and_reserves_cleanup(harness):
    fake, controller, clock, executor, _ = harness
    def health():
        clock.now = 420
        return dict.fromkeys(c.TARGETS[3:], True)
    fake.health_checks = health
    result = controller.run(authorized=True)
    assert not result["query_passed"] and result["cleanup_verified"]
    assert "explain" not in fake.calls
    assert all(cap <= 12 for name, cap in executor.caps if name == "stop")


def test_ownership_change_never_stops_replacement(harness):
    fake, controller, *_ = harness
    def failed_query():
        fake.rows[c.TARGETS[0]] = replace(fake.rows[c.TARGETS[0]], started_at="another_operator")
        raise RuntimeError("secret")
    fake.explain = failed_query
    result = controller.run(authorized=True)
    assert not result["cleanup_verified"]
    assert ("stop", c.TARGETS[0]) not in fake.calls
    assert fake.rows[c.TARGETS[0]].state == "running"


def test_receipt_failure_does_not_prevent_owned_cleanup(harness):
    fake, controller, *_ = harness
    def fail_query():
        controller.receipt.file.close()
        raise RuntimeError("secret")
    fake.explain = fail_query
    result = controller.run(authorized=True)
    assert not result["query_passed"]
    assert all(r.state == "exited" for r in fake.rows.values())


@pytest.mark.parametrize("change", [
    lambda p: p.update(http_status=500),
    lambda p: p["raw"].pop("assistant_status"),
    lambda p: p["raw"].update(execution_disabled="true"),
    lambda p: p["raw"]["execution"].update(enabled=0),
    lambda p: p["raw"]["risk_posture"].update(gate="OPEN"),
    lambda p: p["raw"]["risk_posture"].update(allow_trading=True),
    lambda p: p["raw"]["risk_posture"].update(allow_trading=0),
    lambda p: p["raw"]["risk_posture"].pop("execution_mode"),
    lambda p: p["raw"]["risk_posture"].update(execution_mode="LIVE"),
    lambda p: p["raw"].pop("probe_protocol"),
    lambda p: p["raw"].update(asset="ETH"),
    lambda p: p["raw"]["evidence"][0].update(document_id=True),
    lambda p: p["raw"]["evidence"][0].update(document_id="42"),
    lambda p: p["normalized"]["assistant_status"].update(provider="dashboard_fallback"),
])
def test_raw_provenance_and_exact_safety_are_required(change):
    p = probe()
    change(p)
    with pytest.raises(c.Refused):
        c.explanation_gates(p)


def test_positive_numeric_id_has_canonical_receipt_hash():
    assert c.explanation_gates(probe())["document_id_sha256"] == [hashlib.sha256(b"42").hexdigest()]
    assert diag.response_summary(response())["citation_hashes"][0]["document_id_sha256"] == hashlib.sha256(b"42").hexdigest()


def test_actual_client_suppresses_primary_without_bypassing_guard(monkeypatch):
    monkeypatch.setattr(c, "_CHILD_CONTEXT", True)
    calls = []
    class Reply(io.BytesIO):
        status = 200
    class Opener:
        def open(self, req, timeout):
            assert req.full_url == "http://127.0.0.1:8002/v1/explain"
            assert req.get_header("Authorization") == "Bearer SYNTHETIC_ONLY"
            assert req.get_header("X-cryptkeep-probe") == c.PROTOCOL
            assert 0 < timeout <= 30
            calls.append(req.full_url)
            return Reply(json.dumps(response()).encode())
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *a: Opener())
    monkeypatch.setattr(http.urllib.request, "urlopen", lambda *a, **k: pytest.fail("primary called"))
    stub = SimpleNamespace(_default_explain_payload=lambda *a: {"assistant_status": {"provider": "dashboard_fallback"}},
                           _explain_mentions_foreign_asset=signals._explain_mentions_foreign_asset,
                           _request_envelope=http._request_envelope, _request_envelope_from_base=http._request_envelope_from_base,
                           _read_mock_envelope=lambda *a: None, PHASE1_ORCHESTRATOR_URL="http://must-not-use.invalid")
    monkeypatch.setattr(market_view, "_view_data", lambda: stub)
    result = c.dashboard_probe("SYNTHETIC_ONLY")
    assert len(calls) == 1
    assert c.explanation_gates(result)
    assert http._PROBE.get() is None
    assert "SYNTHETIC_ONLY" not in json.dumps(result["diagnostics"])
    assert "private" not in json.dumps(result["diagnostics"])


def test_probe_spends_budget_on_failure_and_clears_private_state(monkeypatch):
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *a: SimpleNamespace(open=lambda *a, **k: (_ for _ in ()).throw(TimeoutError())))
    with http.companion_probe_request("SYNTHETIC_ONLY", base="http://127.0.0.1:8002") as state:
        assert "SYNTHETIC_ONLY" not in repr(state)
        assert http._request_envelope_from_base(state.base, "/v1/explain", method="POST") is None
        with pytest.raises(RuntimeError):
            http._request_envelope_from_base(state.base, "/v1/explain", method="POST")
    assert state.token == "" and state.raw_response is None


def test_process_executor_return_and_hard_timeout():
    executor = c.ProcessExecutor()
    assert executor.call(sum, ([1, 2, 3],), 2) == 6
    start = time.monotonic()
    with pytest.raises(c.Refused, match="operation_timeout"):
        executor.call(time.sleep, (10,), 0.1)
    assert time.monotonic() - start < 2


def test_real_receipt_fsync_is_bounded_in_child(tmp_path, monkeypatch):
    receipt = c.Receipt(tmp_path / "slow.jsonl")
    monkeypatch.setattr(c.os, "fsync", lambda fd: time.sleep(10))
    start = time.monotonic()
    try:
        with pytest.raises(c.Refused, match="operation_timeout"):
            c.ProcessExecutor().call(receipt.write, ({"phase": "synthetic"},), 0.1)
        assert time.monotonic() - start < 1
    finally:
        receipt.close()


def test_receipt_exclusive_and_private(tmp_path):
    path = tmp_path / "attempt.jsonl"
    receipt = c.Receipt(path)
    receipt.close()
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        c.Receipt(path)


def test_receipt_delay_rechecks_budget_before_dispatch(harness):
    fake, controller, clock, _, _ = harness
    write = controller.receipt.write
    def delayed(event):
        write(event)
        if event == {"phase": "operation", "operation": "explain"}:
            clock.now = 601
    controller.receipt.write = delayed
    result = controller.run(authorized=True)
    assert not result["query_passed"]
    assert "explain" not in fake.calls


def test_receipt_io_is_inside_executor_budget(harness):
    _, controller, _, executor, _ = harness
    controller.run(authorized=True)
    assert any(name == "write" and cap == 2 for name, cap in executor.caps)


def test_failed_success_receipt_is_never_a_successful_terminal_record(harness):
    fake, controller, _, _, path = harness
    write = controller.receipt.write
    def fail_after_write(event):
        write(event)
        if event["phase"] == "checks_passed_pending_return":
            raise OSError("synthetic fsync failure")
    controller.receipt.write = fail_after_write
    result = controller.run(authorized=True)
    assert not result["query_passed"] and result["cleanup_verified"]
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert any(e["phase"] == "checks_passed_pending_return" for e in events)
    assert not any(e["phase"] == "finished" and e.get("success") is True for e in events)
    assert events[-1] == {"phase": "finished", "success": False, "cleanup_verified": True}


def test_custom_result_reconstruction_never_executes_in_parent():
    class SlowDecode:
        def __reduce__(self):
            return time.sleep, (10,)
    start = time.monotonic()
    with pytest.raises(c.Refused, match="operation_failed"):
        c.ProcessExecutor().call(lambda: SlowDecode(), (), 0.5)
    assert time.monotonic() - start < 1


def test_probe_read_is_hard_bounded_not_just_socket_timeout(monkeypatch):
    monkeypatch.setattr(c, "_CHILD_CONTEXT", True)
    class Reply(io.BytesIO):
        status = 200
        def read(self, *args):
            time.sleep(10)
            return b'{}'
    monkeypatch.setattr(http.urllib.request, "build_opener", lambda *a: SimpleNamespace(open=lambda *a, **k: Reply()))
    start = time.monotonic()
    with http.companion_probe_request("SYNTHETIC_ONLY", base="http://127.0.0.1:8002", timeout=0.1) as state:
        result = http._request_envelope_from_base(state.base, "/v1/explain", method="POST")
        assert result is None and state.raw_response is None
    assert time.monotonic() - start < 1


def test_nested_executors_are_refused_before_dispatch():
    with pytest.raises(c.Refused, match="operation_failed"):
        c.ProcessExecutor().call(lambda: c.ProcessExecutor().call(sum, ([1],), 1), (), 2)


def test_http_cannot_escape_shorter_outer_deadline(tmp_path, monkeypatch):
    pid_path = tmp_path / "http-child-pid"
    def slow_read(req, timeout):
        pid_path.write_text(str(os.getpid()))
        time.sleep(10)
    monkeypatch.setattr(http, "_probe_http_request", slow_read)
    with pytest.raises(c.Refused, match="operation_timeout"):
        c.ProcessExecutor().call(http._bounded_probe_http, (None, 0.3), 0.1)
    pid = int(pid_path.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
