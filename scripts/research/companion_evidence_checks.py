"""Offline helper; importing this file never loads settings or opens a service.

Topical support means ONLY that an externally reviewed, exact-question content
witness matches an approved archived body and is actually cited. Approvals are
trusted operator inputs under a separately reviewed contract, not keyword-derived
semantic judgments, cryptographic attestations, or causal proof. No approval
generator is supplied. The five booleans do not certify auxiliary operational
metadata, freshness, market facts, profitability, or runtime readiness.

EVIDENCE_SCRIPT is fixed code for a separately reviewed bounded transport running
inside memory. Credentials stay there. Its private process has an eight-second
SIGALRM work cap (including DB teardown); an occupied timer is left untouched and
refused. Parent must still discard stderr and bound launch/output/transport.

DIAGNOSTIC_EVIDENCE_SCRIPT additionally returns a closed stage/code envelope.
Stages identify the first failing group, not a specific predicate or private
value. A hard deadline identifies the stage interrupted, not a semantic verdict.
Legacy evaluate()/EVIDENCE_SCRIPT retain the five-Boolean interface.
"""
import hashlib
import inspect
import json
import os
import re
from datetime import datetime


QUESTION = "What news explains Bitcoin liquidations?"
QUERY_AUDIT = {
    "original": QUESTION, "query": "Bitcoin liquidations", "mode": "CONVERSATIONAL_FILLER_REMOVED",
    "method": "english_conversational_scaffolding_v1", "semantic_relevance_verified": False,
    "relative_time_interpreted": False,
}
MAX_INPUT_BYTES = 262_144
KEYS = ("persisted_identity", "article_view_mapping", "content_hash",
        "topical_support", "causal_limits")
FAILURE_OUTPUT = (json.dumps(dict.fromkeys(KEYS, False), separators=(",", ":")) + "\n").encode("ascii")
DIAGNOSTIC_STAGES = (
    "timer", "input_read", "input_parse", "imports", "archive_load", "archive_index",
    "db_connect", "db_transaction", "db_query", "source_lineage", "db_teardown", "timer_cleanup",
    "input", "persisted_identity", "archive_envelope", "response_contract", "query_contract",
    "citations", "bundle_contract", "bundle_market", "bundle_documents", "metadata", "narrative", "witnesses", "complete",
)
DIAGNOSTIC_CODES = ("ok", "rejected", "error", "deadline")
DIAGNOSTIC_DEADLINES = {
    stage: (json.dumps({"checks": dict.fromkeys(KEYS, False),
                       "diagnostic": {"stage": stage, "code": "deadline"}},
                      separators=(",", ":")) + "\n").encode("ascii")
    for stage in DIAGNOSTIC_STAGES if stage != "complete"
}
SOURCE_SQL = (
    "SELECT id, content_hash, url, source, source_type, raw_object_key, "
    "published_at, fetched_at FROM public.documents WHERE id = ANY(%s)"
)


class _EvidenceRejected(ValueError):
    pass


def _require(condition):
    if not condition:
        raise _EvidenceRejected("evidence_rejected")


def _stage(state, name):
    if state is not None:
        state["stage"] = name


def diagnostic_valid(value):
    return (type(value) is dict and set(value) == {"stage", "code"}
            and type(value["stage"]) is str and value["stage"] in DIAGNOSTIC_STAGES
            and type(value["code"]) is str and value["code"] in DIAGNOSTIC_CODES
            and ((value["stage"] == "complete") == (value["code"] == "ok")))


def diagnostic_result_valid(value):
    if (type(value) is not dict or set(value) != {"checks", "diagnostic"}
            or type(value["checks"]) is not dict or set(value["checks"]) != set(KEYS)
            or any(type(v) is not bool for v in value["checks"].values())
            or not diagnostic_valid(value["diagnostic"])):
        return False
    return (all(value["checks"].values()) if value["diagnostic"]["code"] == "ok"
            else not any(value["checks"].values()))


def _failed(state, error):
    return {"checks": dict.fromkeys(KEYS, False), "diagnostic": {
        "stage": state["stage"], "code": "rejected" if isinstance(error, _EvidenceRejected) else "error"}}


