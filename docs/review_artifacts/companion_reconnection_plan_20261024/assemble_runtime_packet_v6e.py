"""Offline exact-ID V6e drafts via the existing assembler; no policy authority."""
import hashlib
import json
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
WORKER = "docs/review_artifacts/companion_worker_preparation_20261023"
PRIOR = WORKER + "/runtime_packet_v6d"
HELPER = ROOT / WORKER / "assemble_runtime_packet_v6c.py"
HELPER_SHA = "319153a8c64cb5666d046c0f7031146eaf50deeab14d8d49451fe810734b80fd"
PINS = {
    "manifest": (BASE + "/fresh_inputs/reviewed_preparation_manifest.json", "2075f3b98abc53be9e8336d425dd8d158aca4b1934a1b9da46c2ae9d3cd562d4"),
    "evidence": (BASE + "/actual_preparation/preparation_evidence.json", "49a95a20860e9e62d02a1ecc01884ecbd973e19c6b09d17575e89950f49ebc51"),
    "id_review": (BASE + "/actual_preparation/actual_id_review.json", "9f474d32fecc474721876313f31f1b46fbdf2bf43893e9ff6fd0a5250ce6cab1"),
    "actual_review": (BASE + "/actual_preparation/independent_review.json", "44a0dd8a2207bb85ddb5f9cec5af198ffc61150718d4c83de9e23e4970ee8e93"),
    "metadata": (BASE + "/actual_preparation/postcheck.json", "129ffe87c50b845f4f61374c62c0c23bbb9bdd64b2dbbbd870849f499904dbc1"),
    "postcheck": (BASE + "/actual_preparation/postcheck.json", "129ffe87c50b845f4f61374c62c0c23bbb9bdd64b2dbbbd870849f499904dbc1"),
    "correction": (WORKER + "/nonrecipient_configuration_review_20261023.json", "ced40c1af138f586af0878182ab462ff6bbc5e7ab17870815f8783ad2a1bbb69"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "c15d6ea7b98c29c965b95c7a075e82db5a4e8de4acf810e04261afebe197adb6"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "63a8571166993cfbccb51ae474da9fd43089cdea8f61861ff52fb0bfdc2c74d9"),
    "topical": ("docs/review_artifacts/companion_evidence_packet_v2_20261024/topical_candidates.json", "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"),
}
LINEAGE = {
    BASE + "/fresh_inputs/provenance.json": "9407ddedf5b573286af1de56c7c867fe5a09d3e8bfa31bf6f4e14fc0a7f31fed",
    "docs/review_artifacts/companion_witness_proposal_v2_20261024/independent_review.json": "c24620ca184ccd01d8afc14e6fdc2ecc96073181c09bc0dc880920e9b8598525",
    "docs/review_artifacts/companion_witness_proposal_v2_20261024/proposal.json": "5095d72eef7a2a9ac1d158aa8aa81fa78944b7c5788db61c735424b75591bf20",
    "docs/review_artifacts/companion_context_guard_20261024/independent_review_corrected.json": "9a8acc659bda7e7f53059b3297c714b63ace0b0531d7cafc5265bcb60a8c5819",
    "docs/review_artifacts/companion_evidence_packet_v2_20261024/independent_review.json": "309d6079cc0aee852cba9678ccc0ea77d782d31503edabf53024f3a99ca7b6ef",
}
CLIENTS = {
    "dashboard/services/view_data.py": "c6a672aa818ac18b5bb9d37c9d5c9f465a820cceb868d92655676b60450baa51",
    "dashboard/services/views/_shared.py": "92d24a74c55963f5dafdaf47763e427c55c287ca2c4513935d7d2d5679e70202",
    "dashboard/services/views/_shared_http.py": "c4e5aaa1430ea8768062fb6ed60a0782a3938074defdc86ae77d3e0225ec95ae",
    "dashboard/services/views/_shared_signals.py": "d003edac94edbb7d7886901784674e23ed9accae2d42bd69c0a7f6fbc0c9e381",
    "dashboard/services/views/market_view.py": "4d24d894ad791db44dc3f37e84845a40355207930bba25d41f4ad36753d47d75",
    "dashboard/services/views/_explain_diagnostics.py": "356a235a22f412460e902347e1d8eb489a9d4f0a528c7bd9ce127cb11e5d7556",
    "scripts/research/companion_evidence_checks.py": "a35dc46439f25ff8ebc6f4068c28bd1bdd268d7da623a11c3a0b0f02edf614e8",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def raw_checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("v6e_packet_input_changed:" + str(path))
    return raw


def checked(path, expected):
    raw = raw_checked(path, expected)
    if path == PINS["actual_review"][0]:
        value = json.loads(raw)
        consumers = json.loads(raw_checked(BASE + "/fresh_inputs/provenance.json", LINEAGE[BASE + "/fresh_inputs/provenance.json"]))["consumer_sha256"]
        assert len(consumers) == 13
        assert all(value["source_and_artifact_sha256"].get(p) == h for p, h in consumers.items())
        value["consumer_sha256"] = consumers
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if path == PINS["postcheck"][0]:
        value = json.loads(raw)
        by_id = {r["id"]: r for r in value["before"]}
        value["rows"] = value["before"][7:]
        witnesses = []
        for row in value["sources"]:
            image = by_id[row["container_id"]]["image"]
            assert row["image_id_from_same_id_metadata"] == image
            witnesses.append({"name": row["target"], "path": row["path"],
                              "container_id": row["container_id"], "image": image,
                              "sha256": row["sha256"], "matches_frozen_source": row["local_and_manifest_match"]})
        value["source_files"] = witnesses
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return raw


def derive():
    lineage = {p: json.loads(raw_checked(p, h)) for p, h in LINEAGE.items()}
    for path, value in lineage.items():
        if path.endswith("independent_review.json") or path.endswith("independent_review_corrected.json"):
            assert value["decision"] == "ACCEPTED_WITH_RISK" and not value["findings"]
    proposal = lineage["docs/review_artifacts/companion_witness_proposal_v2_20261024/proposal.json"]
    assert json.loads(raw_checked(*PINS["topical"])) == proposal["proposed_records"]
    for path, sha in CLIENTS.items():
        raw_checked(path, sha)
    raw = raw_checked(str(HELPER.relative_to(ROOT)), HELPER_SHA)
    worker = types.ModuleType("reviewed_v6e_packet_recipe")
    worker.__file__ = str(HELPER)
    exec(compile(raw, str(HELPER), "exec"), worker.__dict__)
    worker.PINS, worker.PRIOR, worker.checked = dict(PINS), PRIOR, checked
    artifacts = worker.derive()
    proof = artifacts["provenance.json"]
    assert proof["attempt"] == "workerprep20261024v6e" and proof["total_source_pins"] == 132
    proof["preparation_consumer_sha256"] = dict(proof["consumer_sha256"])
    proof["consumer_sha256"].update(CLIENTS)
    proof["input_sha256"].update(LINEAGE)
    proof["input_sha256"].update({str(HELPER.relative_to(ROOT)): HELPER_SHA,
        str(Path(__file__).relative_to(ROOT)): digest(Path(__file__).read_bytes())})
    proof.update(schema="companion-v6e-runtime-packet-proposal-v1",
        source_provenance="43 direct V6e application-file witnesses; 89 exact-image/storage source pins inherited, not recaptured",
        schema_adapter="Raw postcheck -> rows/source_files; actual review -> same13consumer table; original files unchanged and image association joined from same-ID before/after metadata",
        added_client_bindings=CLIENTS,
        evidence_change="Exact independently reviewed archived witnesses7,5,47,18; no current causation, truth or runtime activation claimed",
        guard_change="Previously accepted exact headline-context correction; unsupported/wrong-asset and source/body/citation gates retained",
        adapted_input_sha256={p: digest(checked(p, h)) for key, (p, h) in PINS.items() if key in {"actual_review", "postcheck"}},
        historical_runtime_cause="UNVERIFIED", runtime_state="INCOMPLETE")
    return artifacts


if __name__ == "__main__":
    output = HERE / "runtime_packet_v6e"
    artifacts = derive()
    output.mkdir(exist_ok=False)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
