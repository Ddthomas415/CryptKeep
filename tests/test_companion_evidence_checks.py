"""Synthetic only: no application imports, Settings, DB, Docker, or network."""
import ast
import builtins
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
from types import ModuleType, SimpleNamespace

import pytest

from scripts.research import companion_evidence_checks as checks


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline test attempted service or network access")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in {"shared", "memory_retrieval", "psycopg", "pydantic_settings"}:
            if name not in sys.modules or not getattr(sys.modules[name], "_synthetic", False):
                forbidden()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


def orchestrator_functions():
    """Compile only pure reviewed functions; never import app or Settings."""
    path = ROOT / "phase1_research_copilot/orchestrator/main.py"
    tree = ast.parse(path.read_text())
    names = {"_fallback_reasoning", "_build_evidence", "_build_evidence_bundle",
             "_assemble_explain_response", "_clip_confidence"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    class Metadata(SimpleNamespace):
        def model_dump(self):
            return vars(self)

    metadata_path = ROOT / "phase1_research_copilot/shared/answer_metadata.py"
    metadata_tree = ast.parse(metadata_path.read_text())
    metadata_nodes = [n for n in metadata_tree.body if isinstance(n, ast.FunctionDef)]
    metadata_ns = {"Any": object, "datetime": datetime, "timezone": timezone, "AnswerMetadata": Metadata}
    exec(compile(ast.Module(body=metadata_nodes, type_ignores=[]), str(metadata_path), "exec"), metadata_ns)
    namespace = {"Any": object, "ExplainRequest": object, "_asset_symbol": lambda a: a,
                 "build_answer_metadata": metadata_ns["build_answer_metadata"]}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def query_audit():
    path = ROOT / "phase1_research_copilot/memory_retrieval/question_query.py"
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, (ast.Assign, ast.FunctionDef))]
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["question_query"](checks.QUESTION)


@pytest.fixture
def case():
    originals, derived = [], []
    for ident in range(1, 5):
        row = {"id": ident, "content_hash": str(ident) * 64, "source_type": "news",
               "source": "synthetic", "url": f"https://example.test/{ident}",
               "title": f"Stored headline {ident}", "raw_object_key": f"raw/{ident}",
               "published_at": None, "fetched_at": "2026-10-01T00:00:00+00:00"}
        originals.append(row)
        derived.append({**row, "original_content_hash": row["content_hash"],
                        "body_verified": True, "content_text": "A reviewed content witness in its body."})
    view = {"rows": derived, "original": {r["id"]: r for r in originals}, "sha256": "d" * 64}
    ns = orchestrator_functions()
    tools = {"get_signal_summary": {
        "lexical_matches": deepcopy(derived[:3]), "past_context": [deepcopy(derived[3])],
        "keyword_query": query_audit(),
        "market": {"ok": False, "reason": "no_market_data", "latest_price": None,
                   "change_pct": 0.0, "window_samples": 0},
        "future_context": [], "archive_view": {
            "status": "ARTICLE_BODY_V1_PRIMARY", "derived_sha256": view["sha256"],
            "preserved_unverified_diagnostics": [], "diagnostics_complete": True,
            "original_records_preserved": True}}}
    reasoning = ns["_fallback_reasoning"]("BTC", checks.QUESTION, tools)
    raw = ns["_assemble_explain_response"](
        SimpleNamespace(asset="BTC", question=checks.QUESTION), reasoning, tools,
        llm_status={"provider": "fallback", "model": None, "fallback": True})
    approval = {"document_id": 1, "original_content_hash": "1" * 64,
                "body_sha256": hashlib.sha256(derived[0]["content_text"].encode()).hexdigest(),
                "excerpt": "reviewed content witness", "question": checks.QUESTION}
    return raw, view, deepcopy(originals), [approval]


def refused(case):
    assert checks.evaluate(*case) == dict.fromkeys(checks.KEYS, False)


def test_exact_installed_fallback_with_reviewed_witness_passes(case):
    assert checks.QUERY_AUDIT == query_audit()
    assert case[0]["answer_metadata"]["source_type"] == "fallback"
    assert checks.evaluate(*case) == dict.fromkeys(checks.KEYS, True)
    # No keyword-based semantic rule: this externally reviewed fixture's headline
    # and excerpt need not contain Bitcoin/liquidations at all.
    assert "Bitcoin" not in case[3][0]["excerpt"]


