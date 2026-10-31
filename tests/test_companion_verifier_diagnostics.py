"""Synthetic-only diagnostic protocol, privacy and unchanged acceptance gates."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time

import pytest

from scripts.research import companion_evidence_checks as checks
from scripts.research import companion_existing_controller as core
from tests.test_companion_evidence_checks import case, offline, remote
from tests.test_companion_runtime_adapter import setup as adapter_setup
from tests.test_companion_running_update import harness, run as run_update


@pytest.mark.parametrize("change,stage,code", [
    ("input", "input", "rejected"), ("identity", "persisted_identity", "rejected"),
    ("archive", "archive_envelope", "rejected"), ("response", "response_contract", "rejected"),
    ("query", "query_contract", "rejected"), ("citation", "citations", "rejected"),
    ("bundle", "bundle_contract", "rejected"), ("market", "bundle_market", "rejected"),
    ("document", "bundle_documents", "rejected"), ("metadata", "metadata", "error"),
    ("narrative", "narrative", "rejected"), ("witness", "witnesses", "rejected"),
])
def test_first_failed_group_without_payload_or_exception_text(case, change, stage, code):
    raw, view, actual, approvals = deepcopy(case)
    if change == "input": raw = []
    elif change == "identity": actual[0]["content_hash"] = "f" * 64
    elif change == "archive": raw["archive_view"]["status"] = "PRIVATE"
    elif change == "response": raw["asset"] = "ETH"
    elif change == "query": raw["question_evidence"]["method"] = "PRIVATE"
    elif change == "citation": raw["evidence"][0]["url"] = "PRIVATE"
    elif change == "bundle": raw["evidence_bundle"]["PRIVATE"] = "PRIVATE"
    elif change == "market": raw["evidence_bundle"]["market"]["latest_price"] = 123
    elif change == "document": raw["evidence_bundle"]["past_context"][0]["title"] = "PRIVATE"
    elif change == "metadata": raw["answer_metadata"]["as_of"] = "PRIVATE"
    elif change == "narrative": raw["current_cause"] = "PRIVATE"
    else: approvals.clear()
    result = checks.evaluate_diagnostic(raw, view, actual, approvals)
    assert result["checks"] == checks.evaluate(raw, view, actual, approvals) == dict.fromkeys(checks.KEYS, False)
    assert result["diagnostic"] == {"stage": stage, "code": code}
    assert "PRIVATE" not in json.dumps(result)


def test_diagnostic_success_preserves_pure_api(case):
    result = checks.evaluate_diagnostic(*case)
    assert result == {"checks": checks.evaluate(*case), "diagnostic": {"stage": "complete", "code": "ok"}}
    assert all(result["checks"].values()) and checks.diagnostic_result_valid(result)


@pytest.mark.parametrize("failure,stage", [
    ("archive", "archive_load"), ("lineage", "source_lineage"),
    ("query", "db_query"), ("teardown", "db_teardown"), ("arm", "timer"),
    ("cleanup", "timer_cleanup")])
def test_remote_operational_failure_codes_are_fixed(monkeypatch, case, failure, stage):
    result, _ = remote(monkeypatch, case, failure=failure, diagnostic=True)
    assert result["diagnostic"] == {"stage": stage, "code": "error"}
    assert not any(result["checks"].values())


def test_occupied_timer_reports_rejection_without_touching_it(monkeypatch, case):
    events = []
    result, calls = remote(monkeypatch, case, timer=(1.0, 0.0), alarm_events=events, diagnostic=True)
    assert result["diagnostic"] == {"stage": "timer", "code": "rejected"}
    assert not calls and events == ["getitimer"]


def test_remote_diagnostic_keeps_single_readonly_query(monkeypatch, case):
    result, calls = remote(monkeypatch, case, diagnostic=True)
    assert result["diagnostic"] == {"stage": "complete", "code": "ok"}
    assert calls == ["archive", "connect", "transaction", "cursor",
                     ("SET TRANSACTION READ ONLY", None),
                     (checks.SOURCE_SQL, ([1, 2, 3, 4],)), "lineage"]


def test_first_evaluation_failure_survives_later_teardown_failure(monkeypatch, case):
    case[0]["asset"] = "ETH"
    result, _ = remote(monkeypatch, case, failure="late_teardown", diagnostic=True)
    assert result["diagnostic"] == {"stage": "response_contract", "code": "rejected"}


@pytest.mark.parametrize("data,code", [
    (b"PRIVATE invalid json", "error"),
    (b'{"raw":{},"raw":{},"approvals":[]}', "rejected"),
    (b'{"raw":{},"approvals":[],"PRIVATE":"PRIVATE"}', "rejected"),
])
def test_input_failures_are_diagnosed_before_any_dependency(monkeypatch, case, data, code):
    result, calls = remote(monkeypatch, case, data=data, diagnostic=True)
    assert result["diagnostic"] == {"stage": "input_parse", "code": code} and not calls


@pytest.mark.parametrize("stage,code", [("PRIVATE", "error"), ("input", "PRIVATE"),
                                       ("complete", "error"), ("input", "ok"), ([], "error")])
def test_unknown_or_inconsistent_diagnostics_fail_closed(adapter_setup, monkeypatch, stage, code):
    _, _, runtime = adapter_setup
    result = {"checks": dict.fromkeys(checks.KEYS, True), "diagnostic": {"stage": stage, "code": code}}
    monkeypatch.setattr(runtime, "_command", lambda *_a, **_kw: json.dumps(result).encode())
    with pytest.raises(core.Refused, match="invalid_evidence_receipt"):
        runtime.verify_evidence({})


def test_diagnostic_survives_real_bounded_process_json_channel():
    value = {"checks": dict.fromkeys(checks.KEYS, False),
             "diagnostic": {"stage": "citations", "code": "rejected"}}
    assert core.ProcessExecutor().call(lambda: value, (), 2) == value


def test_legacy_adapter_method_keeps_five_boolean_shape(adapter_setup, monkeypatch):
    _, _, runtime = adapter_setup
    value = {"checks": dict.fromkeys(checks.KEYS, True), "diagnostic": {"stage": "complete", "code": "ok"}}
    monkeypatch.setattr(runtime, "_command", lambda *_a, **_kw: json.dumps(value).encode())
    assert runtime.verify_evidence({}) == value["checks"]
    assert runtime.verify_evidence_diagnostic({}) == value


@pytest.mark.parametrize("duplicate", ["checks", "diagnostic", "check", "stage", "code"])
def test_adapter_rejects_duplicate_wire_members_at_every_depth(adapter_setup, monkeypatch, duplicate):
    _, _, runtime = adapter_setup
    good_checks = json.dumps(dict.fromkeys(checks.KEYS, True))
    good_diagnostic = '{"stage":"complete","code":"ok"}'
    members = f'"checks":{good_checks},"diagnostic":{good_diagnostic}'
    if duplicate == "checks":
        members = f'"checks":{json.dumps(dict.fromkeys(checks.KEYS, False))},' + members
    elif duplicate == "diagnostic":
        members = '"diagnostic":{"stage":"input","code":"rejected"},' + members
    elif duplicate == "check":
        members = members.replace('"content_hash": true', '"content_hash": false,"content_hash": true')
    elif duplicate == "stage":
        members = members.replace('"stage":"complete"', '"stage":"input","stage":"complete"')
    else:
        members = members.replace('"code":"ok"', '"code":"error","code":"ok"')
    wire = ("{" + members + "}").encode()
    calls = []

    def command(*args, **kwargs):
        calls.append((args, kwargs))
        return wire

    monkeypatch.setattr(runtime, "_command", command)
    with pytest.raises(core.Refused, match="invalid_evidence_receipt"):
        runtime.verify_evidence_diagnostic({})
    assert len(calls) == 1
    assert calls[0][1]["cap"] == 10 and calls[0][1]["limit"] == 8192


@pytest.mark.parametrize("value", [False, True])
def test_diagnostic_method_cannot_downgrade_to_bare_checks(value):
    h = harness()
    calls = []

    def diagnostic(_raw):
        calls.append(True)
        return dict.fromkeys(checks.KEYS, value)

    h[-1].verify_evidence_diagnostic = diagnostic
    h[-1].verify_evidence = lambda _raw: pytest.fail("must not retry via legacy")
    result = run_update(h)
    event = next(e["installation_evidence"] for e in h[2].events if e["phase"] == "evidence_verification_checks")
    assert calls == [True] and not result["query_passed"]
    assert event["shape_valid"] is False
    assert event["diagnostic"] == {"stage": "parent_boundary", "code": "invalid"}


def test_explicit_legacy_method_still_accepts_bare_checks():
    h = harness()
    assert not callable(getattr(h[-1], "verify_evidence_diagnostic", None))
    h[-1].evidence_result = dict.fromkeys(checks.KEYS, True)
    result = run_update(h)
    event = next(e["installation_evidence"] for e in h[2].events if e["phase"] == "evidence_verification_checks")
    assert result["query_passed"] and event["shape_valid"] is True
    assert event["diagnostic"] == {"stage": "legacy_result", "code": "unavailable"}


@pytest.mark.parametrize("failure", [False, True])
def test_installer_selects_diagnostic_method_once_without_legacy_retry(failure):
    h = harness()
    calls = []

    def diagnostic(raw):
        calls.append(True)
        if failure:
            raise RuntimeError("PRIVATE")
        return {"checks": dict.fromkeys(checks.KEYS, True), "diagnostic": {"stage": "complete", "code": "ok"}}

    h[-1].verify_evidence_diagnostic = diagnostic
    h[-1].verify_evidence = lambda _raw: pytest.fail("must not retry via legacy")
    result = run_update(h)
    assert result["query_passed"] is not failure and calls == [True]
    event = next(e["installation_evidence"] for e in h[2].events if e["phase"] == "evidence_verification_checks")
    assert event["diagnostic"] == ({"stage": "parent_boundary", "code": "unavailable"} if failure
                                    else {"stage": "complete", "code": "ok"})
    assert "PRIVATE" not in json.dumps(h[2].events)


@pytest.mark.parametrize("success", [False, True])
def test_installer_records_diagnostic_but_accepts_only_checks(success):
    h = harness()
    h[-1].evidence_result = {"checks": dict.fromkeys(checks.KEYS, success),
        "diagnostic": {"stage": "complete" if success else "bundle_market", "code": "ok" if success else "rejected"}}
    result = run_update(h)
    event = next(e["installation_evidence"] for e in h[2].events if e["phase"] == "evidence_verification_checks")
    assert event["diagnostic"] == h[-1].evidence_result["diagnostic"]
    assert result["query_passed"] is success


def test_installer_drops_malicious_diagnostic_and_never_approves():
    h = harness()
    h[-1].evidence_result = {"checks": dict.fromkeys(checks.KEYS, True),
                            "diagnostic": {"stage": "PRIVATE", "code": "ok"}}
    result = run_update(h)
    event = next(e["installation_evidence"] for e in h[2].events if e["phase"] == "evidence_verification_checks")
    assert not result["query_passed"] and event["outcome"] == "invalid_shape"
    assert event["diagnostic"] == {"stage": "parent_boundary", "code": "invalid"}
    assert "PRIVATE" not in json.dumps(h[2].events)


@pytest.mark.parametrize("change", ["extra", "missing", "list", "numeric", "false_with_ok"])
def test_diagnostic_envelope_cannot_hide_failed_or_invalid_checks(change):
    h = harness()
    payload = {"checks": dict.fromkeys(checks.KEYS, True),
               "diagnostic": {"stage": "complete", "code": "ok"}}
    if change == "extra": payload["PRIVATE"] = "PRIVATE"
    elif change == "missing": payload["diagnostic"].pop("code")
    elif change == "list": payload["diagnostic"] = ["PRIVATE"]
    elif change == "numeric": payload["checks"]["content_hash"] = 1
    else: payload["checks"]["content_hash"] = False
    h[-1].evidence_result = payload
    result = run_update(h)
    assert not result["query_passed"]
    assert "PRIVATE" not in json.dumps(h[2].events)


def test_original_predicates_and_sql_except_approved_exclusion_branch():
    root = Path(__file__).resolve().parents[1]
    with tarfile.open(root / "docs/review_artifacts/companion_verifier_diagnostics_20261026/prechange.tar") as archive:
        before = ast.parse(archive.extractfile("scripts/research/companion_evidence_checks.py").read())
    after = ast.parse((root / "scripts/research/companion_evidence_checks.py").read_text())
    names = {"_evaluate", "_document", "_archive_envelope", "_indexed", "_time", "_unique_object"}

    expected = ast.parse('''
if market["reason"] == "excluded_by_archival_probe":
    _require(key == "market" and set(market) == {"ok", "reason", "latest_price", "change_pct", "window_samples"}
             and raw.get("probe_protocol") == "single-cited-query-v1"
             and status.get("probe_protocol") == "single-cited-query-v1"
             and market["latest_price"] is None and type(market["window_samples"]) is int)
else:
    _require(market["reason"] == "no_market_data")
''').body[0]

    class ApprovedBranch(ast.NodeTransformer):
        matches = 0

        def visit_If(self, node):
            if ast.dump(node.test) == ast.dump(expected.test):
                assert ast.dump(node) == ast.dump(expected)
                self.matches += 1
                return node.orelse[0]
            return self.generic_visit(node)

    approved = ApprovedBranch()
    after = approved.visit(after)
    assert approved.matches == 1

    def conditions(tree):
        return {fn.name: [ast.dump(call.args[0]) for call in ast.walk(fn)
                          if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "_require"]
                for fn in tree.body if isinstance(fn, ast.FunctionDef) and fn.name in names}

    assert conditions(before) == conditions(after)
    assert checks.SOURCE_SQL == next(ast.literal_eval(n.value) for n in before.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SOURCE_SQL" for t in n.targets))


def test_actual_private_child_deadline_has_only_fixed_diagnostic():
    bootstrap = '''
import builtins, socket, sys, time
from types import SimpleNamespace
original_import = builtins.__import__
def forbidden(*args, **kwargs): raise AssertionError("offline child")
def guarded(name, *args, **kwargs):
    if name.split(".")[0] in {"shared", "memory_retrieval", "psycopg", "pydantic_settings"}: forbidden()
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded
socket.socket = socket.create_connection = socket.getaddrinfo = forbidden
class StalledInput:
    def read(self, size): time.sleep(60)
sys.stdin = SimpleNamespace(buffer=StalledInput())
'''
    started = time.monotonic()
    completed = subprocess.run([sys.executable, "-I", "-S", "-B", "-c",
        bootstrap + f"\nexec({checks.DIAGNOSTIC_EVIDENCE_SCRIPT!r})\n"],
        env={}, capture_output=True, timeout=10, check=False)
    assert completed.returncode == 0 and completed.stderr == b""
    assert json.loads(completed.stdout) == {"checks": dict.fromkeys(checks.KEYS, False),
        "diagnostic": {"stage": "input_read", "code": "deadline"}}
    assert 7.5 <= time.monotonic() - started < 10
