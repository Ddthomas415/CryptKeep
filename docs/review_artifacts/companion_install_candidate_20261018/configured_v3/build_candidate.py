"""Offline derivation only: no Docker, credentials, acceptance or installation."""
import copy
import hashlib
import json
from pathlib import Path

from scripts.research import companion_network_configuration as network
from scripts.research import companion_runtime_adapter as adapter
from scripts.research.prepare_companion_stopped_recipe import compile_recipe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ATTEMPT = "1693bb273e564a5d9dd096a9fb8db778"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def derive():
    capture_raw = (HERE / "capture/observation.json").read_bytes()
    capture = json.loads(capture_raw)
    source_raw = (ROOT / "docs/review_artifacts/companion_import_inventory_20261018/source_bundle/manifest.json").read_bytes()
    assert sha(source_raw) == "973da853c3c2aabdce982c677b5b6ab9c6d7cbab5061ec27ab28197b07b3c875"
    old_raw = (HERE.parent / "reviewed_stopped_plan.json").read_bytes()
    assert sha(old_raw) == "a513c458419f01517fec5e771e5be967f85b43391de663dc55c0bcdfb8ac4af4"
    old = json.loads(old_raw)
    code_raw = (HERE.parent / "network_contract_review.json").read_bytes()
    assert sha(code_raw) == "641ff6792fdef7325aae305ca86ad56792310993fa2f39d6cc66a4e4f0be452d"
    for pin in json.loads(code_raw)["bindings"]["reviewed_files"]:
        assert sha((ROOT / pin["path"]).read_bytes()) == pin["sha256"]
    recipe = compile_recipe(capture, source_raw)
    assert adapter._canonical(recipe) == adapter._canonical(json.loads((HERE / "recipe.json").read_bytes()))
    observed = json.loads((HERE / "network_bindings.json").read_bytes())
    assert observed["container_capture_sha256"] == sha(capture_raw)
    bindings = observed["bindings"]
    network.validate_bindings(bindings)
    assert len(observed["observed_rows"]) == len(bindings)
    assert {r["name"]: r["id"] for r in observed["observed_rows"]} == bindings
    assert observed["connectivity_verified"] is False
    by_name = {r["name"].removeprefix("/"): r for r in capture["observations"]}
    baseline = copy.deepcopy(recipe["baseline"])
    for record in baseline:
        row = by_name[record["name"]]
        assert record["metadata"] == adapter.preservation_digest(row)
        configured, ids, evidence = network.project(row, bindings)
        record.update(configured_metadata=configured, configured_networks=list(ids),
                      network_evidence=[list(e) for e in evidence])
    overrides = {k: v for k, v in adapter.ENV_EXPECTED.items() if k not in {"POSTGRES_USER", "POSTGRES_DB"}}
    apps = []
    for app in recipe["applications"]:
        row = app["observed_recreation_metadata"]
        networks = list(row["networks"].values())
        assert len(networks) == 1 and networks[0]["IPAMConfig"] in (None, {})
        aliases = networks[0]["Aliases"]
        assert type(aliases) is list and aliases and len(set(aliases)) == len(aliases)
        options = [part for alias in aliases for part in ("--alias", alias)]
        if "network_options" in app:
            assert options == app["network_options"]
        projected = copy.deepcopy(row)
        flags = [dict(f) for f in row["flags"] if f is not None]
        present = set()
        for flag in flags:
            if flag["key"] in overrides:
                flag["ok"] = True
            present.add(flag["key"])
        flags.extend({"key": key, "ok": True} for key in overrides if key not in present)
        projected["flags"] = [*flags, None]
        assert adapter.preservation_digest(projected) == app["replacement_metadata"]
        apps.append({"name": app["name"], "create_options": app["create_options"],
                     "command": app["command"], "network_options": options,
                     "replacement_configured_metadata": network.project(projected, bindings)[0],
                     "sources": [{k: s[k] for k in ("local", "destination", "sha256")} for s in app["sources"]]})
    return {"schema": "companion-configured-install-v3", "decision": "READY_FOR_INDEPENDENT_REVIEW",
            "reviewer": "pending_independent_review", "attempt": ATTEMPT,
            "cli_sha256": capture["cli_sha256"], "policies": old["policies"],
            "network_contract": {"schema": network.CONTRACT, "bindings": bindings, "connectivity_verified": False},
            "baseline": baseline, "applications": apps}


def main():
    candidate = derive()
    raw = (json.dumps(candidate, indent=2, sort_keys=True) + "\n").encode()
    with (HERE / "plan_candidate_v3.json").open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"state": candidate["decision"], "candidate_sha256": sha(raw),
                      "installation_authorized": False, "startup_authorized": False}))


if __name__ == "__main__":
    main()