@pytest.mark.parametrize("key,value", [
    ("current_cause", "A liquidation caused the move. Confidence is uncalibrated."),
    ("past_precedent", "Invented precedent"), ("future_catalyst", "Invented catalyst"),
    ("relevant_past_precedent", "Foreign assertion"), ("question", "Other question"),
    ("asset", "ETH"), ("confidence_calibrated", True), ("execution_disabled", False),
    ("confidence", "malformed"), ("confidence_score", 0.99),
    ("additional_analysis", "Foreign assertion"),
])
def test_foreign_or_malformed_narrative_fails(case, key, value):
    case[0][key] = value
    refused(case)


def test_disclaimer_is_not_sufficient(case):
    case[0]["current_cause"] += " Nonetheless, this proves a crash is imminent."
    refused(case)


def test_probe_envelope_and_known_fallback_metadata(case):
    raw = case[0]
    raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = "single-cited-query-v1"
    raw["answer_metadata"] = {
        "as_of": "2026-10-16T00:00:00Z", "source_type": "fallback", "source_family": "fallback",
        "source_ids": [], "freshness_status": "missing", "age_seconds": None,
        "confidence_label": "Medium",
        "caveat": "Research only. Execution disabled. Trusted evidence timestamps were unavailable.",
        "partial_provenance": True,
        "missing_provenance_reason": "Trusted evidence timestamps were unavailable.",
        "source_name": "Fallback", "source_names": [], "data_timestamp": None,
        "metadata_status": "critical"}
    raw["evidence_bundle"]["market"] = {"ok": False, "reason": "no_market_data",
                                              "latest_price": None, "change_pct": 0.0, "window_samples": 0}
    raw["risk_posture"] = raw["evidence_bundle"]["risk"] = {
        "execution_mode": "DISABLED", "gate": "NO_TRADING", "allow_trading": False,
        "reason": "Phase 1 research copilot mode"}
    assert all(checks.evaluate(*case).values())
    raw["answer_metadata"]["caveat"] += " A liquidation caused the move."
    refused(case)


@pytest.mark.parametrize("target", ["assistant_status", "risk_posture", "operations", "market"])
def test_foreign_auxiliary_assertions_rejected(case, target):
    if target in {"assistant_status", "risk_posture"}:
        case[0][target]["analysis"] = "Foreign assertion"
    else:
        case[0]["evidence_bundle"][target] = {"analysis": "Foreign assertion"}
    refused(case)


def test_integer_zero_is_not_a_disabled_execution_boolean(case):
    case[0]["execution"]["enabled"] = 0
    refused(case)


@pytest.mark.parametrize("value", [True, False, 0, -1, "1", 1.0, None])
def test_cited_ids_are_positive_exact_integers(case, value):
    case[0]["evidence"][0]["document_id"] = value
    refused(case)


@pytest.mark.parametrize("target", ["live", "view", "approval", "bundle"])
def test_duplicate_ids_rejected(case, target):
    raw, view, actual, approvals = case
    if target == "live":
        actual.append(deepcopy(actual[0]))
    elif target == "view":
        view["rows"].append(deepcopy(view["rows"][0]))
    elif target == "approval":
        approvals.append(deepcopy(approvals[0]))
    else:
        raw["evidence_bundle"]["past_context"] *= 2
    refused(case)


@pytest.mark.parametrize("field", ["content_hash", "url", "source", "source_type",
                                    "raw_object_key", "fetched_at", "published_at"])
def test_whole_archive_live_lineage_drift_rejected(case, field):
    case[2][-1][field] = "2026-09-01T00:00:00+00:00" if field.endswith("_at") else "changed"
    refused(case)


@pytest.mark.parametrize("field,value", [
    ("document_id", 99), ("document_id", True), ("original_content_hash", "2" * 64),
    ("body_sha256", "0" * 64), ("body_sha256", "malformed"), ("excerpt", ""),
    ("excerpt", " "), ("excerpt", "not present"), ("excerpt", 1),
    ("question", "What news explains Ethereum liquidations?"), ("reviewed", True),
])
def test_approval_contract_is_exact_and_body_bound(case, field, value):
    case[3][0][field] = value
    refused(case)


@pytest.mark.parametrize("where,field,value", [
    ("evidence", "url", "https://foreign.test"), ("evidence", "source", "foreign"),
    ("evidence", "summary", "Invented headline"), ("bundle", "title", "Invented headline"),
    ("bundle", "url", "https://foreign.test"), ("bundle", "id", True),
])
def test_every_quoted_document_must_match_verified_view(case, where, field, value):
    row = case[0]["evidence"][0] if where == "evidence" else case[0]["evidence_bundle"]["past_context"][0]
    row[field] = value
    refused(case)


