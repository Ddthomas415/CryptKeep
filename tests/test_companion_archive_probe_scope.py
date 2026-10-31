"""Offline synthetic SQL boundary/ASGI proof, not actual PostgreSQL or live replay."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace

import pytest

from phase1_research_copilot.memory_retrieval import article_view
from scripts.research import companion_evidence_checks as checks
from tests.test_companion_probe_policy import AUTH, HEADER, PROFILE, loaded, request, run
from tests.test_companion_running_update import harness, run as run_update

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research/companion_article_body_v1_20261011_gd1abqx9"


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("offline scope test attempted external operation")
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def saved_view():
    return article_view.read_archive(ARCHIVE, required=True,
        expected_manifest_sha256=article_view.APPROVED_MANIFEST_SHA256)


def test_ordinary_sql_is_byte_identical_and_frozen_union_is_absent():
    prior = ROOT / "docs/review_artifacts/companion_installed_imports_targeted_20261018/frozen/memory_retrieval/memory_retrieval/article_view.py"
    raw = prior.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "9ba354456ade0c74d0103e31557d5c5bd7031ad6aad5ed41e5593c9ebaf7b767"
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "CTE" for t in n.targets))
    assert article_view.CTE == ast.literal_eval(node.value)
    assert "UNION ALL" in article_view.CTE
    assert "UNION ALL" not in article_view.FROZEN_CTE
    assert "r.body_verified" in article_view.FROZEN_CTE
    assert "lineage_ok" in article_view.FROZEN_CTE


@pytest.mark.parametrize("frozen", [False, True])
def test_scope_precedes_query_rank_and_limit_and_preserves_parameters(frozen):
    view = saved_view()
    calls = []
    class DB:
        def fetch_all(self, sql, params):
            calls.append((sql, params))
            return [{"source_valid": True, "rows": []}]
    query = "SELECT * FROM documents WHERE title=%s ORDER BY id LIMIT %s"
    article_view.fetch_from_view(DB(), view, query, ("untrusted question", 3), frozen_only=frozen)
    sql, params = calls[0]
    assert sql.startswith(article_view.FROZEN_CTE if frozen else article_view.CTE)
    assert sql.index("lineage_ok") < sql.index(query)
    assert "untrusted question" not in sql and params[1:] == ("untrusted question", 3)
    assert json.loads(params[0]) == view["rows"]


@pytest.mark.parametrize("bad", [None, 0, "false"])
def test_invalid_scope_refuses_before_sql(bad):
    class DB:
        def fetch_all(self, *args):
            pytest.fail("invalid scope reached SQL")
    with pytest.raises(ValueError, match="invalid_archive_scope"):
        article_view.fetch_from_view(DB(), saved_view(), "SELECT 1", (), frozen_only=bad)


def retrieval(loaded, monkeypatch, *, missing=False, drift=False):
    memory, view, calls = loaded.memory_retrieval, saved_view(), []
    by_id = {r["id"]: r for r in view["rows"]}
    live = {**deepcopy(by_id[5]), "id": 9001, "title": "Bitcoin liquidations new live story"}
    def fetch(sql, params):
        calls.append(sql)
        if "FROM market_ticks" in sql:
            return []
        if sql.startswith("SELECT id, content_hash"):
            rows = deepcopy(list(view["original"].values()))
            if drift:
                rows[0]["content_hash"] = "f" * 64
            return rows
        if sql.startswith("SELECT id AS document_id"):
            return []
        assert sql.startswith("WITH repair AS")
        frozen = "UNION ALL" not in sql
        if "AS lexical_rank" in sql:
            rows = [by_id[i] for i in [5, 47, 18]] if frozen else [live, by_id[5], by_id[47]]
            return [{"source_valid": True, "rows": deepcopy(rows)}]
        if "WHERE id = ANY" in sql or "timeline_tag = 'present'" in sql:
            return [{"source_valid": True, "rows": [] if frozen else [deepcopy(live)]}]
        return [{"source_valid": True, "rows": []}]
    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    monkeypatch.setattr(memory, "read_archive", lambda *a, **kw: None if missing else deepcopy(view))
    monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(
        search=lambda **kw: [SimpleNamespace(id=9001)]))
    async def audit(*a, **kw):
        return None
    monkeypatch.setattr(memory, "emit_audit_event", audit)
    return memory, view, calls


def call(memory, *, probe):
    return run(request(memory.app, "/v1/memory/retrieve",
        headers={**AUTH, **({HEADER: PROFILE} if probe else {})},
        payload={"asset": "BTC", "question": checks.QUESTION, "limit": 3}))


@pytest.mark.parametrize("probe", [False, True])
def test_real_handler_keeps_live_route_but_scopes_every_probe_document_query(loaded, monkeypatch, probe):
    memory, view, calls = retrieval(loaded, monkeypatch)
    response = call(memory, probe=probe)
    assert response.status_code == 200
    payload = response.json()
    assert [r["id"] for r in payload["lexical_matches"]] == ([5, 47, 18] if probe else [9001, 5, 47])
    assert [r["id"] for r in payload["vector_matches"]] == ([] if probe else [9001])
    queries = [sql for sql in calls if sql.startswith("WITH repair AS")]
    assert len(queries) == 5
    assert all(("UNION ALL" not in sql) == probe for sql in queries)
    if probe:
        tools = {"get_signal_summary": payload, "get_risk_summary": {
            "execution_mode": "DISABLED", "gate": "NO_TRADING", "allow_trading": False,
            "reason": "Phase 1 research copilot mode"}}
        orchestrator = loaded.orchestrator
        req = orchestrator.ExplainRequest(asset="BTC", question=checks.QUESTION)
        raw = orchestrator._assemble_explain_response(req,
            orchestrator._fallback_reasoning("BTC", checks.QUESTION, tools), tools,
            llm_status={"provider": "fallback", "model": None, "fallback": True})
        raw["probe_protocol"] = raw["assistant_status"]["probe_protocol"] = PROFILE
        approvals = json.loads((ROOT / "docs/review_artifacts/companion_evidence_packet_v2_20261024/topical_candidates.json").read_bytes())
        assert all(checks.evaluate(raw, view, deepcopy(list(view["original"].values())), approvals).values())


@pytest.mark.parametrize("probe", [False, True])
def test_missing_archive_fails_only_archival_probe(loaded, monkeypatch, probe):
    memory, _, _ = retrieval(loaded, monkeypatch, missing=True)
    if not probe:
        monkeypatch.setattr(memory.db, "fetch_all", lambda *a: [])
        monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(search=lambda **kw: []))
    response = call(memory, probe=probe)
    assert response.status_code == (503 if probe else 200)


@pytest.mark.parametrize("probe", [False, True])
def test_lineage_drift_still_refuses(loaded, monkeypatch, probe):
    memory, _, _ = retrieval(loaded, monkeypatch, drift=True)
    assert call(memory, probe=probe).status_code == 503


@pytest.mark.parametrize("value,outcome", [(True, "complete"), (False, "complete"),
    (None, "invalid_shape"), ("PRIVATE", "invalid_shape")])
def test_verifier_result_is_sanitized_before_acceptance_or_recovery(value, outcome):
    h = harness()
    _, _, receipt, _, runtime = h
    runtime.evidence_result["content_hash"] = value
    result = run_update(h)
    event = next(e for e in receipt.events if e["phase"] == "evidence_verification_checks")
    details = event["installation_evidence"]
    assert details["outcome"] == outcome
    assert set(details["checks"]) == set(checks.KEYS)
    assert all(type(v) is bool for v in details["checks"].values())
    assert details["checks"]["content_hash"] is (value is True)
    assert "PRIVATE" not in json.dumps(receipt.events)
    assert result["query_passed"] is (value is True)
    if value is not True:
        assert result["rollback_verified"]
        assert receipt.events.index(event) < next(i for i,e in enumerate(receipt.events)
                                                 if e["phase"] == "installation_failed")


def test_verifier_exception_is_recorded_without_payload_or_retry():
    h = harness()
    _, backend, receipt, _, runtime = h
    calls = []
    def fail(raw):
        calls.append(True)
        raise RuntimeError("PRIVATE_EXCEPTION")
    runtime.verify_evidence = fail
    result = run_update(h)
    assert calls == [True] and not result["query_passed"] and result["rollback_verified"]
    event = next(e for e in receipt.events if e["phase"] == "evidence_verification_checks")
    assert event["installation_evidence"]["outcome"] == "exception_or_timeout"
    assert "PRIVATE_EXCEPTION" not in json.dumps(receipt.events)


@pytest.mark.parametrize("bad", ["missing", "extra", "list", "bool"])
def test_malformed_verifier_result_never_leaks_or_approves(bad):
    h = harness()
    _, _, receipt, _, runtime = h
    if bad == "missing":
        runtime.evidence_result.pop("content_hash")
    elif bad == "extra":
        runtime.evidence_result["PRIVATE_KEY"] = "PRIVATE_VALUE"
    else:
        runtime.evidence_result = [] if bad == "list" else True
    result = run_update(h)
    assert not result["query_passed"] and result["rollback_verified"]
    event = next(e for e in receipt.events if e["phase"] == "evidence_verification_checks")
    assert event["installation_evidence"]["outcome"] == "invalid_shape"
    assert "PRIVATE" not in json.dumps(receipt.events)


def test_diagnostic_write_failure_cannot_claim_query_success():
    h = harness()
    _, backend, receipt, _, _ = h
    original = receipt.write
    def write(event):
        if event["phase"] == "evidence_verification_checks":
            raise RuntimeError("PRIVATE_WRITE_ERROR")
        original(event)
    receipt.write = write
    result = run_update(h)
    assert not result["query_passed"] and not result["receipt_complete"]
    assert result["rollback_verified"]
    assert sum(method == "runtime_explain" for method, _ in backend.calls) == 1
    assert "PRIVATE_WRITE_ERROR" not in json.dumps(receipt.events)