def _positive_id(value):
    return type(value) is int and 0 < value <= 9_223_372_036_854_775_807


def _hash(value):
    return type(value) is str and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def _indexed(rows):
    _require(type(rows) is list and 0 < len(rows) <= 500)
    result = {}
    for row in rows:
        _require(type(row) is dict and _positive_id(row.get("id")))
        _require(row["id"] not in result)
        result[row["id"]] = row
    return result


def _time(value):
    return None if value is None else datetime.fromisoformat(str(value))


def _archive_envelope(archive, view):
    _require(type(archive) is dict and set(archive) == {
        "status", "derived_sha256", "preserved_unverified_diagnostics",
        "diagnostics_complete", "original_records_preserved"})
    _require(archive["status"] == "ARTICLE_BODY_V1_PRIMARY"
             and _hash(view.get("sha256")) and archive["derived_sha256"] == view["sha256"])
    _require(archive["original_records_preserved"] is True
             and (archive["diagnostics_complete"] is None
                  or type(archive["diagnostics_complete"]) is bool))
    diagnostics = archive["preserved_unverified_diagnostics"]
    _require(type(diagnostics) is list and len(diagnostics) <= 600)
    seen = set()
    for diagnostic in diagnostics:
        _require(type(diagnostic) is dict and set(diagnostic) == {"document_id", "title", "url", "status"})
        ident = diagnostic["document_id"]
        _require(_positive_id(ident) and ident not in seen)
        seen.add(ident)
        _require(diagnostic["status"] == "UNVERIFIED_ARTICLE_BOUNDARY")
        for field, bound in (("title", 4096), ("url", 8192)):
            text = diagnostic[field]
            _require(type(text) is str and bool(text.strip()) and len(text) <= bound)
            if ident in view["original"]:
                _require(text == view["original"][ident][field])
        # Newer diagnostic IDs are intentionally outside the approved snapshot.
        # Only their shape/bounds are checked, never their truth or semantics;
        # they cannot supply citations, approvals, topical or causal support.


def _document(row, mapped, *, citation=False):
    _require(type(row) is dict)
    ident = row.get("document_id" if citation else "id")
    _require(_positive_id(ident) and ident in mapped)
    stored = mapped[ident]
    _require(stored.get("body_verified") is True)
    for key in ("url", "source"):
        _require(type(stored.get(key)) is str and bool(stored[key].strip()))
        _require(row.get(key) == stored[key])
    title = stored.get("title")
    _require(type(title) is str and bool(title.strip()))
    _require(row.get("summary" if citation else "title") == title)
    if citation:
        common = {"id", "document_id", "url", "type", "source", "timestamp", "summary"}
        extra = ({"retrieval_method", "lexical_rank", "semantic_relevance_verified"}
                 if row.get("type") == "keyword_match" else {"relevance"})
        _require(set(row) == common | extra)
        _require(_time(row["timestamp"]) == _time(stored.get("published_at") or stored["fetched_at"]))
    else:
        _require(not set(row) - set(stored) - {"lexical_rank"})
        for key in set(row) & set(stored):
            if key in {"published_at", "fetched_at"}:
                _require(_time(row[key]) == _time(stored[key]))
            else:
                _require(row[key] == stored[key])
    if "lexical_rank" in row:
        rank = row["lexical_rank"]
        _require(rank is None or (type(rank) in (int, float) and rank >= 0))
    return ident