@pytest.mark.parametrize("change", ["unverified", "legacy", "archive_hash", "missing_mapping",
                                    "no_approval", "provider", "unquoted_witness", "changed_body"])
def test_missing_or_untrusted_material_evidence_fails(case, change):
    raw, view, actual, approvals = case
    if change == "unverified":
        view["rows"][0]["body_verified"] = False
    elif change == "legacy":
        raw["archive_view"]["status"] = "LEGACY_EXTRACTION_UNVERIFIED"
    elif change == "archive_hash":
        raw["archive_view"]["derived_sha256"] = "a" * 64
    elif change == "missing_mapping":
        view["rows"].pop()
    elif change == "no_approval":
        approvals.clear()
    elif change == "provider":
        raw["assistant_status"]["provider"] = "openai"
    elif change == "unquoted_witness":
        approvals[0].update(document_id=4, original_content_hash="4" * 64)
    else:
        view["rows"][0]["content_text"] += " changed"
    refused(case)


@pytest.mark.parametrize("value", [1, -1, True, "0", float("nan"), float("inf")])
@pytest.mark.parametrize("market", ["market", "market_snapshot"])
def test_market_claims_not_certified(case, market, value):
    case[0]["evidence_bundle"][market] = {"latest_price": value}
    refused(case)


def test_no_context_text_must_be_exact(case):
    case[0]["evidence_bundle"]["past_context"] = []
    case[0]["evidence"] = case[0]["evidence"][:3]
    case[0]["confidence"] = case[0]["confidence_score"] = 0.35
    case[0]["answer_metadata"]["confidence_label"] = "Low"
    case[0]["past_precedent"] = "No indexed historical precedent for BTC was found yet."
    case[0]["relevant_past_precedent"] = case[0]["past_precedent"]
    assert all(checks.evaluate(*case).values())


@pytest.mark.parametrize("where", ["evidence", "bundle"])
def test_hidden_foreign_document_assertions_rejected(case, where):
    row = case[0]["evidence"][0] if where == "evidence" else case[0]["evidence_bundle"]["past_context"][0]
    row["analysis"] = "Liquidations caused the crash."
    refused(case)


def test_forged_citation_order_timestamp_or_kind_rejected(case):
    case[0]["evidence"][0]["timestamp"] = "2026-01-01T00:00:00+00:00"
    refused(case)


def test_bundle_only_witness_and_truncated_keyword_order_rejected(case):
    case[0]["evidence"][0], case[0]["evidence"][-1] = case[0]["evidence"][-1], case[0]["evidence"][0]
    refused(case)


def test_missing_last_live_row_and_boolean_archive_id_rejected(case):
    case[2].pop()
    refused(case)
    case[1]["rows"][0]["id"] = True
    refused(case)


def remote(monkeypatch, case, data=None, failure=None, timer=(0.0, 0.0), alarm_events=None):
    raw, view, actual, approvals = case
    calls = []
    events = alarm_events if alarm_events is not None else []
    old_handler = signal.SIG_IGN

    def getitimer(which):
        assert which == signal.ITIMER_REAL
        events.append("getitimer")
        return timer

    def getsignal(which):
        assert which == signal.SIGALRM
        return old_handler

    def sethandler(which, handler):
        assert which == signal.SIGALRM
        events.append(("handler", handler))
        return old_handler

    def setitimer(which, seconds):
        assert which == signal.ITIMER_REAL
        events.append(("timer", seconds))
        if failure == "arm" and seconds:
            raise ValueError("private alarm setup error")
        return (0.0, 0.0)

    monkeypatch.setattr(signal, "getitimer", getitimer)
    monkeypatch.setattr(signal, "getsignal", getsignal)
    monkeypatch.setattr(signal, "signal", sethandler)
    monkeypatch.setattr(signal, "setitimer", setitimer)

    def module(name, **attrs):
        mod = ModuleType(name)
        mod.__dict__.update(_synthetic=True, **attrs)
        monkeypatch.setitem(sys.modules, name, mod)
        return mod

    def read_archive(path, **kwargs):
        assert str(path) == "/app/memory_retrieval/article_archive"
        assert kwargs == {"required": True, "expected_manifest_sha256": "f" * 64}
        calls.append("archive")
        if failure == "archive":
            raise ValueError("private details must not escape")
        return view

    def check_source_rows(got_view, rows):
        assert got_view is view and rows == actual
        calls.append("lineage")
        if failure == "lineage":
            raise ValueError("private source")

    class Context:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            if failure == "teardown":
                raise RuntimeError("private cleanup error")
            return False

        def transaction(self):
            calls.append("transaction")
            return self

        def cursor(self):
            calls.append("cursor")
            return self

        def execute(self, sql, params=None):
            calls.append((sql, params))
            if failure == "query":
                raise RuntimeError("private DB message")

        def fetchmany(self, size):
            assert size == 501
            return actual

    dict_row = object()

    def connect(url, **kwargs):
        assert url == "synthetic-owned-db"
        assert kwargs == {"connect_timeout": 2, "autocommit": True, "row_factory": dict_row,
                          "options": "-c default_transaction_read_only=on -c statement_timeout=2000"}
        calls.append("connect")
        print("synthetic dependency noise")
        return Context()

    module("shared")
    module("shared.config", get_settings=lambda: SimpleNamespace(database_url="synthetic-owned-db"))
    module("memory_retrieval")
    module("memory_retrieval.article_view", APPROVED_MANIFEST_SHA256="f" * 64,
           read_archive=read_archive, check_source_rows=check_source_rows)
    module("psycopg", connect=connect)
    module("psycopg.rows", dict_row=dict_row)
    payload = json.dumps({"raw": raw, "approvals": approvals}).encode() if data is None else data
    stdout, stderr = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(payload)))
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    exec(checks.EVIDENCE_SCRIPT, {"__name__": "__main__"})
    output = stdout.getvalue()
    result = json.loads(output)
    assert set(result) == set(checks.KEYS) and all(type(v) is bool for v in result.values())
    assert output == json.dumps(result, separators=(",", ":")) + "\n"
    assert "private" not in output and "synthetic" not in output and "https" not in output
    return result, calls


