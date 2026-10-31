"""Fresh offline inputs through the existing recipe; no preparation or authority."""
import hashlib
import json
import os
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKER = Path("docs/review_artifacts/companion_worker_preparation_20261023")
INVENTORY = Path("docs/review_artifacts/companion_runtime_inventory_20261024")
ATTEMPT = "workerprep20261024v6e"
HELPER = WORKER / "derive_fresh_preparation.py"
HELPER_SHA = "bb5854132df93d2e055a98358e581fc4a8ab7c16db2f98e7048e51a29d63544e"
PINS = {
    "manifest": (WORKER / "fresh_preparation_v6d/reviewed_preparation_manifest.json", "629662e509e099be8601be1c9499d7139f03803f4f998f5b31fce15b2551b4a0"),
    "observation": (INVENTORY / "observation.json", "0a71483b1ee7e54874975647d0105b3f03bc44a9c2274e8a5350ed34bc950793"),
    "correction": (WORKER / "nonrecipient_configuration_review_20261023.json", "ced40c1af138f586af0878182ab462ff6bbc5e7ab17870815f8783ad2a1bbb69"),
    "consumers": (WORKER / "fresh_preparation_v6d/provenance.json", "450528ec555d61fca4d3bc6defb94bfaf08ef37b170f18db96f7f2fb94691857"),
    "models": (WORKER / "runtime_packet_v6d/staged_metadata.derived.json", "b571301e009d0005a7498076db63ccd91b72ef7a7bc9cc4bff9446f6f73722ec"),
}
PLAN_REVIEW = HERE / "independent_review.json"
PLAN_REVIEW_SHA = "f0f3d0ff17b359bc6fe1f10d27876787ed586dc6f66fed84b58efcc707733ca4"


def read_checked(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("fresh_input_changed")
    return raw


def checked(path, expected):
    raw = read_checked(path, expected)
    if path == ROOT / PINS["observation"][0]:
        value = json.loads(raw)
        pair = value["observations"]
        if (len(pair) != 2 or pair[0] != pair[1]
                or value["selected_observations_equal"] is not True
                or value["metadata_complete_for_selected_fields"] is not True):
            raise ValueError("fresh_inventory_pair_invalid")
        # Pure shape adapter only; preserve the actual source capture file/hash.
        value.update(observations=pair[0], final_observations=pair[1],
                     final_observations_match=True, observed_utc=value["observed_end_utc"])
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return raw


def recipe():
    raw = read_checked(ROOT / HELPER, HELPER_SHA)
    module = types.ModuleType("reviewed_fresh_inputs_v6e")
    module.__file__ = str(ROOT / HELPER)
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    module.ROOT, module.HERE = ROOT, ROOT
    module.ATTEMPT, module.PINS, module.checked = ATTEMPT, dict(PINS), checked
    return module


def derive():
    review = json.loads(read_checked(PLAN_REVIEW, PLAN_REVIEW_SHA))
    if review["decision"] != "ACCEPTED_WITH_RISK" or review["findings"]:
        raise ValueError("fresh_plan_not_reviewed")
    for path, digest in review["direct_sha256"].items():
        read_checked(ROOT / path, digest)
    table = review["bound_input_table"]
    proof = json.loads(read_checked(ROOT / table["path"], table["sha256"]))
    for path, digest in proof[table["json_field"]].items():
        read_checked(ROOT / path, digest)
    for group in ("companion_preparations", "companion_cutovers"):
        if not os.path.lexists(ROOT / ".cbp_state/runtime" / group / "workerprep20261023v6d"):
            raise ValueError("prior_consumption_evidence_missing")
    candidate, provenance = recipe().derive()
    provenance["input_sha256"].update({str(HELPER): HELPER_SHA,
        str(PLAN_REVIEW.relative_to(ROOT)): PLAN_REVIEW_SHA,
        str(Path(__file__).relative_to(ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    provenance.update(
        capture_schema_adapter="Hash-verified paired observations[0]/[1] projected to old recipe row/final-row fields; observed_end_utc -> observed_utc; original file unchanged",
        adapted_capture_sha256=hashlib.sha256(checked(ROOT / PINS["observation"][0], PINS["observation"][1])).hexdigest(),
        recipe_reuse="Exact accepted pure recipe; five fixed inputs/new unused label only, no lifecycle or policy changes",
        prior_prepared_ids="Historical configuration models only; not future IDs or adopted replacements",
        evidence_integration="Reviewed evidence portion remains non-effective; actual-ID runtime packet remains separate",
        runtime_status="INCOMPLETE", authorization="No build, create, private-config copy, reserve, startup, cutover, query or reset")
    return candidate, provenance


if __name__ == "__main__":
    candidate, proof = derive()
    output = HERE / "fresh_inputs"
    output.mkdir(exist_ok=False)
    for name, value in (("candidate_manifest.json", candidate), ("provenance.json", proof)):
        with (output / name).open("xb") as stream:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())
