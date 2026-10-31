"""Saved sanitized receipt only; no replay, live query or response reconstruction."""
import hashlib
import json
from pathlib import Path

from scripts.research.companion_evidence_checks import diagnostic_result_valid


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RECEIPT_SHA = "ab587bb2fa1a56818b2c70f45cafc29b543e4ae3efba83c006ac696021d91b4a"


def diagnose():
    receipt = HERE / "receipt.jsonl"
    original = ROOT / ".cbp_state/runtime/companion_cutovers/workerprep20261026v6h/receipt.jsonl"
    raw = receipt.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECEIPT_SHA and raw == original.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    query = [r for r in rows if r["phase"] == "query_diagnostics"]
    checks = [r for r in rows if r["phase"] == "evidence_verification_checks"]
    assert len(query) == len(checks) == 1
    events = query[0]["installation_evidence"]["events"]
    result = checks[0]["installation_evidence"]
    assert result["outcome"] == "complete" and result["shape_valid"] is True
    assert diagnostic_result_valid({"checks": result["checks"], "diagnostic": result["diagnostic"]})
    assert result["diagnostic"] == {"stage": "bundle_market", "code": "rejected"}
    assert all(v is False for v in result["checks"].values())
    assert any(e["route"] == "companion" and e["stage"] == "normalization" and e["outcome"] == "accepted" for e in events)
    assert not any(e["outcome"] in {"foreign_asset", "static_fallback"} for e in events)
    response = next(e["response"] for e in events if e["route"] == "companion" and e["stage"] == "transport")
    archive = ROOT / "research/companion_article_body_v1_20261011_gd1abqx9/original_snapshot.json"
    indexed = {hashlib.sha256(str(r["id"]).encode()).hexdigest(): r for r in json.loads(archive.read_bytes())}
    correlation = []
    for item in response["citation_hashes"]:
        match = indexed[item["document_id_sha256"]]
        correlation.append({"document_id": match["id"],
            "url_hash_matches": hashlib.sha256(match["url"].encode()).hexdigest() == item["url_sha256"]})
    assert [r["document_id"] for r in correlation] == [5, 47, 18, 5, 26]
    assert all(r["url_hash_matches"] for r in correlation)
    paths = [receipt, original, archive, Path(__file__), HERE / "outcome.json",
        ROOT / "scripts/research/companion_evidence_checks.py",
        ROOT / "scripts/research/companion_runtime_adapter.py",
        ROOT / "scripts/research/companion_installer.py",
        ROOT / "phase1_research_copilot/shared/tools.py",
        ROOT / "phase1_research_copilot/orchestrator/main.py"]
    return {"schema": "companion-v6h-saved-failure-diagnosis-v1", "events": len(rows),
        "runtime_state": "INCOMPLETE", "verifier_result": result,
        "execution_disabled": response["execution_disabled"], "provider": response["provider"],
        "query_stages": [{k: e.get(k) for k in ("route", "stage", "outcome", "http_status")} for e in events],
        "citation_archive_correlation": correlation,
        "rollback": next(r["installation_evidence"] for r in rows if r["phase"] == "rollback_checks_completed"),
        "first_failed_group": "bundle_market", "exact_failed_predicate_and_live_value": "UNVERIFIED",
        "limitations": [
            "Group rejection is not five independent failures or a unique field/predicate diagnosis.",
            "No live raw response, market payload or DB rows were retained or reconstructed.",
            "Offline producer/consumer mismatch is a candidate explanation, not proof of historical causation.",
            "Citation hash correlation is not completed persisted/content/topical/causal verification.",
            "Configuration rollback is not exact restoration, current health, connectivity or volume-byte proof.",
            "No new query, token read, native call, production change, retry or reset occurred.",
        ],
        "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    print(json.dumps(diagnose(), indent=2, sort_keys=True))