def _evaluate(raw, view, actual, approvals, state=None):
    _stage(state, "input")
    _require(type(raw) is dict and type(view) is dict)
    # Bound pure calls too, and reject non-JSON/non-finite claim values.
    _require(len(json.dumps({"raw": raw, "approvals": approvals},
                            allow_nan=False).encode()) <= MAX_INPUT_BYTES)
    _stage(state, "persisted_identity")
    mapped = _indexed(view["rows"])
    originals = view["original"]
    _require(type(originals) is dict and all(_positive_id(i) for i in originals))
    _require(set(mapped) == set(originals))
    live = _indexed(actual)
    _require(set(live) == set(originals))
    for ident, prior in originals.items():
        _require(type(prior) is dict and type(prior.get("id")) is int
                 and prior["id"] == ident and _hash(prior.get("content_hash")))
        derived = mapped[ident]
        _require(derived.get("original_content_hash") == prior["content_hash"])
        _require(type(derived.get("content_text")) is str)
        for key in ("content_hash", "url", "source", "source_type", "raw_object_key"):
            _require(live[ident][key] == prior[key])
        for key in ("url", "source", "source_type", "raw_object_key"):
            _require(derived[key] == prior[key])
        for key in ("published_at", "fetched_at"):
            _require(_time(live[ident][key]) == _time(prior[key])
                     == _time(derived[key]))

    _stage(state, "archive_envelope")
    archive = raw["archive_view"]
    _archive_envelope(archive, view)
    _stage(state, "response_contract")
    _require(raw.get("ok") is True and raw.get("asset") == "BTC"
             and raw.get("question") == QUESTION)
    status = raw["assistant_status"]
    _require(type(status) is dict and status.get("provider") == "fallback"
             and status.get("fallback") is True and status.get("model") is None)
    _require(not set(status) - {"provider", "fallback", "model", "probe_protocol"})
    for envelope in (raw, status):
        if "probe_protocol" in envelope:
            _require(envelope["probe_protocol"] == "single-cited-query-v1")
    _require(raw.get("confidence_calibrated") is False
             and raw.get("confidence_basis") == "context_presence_heuristic")
    _require(raw.get("execution_disabled") is True
             and raw.get("execution") == {"enabled": False, "reason": "Phase 1 research copilot only"}
             and raw.get("risk_note") == "Research only. Execution disabled.")
    _require(raw["execution"]["enabled"] is False)
    allowed = {"ok", "asset", "question", "current_cause", "past_precedent",
               "relevant_past_precedent", "future_catalyst", "confidence", "confidence_score",
               "confidence_calibrated", "confidence_basis", "question_evidence", "archive_view",
               "risk_note", "execution_disabled", "evidence", "evidence_bundle",
               "answer_metadata", "risk_posture", "execution", "assistant_status", "probe_protocol"}
    _require(not set(raw) - allowed)
    _stage(state, "query_contract")
    qe = raw["question_evidence"]
    _require(type(qe) is dict and set(qe) == {
        "method", "match_count", "status", "semantic_relevance_verified",
        "causal_relationship_verified", "keyword_query"})
    _require(qe.get("method") == "english_keyword_full_text"
             and qe.get("status") == "KEYWORD_MATCHES"
             and type(qe.get("match_count")) is int and 0 < qe["match_count"] <= 20
             and qe.get("semantic_relevance_verified") is False
             and qe.get("causal_relationship_verified") is False)
    query = qe["keyword_query"]
    _require(type(query) is dict and query == QUERY_AUDIT
             and query["semantic_relevance_verified"] is False
             and query["relative_time_interpreted"] is False)

    _stage(state, "citations")
    evidence = raw["evidence"]
    _require(type(evidence) is list and 0 < len(evidence) <= 6)
    citation_names, keyword_ids, cited = set(), [], set()
    for item in evidence:
        ident = _document(item, mapped, citation=True)
        name = item.get("id")
        _require(type(name) is str and name not in citation_names)
        citation_names.add(name)
        cited.add(ident)
        kind = item.get("type")
        _require(kind in {"keyword_match", "news", "past", "future"})
        if kind == "keyword_match":
            _require(name == f"keyword_{ident}" and ident not in keyword_ids
                     and item.get("retrieval_method") == "english_keyword_full_text"
                     and item.get("semantic_relevance_verified") is False)
            keyword_ids.append(ident)
    _require(len(keyword_ids) == min(3, qe["match_count"]))
    _require(all(item["type"] == "keyword_match" for item in evidence[:len(keyword_ids)]))

    _stage(state, "bundle_contract")
    bundle = raw["evidence_bundle"]
    _require(type(bundle) is dict)
    document_groups = ("recent_news", "past_context", "future_context", "vector_matches")
    auxiliary = {"market", "market_snapshot", "risk", "operations", "crypto_edges",
                 "latest_live_crypto_edges", "crypto_edge_changes", "crypto_edge_staleness",
                 "crypto_edge_digest"}
    _require(not set(bundle) - set(document_groups) - auxiliary)
    _stage(state, "bundle_market")
    for key in ("market", "market_snapshot"):
        market = bundle.get(key, {})
        _require(type(market) is dict)
        _require(not set(market) - {"latest_price", "price", "ok", "reason", "change_pct", "window_samples"})
        for field in ("latest_price", "price"):
            value = market.get(field)
            _require(value is None or (type(value) in (int, float) and value == 0))
        if "ok" in market:
            _require(market["ok"] is False)
        if "reason" in market:
            if market["reason"] == "excluded_by_archival_probe":
                _require(key == "market" and set(market) == {"ok", "reason", "latest_price", "change_pct", "window_samples"}
                         and raw.get("probe_protocol") == "single-cited-query-v1"
                         and status.get("probe_protocol") == "single-cited-query-v1"
                         and market["latest_price"] is None and type(market["window_samples"]) is int)
            else:
                _require(market["reason"] == "no_market_data")
        for field in ("change_pct", "window_samples"):
            if field in market:
                _require(type(market[field]) in (int, float) and market[field] == 0)
    _stage(state, "bundle_contract")
    for key in auxiliary - {"market", "market_snapshot", "risk"}:
        _require(bundle.get(key, {}) == {})
    risk = bundle.get("risk", {})
    _require(risk == {} or risk == {"execution_mode": "DISABLED", "gate": "NO_TRADING",
                                   "allow_trading": False, "reason": "Phase 1 research copilot mode"})
    if risk:
        _require(risk["allow_trading"] is False)
    _require(raw.get("risk_posture", {}) == risk)
    _stage(state, "bundle_documents")
    for group in document_groups:
        docs = bundle.get(group, [])
        _require(type(docs) is list and len(docs) <= 3)
        ids = [_document(row, mapped) for row in docs]
        _require(len(ids) == len(set(ids)))
    expected_citations = [(f"keyword_{ident}", "keyword_match", ident) for ident in keyword_ids]
    for group, kind, limit in (("recent_news", "news", 2), ("past_context", "past", 1),
                               ("future_context", "future", 1)):
        expected_citations.extend((f"{kind}_{n}", kind, row["id"])
                                  for n, row in enumerate(bundle.get(group, [])[:limit], 1))
    _require([(item["id"], item["type"], item["document_id"]) for item in evidence]
             == expected_citations[:6])
    for item in evidence:
        if item["type"] != "keyword_match":
            relevance = {"news": 0.84, "past": 0.72, "future": 0.68}[item["type"]]
            _require(type(item["relevance"]) in (int, float) and item["relevance"] == relevance)
    confidence = 0.35 + (0.2 if bundle.get("recent_news") else 0)
    confidence += (0.1 if bundle.get("past_context") else 0) + (0.1 if bundle.get("future_context") else 0)
    edges = bundle.get("crypto_edges", {})
    _require(type(edges) is dict)
    confidence += 0.05 if edges.get("has_any_data") else 0
    for key in ("confidence", "confidence_score"):
        _require(type(raw.get(key)) in (int, float) and raw[key] == round(confidence, 3))
    _stage(state, "metadata")
    metadata = raw.get("answer_metadata", {})
    _require(type(metadata) is dict)
    if metadata:
        _require(type(metadata.get("as_of")) is str and _time(metadata["as_of"]).tzinfo is not None)
        expected_metadata = {
            "as_of": metadata["as_of"], "source_type": "fallback", "source_family": "fallback",
            "source_ids": [], "freshness_status": "missing", "age_seconds": None,
            "confidence_label": "Medium" if round(confidence, 3) >= 0.45 else "Low",
            "caveat": "Research only. Execution disabled. Trusted evidence timestamps were unavailable.",
            "partial_provenance": True,
            "missing_provenance_reason": "Trusted evidence timestamps were unavailable.",
            "source_name": "Fallback", "source_names": [], "data_timestamp": None,
            "metadata_status": "critical",
        }
        _require(metadata == expected_metadata and metadata["partial_provenance"] is True)

    _stage(state, "narrative")
    current = (
        "Current market context for BTC is unavailable. No price direction or cause is established."
        " Question-matched archived headlines (keyword overlap only): "
        + "; ".join(mapped[i]["title"].strip() for i in keyword_ids)
        + ". These matches do not establish a cause of the price move."
        " Confidence is an uncalibrated context-availability heuristic, not a probability of correctness."
        " Search uses the versioned article-body view; unverified layouts are retained as diagnostics, not primary evidence."
    )
    _require(raw.get("current_cause") == current)
    for group, key, empty in (
        ("past_context", "past_precedent", "No indexed historical precedent for BTC was found yet."),
        ("future_context", "future_catalyst", "No explicit forward catalyst for BTC is currently indexed."),
    ):
        docs = bundle.get(group, [])
        _require(raw.get(key) == (docs[0]["title"] if docs else empty))
    _require(raw.get("relevant_past_precedent") == raw["past_precedent"])

    _stage(state, "witnesses")
    _require(type(approvals) is list and 0 < len(approvals) <= 500)
    approved_ids, witnesses = set(), set()
    for approval in approvals:
        _require(type(approval) is dict and set(approval) == {
            "document_id", "original_content_hash", "body_sha256", "excerpt", "question"})
        ident = approval["document_id"]
        _require(_positive_id(ident) and ident in mapped and ident not in approved_ids)
        approved_ids.add(ident)
        row = mapped[ident]
        _require(row.get("body_verified") is True and approval["question"] == QUESTION)
        _require(_hash(approval["original_content_hash"]) and _hash(approval["body_sha256"]))
        _require(approval["original_content_hash"] == row["original_content_hash"]
                 == live[ident]["content_hash"])
        _require(approval["body_sha256"].lower()
                 == hashlib.sha256(row["content_text"].encode("utf-8")).hexdigest())
        excerpt = approval["excerpt"]
        _require(type(excerpt) is str and bool(excerpt.strip())
                 and excerpt in row["content_text"])
        if ident in cited and ident in keyword_ids:
            witnesses.add(ident)
    _require(bool(witnesses))
    return dict.fromkeys(KEYS, True)


