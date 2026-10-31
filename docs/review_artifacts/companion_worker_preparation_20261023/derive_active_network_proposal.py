"""Offline historical counterfactual, NOT reusable preparation or runtime approval."""
import hashlib
import json
from pathlib import Path

from scripts.research import companion_network_configuration as network

HERE = Path(__file__).resolve().parent
INPUTS = {
    "metadata": ("runtime_packet_v6b_launcher/staged_metadata.derived.json", "ca7101c34446f7b04cc0e1c08dcfcba2026e197d3cecbedb8de13e3cf70118e8"),
    "subjects": ("runtime_packet_v6b_launcher/subjects.draft.json", "0e6cfcc5bdf823659cf6d1f17aab0a961267d9d881e317b62dfa280141402107"),
    "manifest": ("refresh_inputs/reviewed_preparation_manifest.json", "67e29202a3bcd78f050f94b42bc87f91c7a50be90d3485ebd1fc0cfac0b7485e"),
}


def derive():
    values = {}
    for key, (name, expected) in INPUTS.items():
        raw = (HERE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("historical_input_changed")
        values[key] = json.loads(raw)
    bindings = values["manifest"]["network_contract"]["bindings"]
    subjects = values["subjects"]
    applications = values["manifest"]["applications"]
    if len(subjects) != 7 or len(applications) != 4 or len(values["metadata"]["rows"]) != 4:
        raise ValueError("historical_input_changed")
    result = list(subjects[:3])
    for subject, row, app in zip(subjects[3:], values["metadata"]["rows"], applications):
        if subject["name"] != app["name"] or app["network_options"][::2] != ["--alias"] * (len(app["network_options"]) // 2):
            raise ValueError("historical_input_changed")
        result.append(network.final_subject(subject, row, bindings, app["network_options"][1::2]))
    return {"schema": "companion-active-network-counterfactual-v1", "state": "INCOMPLETE",
            "evidence": "MODELLED", "historical_removed_ids_only": True,
            "network_configuration": {"contract": network.CONTRACT, "bindings": bindings},
            "candidate_subjects": result, "input_sha256": {name: sha for name, sha in INPUTS.values()},
            "runtime_authorized": False, "policy_approval_created": False}


if __name__ == "__main__":
    print(json.dumps(derive(), sort_keys=True, indent=2, allow_nan=False))
