"""Offline tests for the guarded ENTR-CB-1 wrapper (synthetic files; the cohort computation is stubbed)."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.research import pinned_run_inputs as guard
from scripts.research import run_coinbase_tradable_entrants as runner
from scripts.research import run_coinbase_tradable_entrants_pinned as wrapper
from scripts.research import run_low_value_top100_v2 as v2
from scripts.research import test_low_value_top100 as engine

LISTINGS = "research/stepB/listings.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def world(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    modules = {wrapper.REQUIRED_SOURCES[0]: runner, wrapper.REQUIRED_SOURCES[1]: wrapper,
               wrapper.REQUIRED_SOURCES[2]: v2, wrapper.REQUIRED_SOURCES[3]: engine,
               wrapper.REQUIRED_SOURCES[4]: guard}
    for rel, module in modules.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(module.__file__, root / rel)
        monkeypatch.setattr(module, "__file__", str(root / rel))
    files = {wrapper.PREREG: b"frozen prereg text\n", wrapper.ARCHIVE: b"archive bytes",
             wrapper.MANIFEST: b"manifest\n",
             LISTINGS: json.dumps({"schema": runner.LISTING_SCHEMA,
                                   "assets": {"7": {"status": "never_listed"}}}).encode()}
    for rel, data in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    monkeypatch.setattr(runner, "FROZEN_PREREG_SHA256", sha(root / wrapper.PREREG))
    monkeypatch.setattr(wrapper, "dependency_checks", lambda r, rel, s: ((r / rel, s),))
    monkeypatch.setattr(v2, "ARTIFACTS", tmp_path / "artifacts")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "instrument_correction_v2.json").write_text('{"exclusions": []}')
    calls = {}
    def fake_load(archive, manifest):
        calls["load"] = (archive, manifest)
        return ["d"], ["snap"], {"m": "h"}
    monkeypatch.setattr(engine, "load", fake_load)
    monkeypatch.setattr(v2, "corrected_view", lambda snaps, mapping: ("view", snaps))

    def fake_run(dates, view, listings):
        calls["run"] = (dates, view, listings)
        return {"decision": {"verdict": "STOP"}, "cb_summary": {}}
    monkeypatch.setattr(runner, "run_filtered", fake_run)

    def plan(**changes):
        doc = {"schema": guard.SCHEMA, "root": str(root.resolve()),
               "preregistration": {"path": wrapper.PREREG, "sha256": sha(root / wrapper.PREREG)},
               "inputs": {rel: sha(root / rel) for rel in (wrapper.ARCHIVE, wrapper.MANIFEST, LISTINGS)},
               "sources": {rel: sha(root / rel) for rel in wrapper.REQUIRED_SOURCES}}
        doc.update(changes)
        path = tmp_path / f"plan_{len(list(tmp_path.glob('plan_*')))}.json"
        path.write_text(json.dumps(doc))
        return path, sha(path), doc
    return {"root": root, "tmp": tmp_path, "plan": plan, "calls": calls}


def run(world, plan_path, plan_sha, name="out"):
    out = world["tmp"] / name
    return out, wrapper.main(["--plan", str(plan_path), "--plan-sha256", plan_sha, "--output-dir", str(out),
                              "--listings", LISTINGS])


def test_guarded_run_writes_result_with_provenance_bound_to_the_plan(world):
    path, psha, doc = world["plan"]()
    out, payload = run(world, path, psha)
    result = guard.check_output(out, expected_plan_sha256=psha)
    assert result["decision"] == {"verdict": "STOP"} and payload["decision"] == {"verdict": "STOP"}
    prov = result["provenance"]
    assert prov["listings_sha256"] == doc["inputs"][LISTINGS] and prov["archive_sha256"] == doc["inputs"][wrapper.ARCHIVE]
    assert prov["runner_sha256"] == doc["sources"][wrapper.REQUIRED_SOURCES[0]]
    assert world["calls"]["load"] == (world["root"] / wrapper.ARCHIVE, world["root"] / wrapper.MANIFEST)
    assert world["calls"]["run"][2] == {7: {"status": "never_listed"}}  # parsed by the frozen runner's parser
    assert sorted(p.name for p in out.iterdir()) == ["pin_receipt.json", "result.json"]


@pytest.mark.parametrize("change", ["prereg_path", "listings_unpinned", "source_unpinned", "archive_unpinned"])
def test_a_plan_that_does_not_pin_what_is_read_is_refused_without_a_result(world, change):
    _, _, doc = world["plan"]()
    if change == "prereg_path":
        other = world["root"] / "docs/other.md"
        other.write_bytes(b"frozen prereg text\n")
        path, psha, _ = world["plan"](preregistration={"path": "docs/other.md", "sha256": sha(other)})
    elif change == "listings_unpinned":
        inputs = {k: v for k, v in doc["inputs"].items() if k != LISTINGS}
        path, psha, _ = world["plan"](inputs=inputs)
    elif change == "archive_unpinned":
        inputs = {k: v for k, v in doc["inputs"].items() if k != wrapper.ARCHIVE}
        path, psha, _ = world["plan"](inputs=inputs)
    else:
        sources = {k: v for k, v in doc["sources"].items() if k != wrapper.REQUIRED_SOURCES[2]}
        path, psha, _ = world["plan"](sources=sources)
    with pytest.raises(wrapper.PlanMismatch):
        run(world, path, psha)
    out = world["tmp"] / "out"
    assert (out / "refused.json").exists() and not (out / "result.json").exists()
    assert "run" not in world["calls"]
    with pytest.raises(guard.PinError):
        guard.check_output(out, expected_plan_sha256=psha)


def test_imported_modules_must_be_the_pinned_files(world, monkeypatch):
    path, psha, _ = world["plan"]()
    monkeypatch.setattr(engine, "__file__", str(world["tmp"] / "elsewhere.py"))
    with pytest.raises(wrapper.PlanMismatch):
        run(world, path, psha)
    assert "run" not in world["calls"]


def test_a_dependency_hash_mismatch_refuses(world, monkeypatch):
    path, psha, _ = world["plan"]()
    monkeypatch.setattr(wrapper, "dependency_checks", lambda r, rel, s: ((r / wrapper.MANIFEST, "0" * 64),))
    with pytest.raises(wrapper.PlanMismatch):
        run(world, path, psha)
    assert "run" not in world["calls"]


def test_a_listing_file_changed_after_planning_is_refused_before_compute(world):
    path, psha, _ = world["plan"]()
    (world["root"] / LISTINGS).write_bytes(json.dumps({"schema": runner.LISTING_SCHEMA, "assets": {}}).encode())
    with pytest.raises(guard.PinError):
        run(world, path, psha)
    assert "load" not in world["calls"] and "run" not in world["calls"]


def test_dependency_checks_match_the_frozen_runner_main():
    """The wrapper repeats exactly the runner's pinned checks (same paths and expected hashes)."""
    import inspect
    src = inspect.getsource(runner.main)
    for needle in ("(args.prereg, FROZEN_PREREG_SHA256)", "(Path(v2.__file__), V2_RUNNER_SHA256)",
                   "(Path(engine.__file__), v2.ENGINE_HASH)", '(v2.ARTIFACTS / "PROTOCOL.md", engine.PROTOCOL_HASH)',
                   '(v2.ARTIFACTS / "instrument_correction_v2.json", v2.MAP_HASH)',
                   '(v2.ARTIFACTS / "CORRECTION_V2.md", v2.DELTA_HASH)', "(args.listings, args.listings_sha256)"):
        assert needle in src
    root = Path("/r")
    checks = wrapper.dependency_checks(root, "x/l.json", "s" * 64)
    assert checks == ((root / wrapper.PREREG, runner.FROZEN_PREREG_SHA256), (Path(v2.__file__), runner.V2_RUNNER_SHA256),
                      (Path(engine.__file__), v2.ENGINE_HASH), (v2.ARTIFACTS / "PROTOCOL.md", engine.PROTOCOL_HASH),
                      (v2.ARTIFACTS / "instrument_correction_v2.json", v2.MAP_HASH),
                      (v2.ARTIFACTS / "CORRECTION_V2.md", v2.DELTA_HASH), (root / "x/l.json", "s" * 64))
