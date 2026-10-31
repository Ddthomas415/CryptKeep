"""Offline V6f packet proposal; no fabricated capture, policy approval or action."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from scripts.research import companion_existing_controller as core
from scripts.research import companion_installer as install
from scripts.research import companion_network_configuration as network
from scripts.research import companion_prepare as preparation
from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_staged_update as staged

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = str(HERE.relative_to(ROOT))
PRIOR = "docs/review_artifacts/companion_reconnection_plan_20261024/runtime_packet_v6e"
REPAIR = "docs/review_artifacts/companion_archive_scope_repair_20261025"
PINS = {
    "manifest": (BASE + "/reviewed_preparation_manifest.json", "a7854b1660ae2c321f8edb62d3ac2b7ab60350deb62df91bdde774e8c2ea1588"),
    "evidence": (BASE + "/actual_preparation/preparation_evidence.json", "2463b6fe35b8c10ac9df63f9099c0fe986725bab5179e7a7bdbdc23c9ed6fb95"),
    "id_review": (BASE + "/actual_preparation/actual_id_review.json", "281cae425cad8dfae95709c6ab22004789cfec2c0cd2665438bbada8fd210645"),
    "actual_review": (BASE + "/actual_preparation/independent_review.json", "b83fc5ec8a996927e28221f014a0d8e10436697a39e7450dfeb44480464ed6a9"),
    "postcheck": (BASE + "/actual_preparation/postcheck.json", "398fab026e615a94d797ae554677421d7c54f3f7717525f4a26644a3a7a30f07"),
    "provenance": (BASE + "/provenance.json", "b8c685aac89efc0661a2635e97855b997e8fc77cbd9ab2b029b667f4da3377a7"),
    "prior_manifest": ("docs/review_artifacts/companion_reconnection_plan_20261024/fresh_inputs/reviewed_preparation_manifest.json", "2075f3b98abc53be9e8336d425dd8d158aca4b1934a1b9da46c2ae9d3cd562d4"),
    "prior_runtime": (PRIOR + "/accepted_policy_records/runtime_review.json", "9590454b0f9d9fd3350ff58ffae7eafe2b5cacc0a480f0e4e100289bef4c43b0"),
    "prior_scope": (PRIOR + "/accepted_policy_records/scope_review.json", "7da764a58196cd66cf2466d393729d3d3267b620f3829fcd974ca3f977e27b5d"),
    "repair": (REPAIR + "/report.json", "7ff14e8f8f46ee30aa17d526fe670c01bd952dd54155fdc517447d05207dfd6d"),
    "repair_review": (REPAIR + "/independent_review.json", "4747ffdc6f86e549bdc703dd5ee017456ae221ad456b7b97d84828d11dbe5f35"),
    "topical": ("docs/review_artifacts/companion_evidence_packet_v2_20261024/topical_candidates.json", "dc3f5678277fb14afb523d54acfc3ef9303627fb810ad075228702054d18505a"),
    "builder": ("scripts/research/companion_install_docker.py", "fbe5c0abe9be35cd0765d98b6d31b29f0e075cf7ece2e4d541283bce2755b28c"),
    "staged_flow": ("scripts/research/companion_staged_update.py", "f6a6878d8de760caaee757ed5ef570872c67efb74106fe2d6b0f8090ab697d18"),
}
MEMORY_CHANGES = {"/app/memory_retrieval/main.py", "/app/memory_retrieval/article_view.py"}
INSTALLER = "scripts/research/companion_installer.py"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = (ROOT / path).read_bytes()
    if digest(raw) != expected:
        raise ValueError("v6f_packet_input_changed:" + str(path))
    return raw


def require(condition, label):
    if not condition:
        raise ValueError("v6f_packet_" + label)


def snapshot(row, bindings):
    configured, networks, evidence = network.project(row, bindings)
    return install.Snapshot(row["name"].removeprefix("/"), row["id"], row["image"], row["state"],
        row["started"], row["restarts"], row["restart_policy"], adapter.preservation_digest(row),
        adapter.preservation_digest({**row, "networks": {}}),
        tuple(sorted(n["NetworkID"] for n in row["networks"].values())), row.get("attempt") or "",
        configured, networks, evidence)


def derive():
    raw = {key: checked(*pin) for key, pin in PINS.items()}
    data = {key: json.loads(value) for key, value in raw.items() if key not in {"builder", "staged_flow"}}
    plan = preparation._manifest(ROOT / PINS["manifest"][0], PINS["manifest"][1])
    prepared = staged.ReviewedPreparation.load(raw["evidence"], raw["id_review"], PINS["id_review"][1], plan)
    prior, scope, report = data["prior_runtime"], data["prior_scope"], data["repair"]
    for name in ("actual_review", "prior_runtime", "prior_scope", "repair_review"):
        require(data[name]["decision"] == "ACCEPTED_WITH_RISK" and not data[name].get("blocking_findings"), "review_unaccepted")
    require(data["repair_review"]["integrity"]["artifacts"][PINS["repair"][0]] == PINS["repair"][1], "repair_detached")
    for path, sha in report["source_and_input_sha256"].items():
        checked(path, sha)
    for group, expected in (("companion_preparations", True), ("companion_cutovers", False)):
        require(os.path.lexists(ROOT / ".cbp_state/runtime" / group / plan.attempt) is expected, "attempt_state")
    consumers = dict(scope["consumer_sha256"])
    consumers.update(data["provenance"]["consumer_sha256"])
    require(set(consumers) == set(scope["consumer_sha256"]) and len(consumers) == 20
        and len(data["provenance"]["consumer_sha256"]) == 13, "consumer_count")
    require({p for p in consumers if consumers[p] != scope["consumer_sha256"][p]} == {INSTALLER}, "consumer_delta")
    require(consumers[INSTALLER] == report["source_and_input_sha256"][INSTALLER]
        and scope["consumer_sha256"][INSTALLER] == report["pre_change_source_sha256"][INSTALLER], "consumer_lineage")
    for path, sha in consumers.items():
        checked(path, sha)
    require(tuple(s["name"] for s in prior["subjects"]) == core.TARGETS, "prior_subjects")
    for subject in prior["subjects"]:
        child = json.loads(checked(PRIOR + "/accepted_policy_records/" + subject["name"] + ".json",
                                   prior["dependency_reviews"][subject["image_id"]]))
        require(child["subjects"] == [subject], "prior_child")
    observed = data["postcheck"]
    require(len(observed["before"]) == 11 and observed["before"] == observed["after"], "metadata_pair")
    bindings = dict(plan.network_bindings)
    require(tuple(snapshot(r, bindings) for r in observed["before"][:7]) == plan.baseline, "originals")
    rows = observed["before"][7:]
    require(tuple(snapshot(r, bindings) for r in rows) == prepared.replacements, "stages")
    approved = data["actual_review"]["accepted_actual_stages"]
    require([(r.id, r.image) for r in prepared.replacements] == [(r["id"], r["image"]) for r in approved], "actual_identity_review")
    old_manifest = data["prior_manifest"]
    require(plan.attempt == "workerprep20261025v6f" and sum(len(a["sources"]) for a in plan.applications) == 43, "profile")
    subjects, deltas = [], []
    for before, previous in zip(plan.baseline[:3], prior["subjects"][:3]):
        require((before.id, before.image, before.metadata) == (previous["container_id"], previous["image_id"], previous["preservation_sha256"]), "storage")
        subjects.append(deepcopy(previous))
    for index, (app, actual, row, previous) in enumerate(zip(plan.applications, prepared.replacements, rows, prior["subjects"][3:])):
        old_app = old_manifest["applications"][index]
        require({k:v for k,v in app.items() if k != "sources"} == {k:v for k,v in old_app.items() if k != "sources"}, "command_options")
        require(row["command"] == app["command"] and previous["name"] == app["name"], "stage_command")
        require(app["network_options"][::2] == ["--alias"] * (len(app["network_options"]) // 2), "aliases")
        before_parent = old_manifest["baseline"][index + 3]
        require((before_parent["id"], before_parent["image"], before_parent["foundation"])
            == (plan.baseline[index + 3].id, plan.baseline[index + 3].image, plan.baseline[index + 3].foundation), "common_parent")
        sources = dict(previous["sources"])
        expected = {s["destination"]:s["sha256"] for s in app["sources"]}
        require(set(expected) == {p for p in sources if p.startswith("/app/")}, "source_paths")
        changed = {p for p in expected if expected[p] != sources[p]}
        require(changed == (MEMORY_CHANGES if app["name"] == "phase1-memory" else set()), "source_delta")
        require((actual.image != previous["image_id"]) == (app["name"] == "phase1-memory"), "image_delta")
        for source in app["sources"]:
            checked(source["local"], source["sha256"])
            if source["destination"] in changed:
                require(report["pre_change_source_sha256"][source["local"]] == sources[source["destination"]]
                    and report["source_and_input_sha256"][source["local"]] == source["sha256"], "source_repair_lineage")
        sources.update(expected)
        subject = network.final_subject({**previous, "container_id":actual.id, "image_id":actual.image, "sources":sources}, row, bindings, app["network_options"][1::2])
        require(subject["preservation_sha256"] == app["replacement_configured_metadata"], "final_model")
        subjects.append(subject)
        deltas.append({"name":app["name"], "prior_container_id":previous["container_id"], "container_id":actual.id,
            "prior_image_id":previous["image_id"], "image_id":actual.image, "changed_source_paths":sorted(changed),
            "source_provenance":"controller verified at creation; no independently recaptured file streams",
            "inherited_library_pins":len(sources)-len(expected),
            "library_basis":"common original parent/source-only COPY overlay attestation" if changed else "unchanged exact image",
            "common_parent_image":before_parent["image"], "final_configuration_evidence":"MODELLED"})
    topical = data["topical"]
    require(digest(install.canonical(topical)) == prior["topical_approvals_sha256"], "topical_changed")
    targets = tuple(adapter.TargetPin(s["name"],s["container_id"],s["image_id"],s["preservation_sha256"],tuple(sorted(s["sources"].items()))) for s in subjects)
    validator = adapter.PinnedRuntimeAdapter(None,adapter.ReviewedPins(targets,"0"*64,(),tuple(topical),b"",()))
    try:
        require(validator._source_coverage(validator._pins()) and validator._topical_contract(), "structure")
    finally:
        validator.close()
    artifacts, dependencies = {}, {}
    for subject in subjects:
        draft = {"schema":"companion-installed-policy-review-v1", "decision":"INCOMPLETE", "reviewer":"",
            "image_id":subject["image_id"], "subjects":[subject], "policies":dict.fromkeys(scope["policy_meanings"],"UNVERIFIED")}
        artifacts[subject["name"]+".draft.json"] = draft
        dependencies[subject["image_id"]] = digest(install.canonical(draft))
    artifacts["runtime_review.draft.json"] = {"schema":"companion-runtime-pins-v2", "decision":"INCOMPLETE", "reviewer":"",
        "subjects":subjects, "dependency_reviews":dependencies, "topical_approvals_sha256":digest(install.canonical(topical)),
        "network_configuration":{"contract":network.CONTRACT,"bindings":bindings}}
    artifacts.update({"subjects.draft.json":subjects,"staged_metadata.derived.json":{"rows":rows},"topical_approvals.json":topical,
        "provenance.json":{"schema":"companion-v6f-runtime-packet-proposal-v1","state":"READY_FOR_INDEPENDENT_REVIEW",
            "attempt":plan.attempt,"input_sha256":{**{p:h for p,h in PINS.values()},str(Path(__file__).relative_to(ROOT)):digest(Path(__file__).read_bytes())},
            "consumer_sha256":consumers,"prior_dependency_reviews":prior["dependency_reviews"],"subject_delta":deltas,
            "total_source_pins":sum(len(s["sources"]) for s in subjects),"application_entries_controller_attested":43,
            "direct_file_streams_recaptured":0,"inherited_exact_image_or_storage_pins":52,"inherited_common_parent_memory_pins":37,
            "preserved_policy_meanings":scope["policy_meanings"],"preserved_limits":scope["preserved_limits"],
            "provenance_limit":"Build/controller and source-only image lineage attestations, not independent installed bytes or blanket SDK compatibility; fresh source gates mandatory.",
            "final_configuration_evidence":"MODELLED","runtime_state":"INCOMPLETE","native_operations":False,
            "credential_access":False,"policy_approval_created":False,"cutover_authorized":False}})
    require(artifacts["provenance.json"]["total_source_pins"] == 132, "pin_count")
    return artifacts


if __name__ == "__main__":
    artifacts = derive()
    output = HERE / "runtime_packet_v6f"
    output.mkdir(exist_ok=False)
    for name, value in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(install.canonical(value))