def test_fixed_remote_script_single_parameterized_select_in_readonly_transaction(monkeypatch, case):
    result, calls = remote(monkeypatch, case)
    assert all(result.values())
    assert calls == ["archive", "connect", "transaction", "cursor",
                     ("SET TRANSACTION READ ONLY", None),
                     (checks.SOURCE_SQL, ([1, 2, 3, 4],)), "lineage"]


@pytest.mark.parametrize("failure", ["archive", "lineage", "query", "teardown", "arm"])
def test_remote_errors_have_only_false_json(monkeypatch, case, failure):
    events = []
    result, _ = remote(monkeypatch, case, failure=failure, alarm_events=events)
    assert not any(result.values())
    assert events[-2:] == [("timer", 0.0), ("handler", signal.SIG_IGN)]


@pytest.mark.parametrize("data", [b"{}", b"[]", b"not json", b'{"raw":{},"raw":{},"approvals":[]}',
                                   b'{"raw":NaN,"approvals":[]}', b" " * (checks.MAX_INPUT_BYTES + 1)])
def test_bounded_strict_input_rejected_before_settings_or_database(monkeypatch, case, data):
    result, calls = remote(monkeypatch, case, data=data)
    assert not any(result.values()) and calls == []


def test_real_settings_and_network_are_blocked():
    with pytest.raises(AssertionError):
        __import__("shared.config")
    with pytest.raises(AssertionError):
        socket.create_connection(("example.test", 443))


@pytest.mark.parametrize("envelope", ["question_evidence", "archive_view"])
@pytest.mark.parametrize("value", ["A liquidation caused the crash.", {"cause": "proven"}, [], None])
def test_nested_envelopes_reject_unsupported_narrative(case, envelope, value):
    case[0][envelope]["causal_explanation"] = value
    refused(case)


@pytest.mark.parametrize("field,value", [
    ("original", "What news explains Ethereum liquidations?"), ("query", "Ethereum"),
    ("query", {"text": "Bitcoin liquidations"}), ("mode", "EXACT_QUERY"),
    ("method", "semantic_search"), ("semantic_relevance_verified", True),
    ("semantic_relevance_verified", 0), ("relative_time_interpreted", True),
    ("relative_time_interpreted", 0), ("causal_explanation", "Established cause"),
])
def test_query_audit_must_match_frozen_exact_question_result(case, field, value):
    case[0]["question_evidence"]["keyword_query"][field] = value
    refused(case)


@pytest.mark.parametrize("value", [None, [], "Bitcoin liquidations", {}])
def test_query_audit_is_required_known_object(case, value):
    case[0]["question_evidence"]["keyword_query"] = value
    refused(case)


