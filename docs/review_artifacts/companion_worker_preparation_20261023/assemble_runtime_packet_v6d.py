"""Offline exact-ID proposal, reusing the reviewed V2 assembler without authority."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import types

from scripts.research import companion_installer as install

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
PRIOR = BASE + "/runtime_packet_v6c"
HELPER = HERE / "assemble_runtime_packet_v6c.py"
HELPER_SHA = "319153a8c64cb5666d046c0f7031146eaf50deeab14d8d49451fe810734b80fd"
PINS = {
    "manifest": (BASE + "/fresh_preparation_v6d/reviewed_preparation_manifest.json", "629662e509e099be8601be1c9499d7139f03803f4f998f5b31fce15b2551b4a0"),
    "evidence": (BASE + "/actual_d/preparation_evidence.json", "9441411ba4ad31194b4f53aa99e1705a46365a93a0ebd5527e1e23957f52d65e"),
    "id_review": (BASE + "/actual_d/actual_id_review.json", "e185f51ab00c1a719ebe541d22564289931335a2b46d729667b2d8271bfc32a2"),
    "actual_review": (BASE + "/actual_d/independent_review.json", "fdd9a8e09c09f5938fcbd764caa606b39e0b07bf1ca4fbf33ba875410032ea3b"),
    "metadata": (BASE + "/actual_d/staged_metadata.json", "b571301e009d0005a7498076db63ccd91b72ef7a7bc9cc4bff9446f6f73722ec"),
    "postcheck": (BASE + "/actual_d/postcheck.json", "6c85eaf31ec66f89ba34114c1eb90c990436bf95929651b0d971074e5c06dec6"),
    "correction": (BASE + "/nonrecipient_configuration_review_20261023.json", "ced40c1af138f586af0878182ab462ff6bbc5e7ab17870815f8783ad2a1bbb69"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "f916471d3618eb5a44bc8bf00ac6421aa3e941febab431b8a1c49fd65daddb74"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "76f3e5f8f8a788f2b683bc01be58c42a0489e413476120abd062aa28c6927935"),
    "topical": (PRIOR + "/topical_approvals.json", "f4de03c65058769eb434e5931065deaeb5795087983a92a3b2f54dacd8feff45"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("v6d_packet_input_changed")
    if path == PINS["postcheck"][0]:
        value = json.loads(raw)
        rows = {r["id"]: r for r in value["before"]}
        # Schema adapter only. Image binding comes from the matching metadata
        # observation, not a field that the source-copy witness itself recorded.
        value["source_files"] = [{"name": w["target"], "path": w["path"],
            "container_id": w["container_id"], "image": rows[w["container_id"]]["image"],
            "sha256": w["sha256"], "matches_frozen_source": w["local_and_manifest_match"]}
            for w in value["sources"]]
        return install.canonical(value)
    return raw


def derive():
    raw = HELPER.read_bytes()
    if digest(raw) != HELPER_SHA:
        raise ValueError("v6d_packet_helper_changed")
    worker = types.ModuleType("reviewed_v6d_packet_recipe")
    worker.__file__ = str(HELPER)
    exec(compile(raw, str(HELPER), "exec"), worker.__dict__)
    worker.PINS, worker.PRIOR, worker.checked = dict(PINS), PRIOR, checked
    artifacts = worker.derive()
    proof = artifacts["provenance.json"]
    if proof["attempt"] != "workerprep20261023v6d":
        raise ValueError("v6d_packet_attempt_changed")
    proof.update(schema="companion-v6d-runtime-packet-proposal-v1",
        source_provenance="43 actual-v6d application witnesses; remaining 89 same-image/storage pins including four historical launchers are inherited, not recaptured",
        witness_schema_adapter="sources->source_files; target->name; local_and_manifest_match->matches_frozen_source; image joined from same-ID before metadata, not a direct source-copy image witness",
        historical_v6c_cause="UNVERIFIED",
        runtime_state="INCOMPLETE")
    proof["input_sha256"][str(HELPER.relative_to(ROOT))] = HELPER_SHA
    return artifacts


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6d"
    output.mkdir(mode=0o700)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
    print(json.dumps({"state": "READY_FOR_INDEPENDENT_REVIEW", "artifacts": len(artifacts),
                      "source_pins": 132, "native_operations": False, "policy_approval_created": False}))