def evaluate(raw, view, actual, approvals):
    """Pure fail-closed evaluation of caller-supplied snapshots, no I/O.

    The remote entrypoint additionally authenticates the archive manifest and
    calls the installed check_source_rows inside the read-only DB transaction.
    A pure call is not proof that either input came from a running service.
    """
    try:
        return _evaluate(raw, view, actual, approvals)
    except BaseException:
        return dict.fromkeys(KEYS, False)


def evaluate_diagnostic(raw, view, actual, approvals, state=None):
    state = {"stage": "input"} if state is None else state
    try:
        checks = _evaluate(raw, view, actual, approvals, state)
        return {"checks": checks, "diagnostic": {"stage": "complete", "code": "ok"}}
    except BaseException as error:
        return _failed(state, error)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _deadline_exit(signum, frame):
    # Only for the dedicated read-only child. Hard exit avoids catching the
    # deadline in evaluate(), or hanging in connection rollback/close handlers.
    try:
        os.write(1, FAILURE_OUTPUT)
    finally:
        os._exit(0)


def _remote_main(diagnostic=False):
    import contextlib
    import signal
    import sys
    from pathlib import Path

    result = dict.fromkeys(KEYS, False)
    state = {"stage": "timer"}
    envelope = None
    handler_installed = False
    previous_handler = None
    try:
        _require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0))
        previous_handler = signal.getsignal(signal.SIGALRM)
        def diagnostic_deadline(signum, frame):
            # Fixed precomputed bytes only: no exception/payload formatting in
            # the signal path, and hard exit still includes DB teardown.
            try:
                os.write(1, DIAGNOSTIC_DEADLINES[state["stage"]])
            finally:
                os._exit(0)

        signal.signal(signal.SIGALRM, diagnostic_deadline if diagnostic else _deadline_exit)
        handler_installed = True
        signal.setitimer(signal.ITIMER_REAL, 8.0)
        # Installed modules must not leak logs/config/records into stdout.
        with contextlib.redirect_stdout(sys.stderr):
            _stage(state, "input_read")
            data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            _stage(state, "input_parse")
            _require(len(data) <= MAX_INPUT_BYTES)
            payload = json.loads(data, object_pairs_hook=_unique_object,
                                 parse_constant=lambda _: _require(False))
            _require(type(payload) is dict and set(payload) == {"raw", "approvals"})
            _require(type(payload["raw"]) is dict and type(payload["approvals"]) is list)
            _stage(state, "imports")
            from shared.config import get_settings
            from memory_retrieval.article_view import (
                APPROVED_MANIFEST_SHA256, read_archive, check_source_rows,
            )
            import psycopg
            from psycopg.rows import dict_row

            _stage(state, "archive_load")
            _require(_hash(APPROVED_MANIFEST_SHA256))
            view = read_archive(Path("/app/memory_retrieval/article_archive"), required=True,
                                expected_manifest_sha256=APPROVED_MANIFEST_SHA256)
            _stage(state, "archive_index")
            mapped = _indexed(view["rows"])
            _require(set(mapped) == set(view["original"])
                     and all(_positive_id(i) for i in view["original"]))
            _stage(state, "db_connect")
            with psycopg.connect(get_settings().database_url, connect_timeout=2,
                                  options="-c default_transaction_read_only=on -c statement_timeout=2000",
                                  row_factory=dict_row, autocommit=True) as connection:
                _stage(state, "db_transaction")
                with connection.transaction():
                    _stage(state, "db_query")
                    with connection.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.execute(SOURCE_SQL, (list(view["original"]),))
                        actual = cursor.fetchmany(501)
                        _stage(state, "db_teardown")
                    _stage(state, "source_lineage")
                    check_source_rows(view, actual)
                    if diagnostic:
                        envelope = evaluate_diagnostic(payload["raw"], view, actual, payload["approvals"], state)
                        result = envelope["checks"]
                    else:
                        result = evaluate(payload["raw"], view, actual, payload["approvals"])
                    _stage(state, "db_teardown")
    except BaseException as error:
        result = dict.fromkeys(KEYS, False)
        if diagnostic and (envelope is None or envelope["diagnostic"]["code"] == "ok"):
            envelope = _failed(state, error)
    finally:
        if handler_installed:
            try:
                _stage(state, "timer_cleanup")
                signal.setitimer(signal.ITIMER_REAL, 0.0)
                signal.signal(signal.SIGALRM, previous_handler)
            except BaseException as error:
                result = dict.fromkeys(KEYS, False)
                if diagnostic and (envelope is None or envelope["diagnostic"]["code"] == "ok"):
                    envelope = _failed(state, error)
    sys.stdout.write(json.dumps(envelope if diagnostic else result, separators=(",", ":")) + "\n")


