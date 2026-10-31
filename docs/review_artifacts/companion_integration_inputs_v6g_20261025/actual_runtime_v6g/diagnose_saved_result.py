"""Saved public evidence only; no raw-response reconstruction or remote calls."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def diagnose():
    receipt = HERE / "receipt.jsonl"
    original = ROOT / ".cbp_state/runtime/companion_cutovers/workerprep20261025v6g/receipt.jsonl"
    assert receipt.read_bytes() == original.read_bytes()
    rows = [json.loads(line) for line in receipt.read_text().splitlines()]
    query = [r for r in rows if r["phase"] == "query_diagnostics"]
    checks = [r for r in rows if r["phase"] == "evidence_verification_checks"]
    assert len(query) == len(checks) == 1
    events = query[0]["installation_evidence"]["events"]
    result = checks[0]["installation_evidence"]
    assert result["outcome"] == "complete" and result["shape_valid"] is True
    assert len(result["checks"]) == 5 and all(value is False for value in result["checks"].values())
    assert any(e["route"] == "companion" and e["stage"] == "normalization" and e["outcome"] == "accepted" for e in events)
    assert not any(e["outcome"] in {"foreign_asset", "static_fallback"} for e in events)
    archive = ROOT / "research/companion_article_body_v1_20261011_gd1abqx9/original_snapshot.json"
    originals = json.loads(archive.read_text())
    indexed = {hashlib.sha256(str(r["id"]).encode()).hexdigest(): r for r in originals}
    response = next(e["response"] for e in events if e["route"] == "companion" and e["stage"] == "transport")
    correlation = []
    for citation in response["citation_hashes"]:
        match = indexed[citation["document_id_sha256"]]
        correlation.append({"document_id": match["id"],
            "url_hash_matches": hashlib.sha256(match["url"].encode()).hexdigest() == citation["url_sha256"]})
    assert [r["document_id"] for r in correlation] == [5, 47, 18, 5, 26]
    assert all(r["url_hash_matches"] for r in correlation)
    paths = [receipt, original, archive, Path(__file__),
             ROOT / "scripts/research/companion_evidence_checks.py",
             ROOT / "scripts/research/companion_runtime_adapter.py",
             ROOT / "scripts/research/companion_installer.py"]
    return {"schema": "companion-v6g-saved-failure-diagnosis-v1", "events": len(rows),
            "runtime_state": "INCOMPLETE",
            "query_stages": [{k: e.get(k) for k in ("route", "stage", "outcome", "http_status")} for e in events],
            "execution_disabled": response["execution_disabled"], "provider": response["provider"],
            "citation_archive_correlation": correlation, "verifier_result": result,
            "rollback": next(r["installation_evidence"] for r in rows if r["phase"] == "rollback_checks_completed"),
            "first_failure_cause": "UNVERIFIED",
            "limitations": [
                "All-false is not five independent failures; verifier catches and deadlines collapse to identical output.",
                "Response prose/types, live DB rows and first failed predicate were not retained; no reconstruction is claimed.",
                "Citation hash correlation is not persisted identity, content, topical or causal verification.",
                "Configuration recovery is not exact restoration, current health, connectivity or volume-byte proof.",
                "No new query, token read, native call, source change, retry or reset is performed.",
            ],
            "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    print(json.dumps(diagnose(), indent=2, sort_keys=True))