@pytest.mark.parametrize("envelope,field", [
    ("question_evidence", field) for field in (
        "method", "match_count", "status", "semantic_relevance_verified",
        "causal_relationship_verified", "keyword_query")
] + [("archive_view", field) for field in (
    "status", "derived_sha256", "preserved_unverified_diagnostics", "diagnostics_complete",
    "original_records_preserved")])
def test_known_envelopes_require_actual_assembler_shapes(case, envelope, field):
    del case[0][envelope][field]
    refused(case)


def diagnostic(ident=99):
    return {"document_id": ident, "title": "An unverified diagnostic title, not semantic proof",
            "url": "https://example.test/diagnostic", "status": "UNVERIFIED_ARTICLE_BOUNDARY"}


@pytest.mark.parametrize("complete", [None, False, True])
def test_bounded_unverified_diagnostics_remain_tolerated_not_semantic_proof(case, complete):
    archive = case[0]["archive_view"]
    archive["diagnostics_complete"] = complete
    archive["preserved_unverified_diagnostics"] = [diagnostic()]
    assert all(checks.evaluate(*case).values())
    case[3].clear()
    refused(case)


@pytest.mark.parametrize("field,value", [
    ("document_id", True), ("document_id", 0), ("document_id", "99"),
    ("title", ""), ("title", {"cause": "proven"}), ("title", "x" * 4097),
    ("url", "x" * 8193), ("url", None), ("status", "BODY_VERIFIED"),
    ("causal_explanation", "A liquidation caused the crash."),
])
def test_unverified_diagnostics_have_only_bounded_known_fields(case, field, value):
    row = diagnostic()
    row[field] = value
    case[0]["archive_view"]["preserved_unverified_diagnostics"] = [row]
    refused(case)


@pytest.mark.parametrize("change", ["duplicate", "oversize", "not_list", "known_mismatch",
                                    "complete_integer", "preserved_integer"])
def test_diagnostics_cannot_spoof_archive_identity_or_shape(case, change):
    archive = case[0]["archive_view"]
    if change == "duplicate":
        archive["preserved_unverified_diagnostics"] = [diagnostic(), diagnostic()]
    elif change == "oversize":
        archive["preserved_unverified_diagnostics"] = [diagnostic(i) for i in range(100, 701)]
    elif change == "not_list":
        archive["preserved_unverified_diagnostics"] = {}
    elif change == "known_mismatch":
        archive["preserved_unverified_diagnostics"] = [diagnostic(1)]
    elif change == "complete_integer":
        archive["diagnostics_complete"] = 1
    else:
        archive["original_records_preserved"] = 1
    refused(case)


@pytest.mark.parametrize("timer", [(1.25, 0.0), (0.0, 1.0), (2.0, 3.0)])
def test_occupied_timer_refuses_without_touching_timer_or_handler(monkeypatch, case, timer):
    events = []
    result, calls = remote(monkeypatch, case, timer=timer, alarm_events=events)
    assert not any(result.values()) and calls == []
    assert events == ["getitimer"]


def test_alarm_armed_before_io_and_previous_handler_restored(monkeypatch, case):
    events = []
    result, _ = remote(monkeypatch, case, alarm_events=events)
    assert all(result.values())
    assert events[0] == "getitimer"
    assert events[1][0] == "handler" and events[1][1].__name__ == "_deadline_exit"
    assert events[2:] == [("timer", 8.0), ("timer", 0.0), ("handler", signal.SIG_IGN)]


def test_private_process_actual_eight_second_alarm_only_outputs_false_json():
    # Isolated stdlib-only child, empty environment, no application imports.
    # A stalled synthetic stdin proves the alarm covers I/O before Settings/DB.
    bootstrap = '''
import builtins, socket, sys, time
from types import SimpleNamespace
original_import = builtins.__import__
def forbidden(*args, **kwargs):
    raise AssertionError("offline child")
def guarded(name, *args, **kwargs):
    if name.split(".")[0] in {"shared", "memory_retrieval", "psycopg", "pydantic_settings"}:
        forbidden()
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded
socket.socket = socket.create_connection = socket.getaddrinfo = forbidden
class StalledInput:
    def read(self, size):
        time.sleep(60)
        raise AssertionError("deadline did not exit")
sys.stdin = SimpleNamespace(buffer=StalledInput())
'''
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", bootstrap + f"\nexec({checks.EVIDENCE_SCRIPT!r})\n"],
        env={}, capture_output=True, timeout=10, check=False)
    elapsed = time.monotonic() - started
    assert completed.returncode == 0 and completed.stdout == checks.FAILURE_OUTPUT
    assert completed.stderr == b"" and 7.5 <= elapsed < 10