# Only this module's reviewed helpers are serialized, never application source,
# approvals, configuration, credentials, or interpolated raw explanation data.
_SCRIPT = (
    "import hashlib, json, os, re\nfrom datetime import datetime\n"
    + "\n".join(f"{name} = {value!r}" for name, value in (
        ("QUESTION", QUESTION), ("MAX_INPUT_BYTES", MAX_INPUT_BYTES),
        ("QUERY_AUDIT", QUERY_AUDIT), ("FAILURE_OUTPUT", FAILURE_OUTPUT),
        ("KEYS", KEYS), ("SOURCE_SQL", SOURCE_SQL), ("DIAGNOSTIC_STAGES", DIAGNOSTIC_STAGES),
        ("DIAGNOSTIC_CODES", DIAGNOSTIC_CODES), ("DIAGNOSTIC_DEADLINES", DIAGNOSTIC_DEADLINES))) + "\n"
    + inspect.getsource(_EvidenceRejected) + "\n"
    + "\n".join(inspect.getsource(fn) for fn in (
        _require, _stage, _failed, diagnostic_valid, diagnostic_result_valid,
        _positive_id, _hash, _indexed, _time, _archive_envelope, _document, _evaluate,
        evaluate, evaluate_diagnostic, _unique_object, _deadline_exit, _remote_main))
)
EVIDENCE_SCRIPT = _SCRIPT + "\n_remote_main()\n"
DIAGNOSTIC_EVIDENCE_SCRIPT = _SCRIPT + "\n_remote_main(True)\n"
