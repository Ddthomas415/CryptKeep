"""Pinned-input guard: nothing computes unless every pin verifies; no result on change."""
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform

import pytest

from scripts.research import pinned_run_inputs as pins


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(root, rel, data):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha(data)


def write_sums(root, entries):
    text = "".join(f"{digest}  {name}\n" for name, digest in entries)
    return put(root, "data/candles/SHA256SUMS", text.encode())


@pytest.fixture
def study(tmp_path):
    root = tmp_path / "repo"
    members = {"A-USD.json": put(root, "data/candles/A-USD.json", b"[[1,2,3,4,5,6]]"),
               "B-USD.json": put(root, "data/candles/B-USD.json", b"[[7,8,9,10,11,12]]")}
    plan = {
        "schema": pins.SCHEMA,
        "root": str(root),
        "preregistration": {"path": "docs/prereg.md", "sha256": put(root, "docs/prereg.md", b"frozen rule\n")},
        "inputs": {"data/excl.csv": put(root, "data/excl.csv", b"market\nUSDC-USD\n")},
        "input_sets": [{"dir": "data/candles", "sums": "data/candles/SHA256SUMS",
                        "sums_sha256": write_sums(root, sorted(members.items()))}],
        "sources": {"scripts/run.py": put(root, "scripts/run.py", b"print('run')\n")},
        "model": {"revision": "29ec3766d36d6f73f0696f85560a422f50e8498c",
                  "files": {"models/m/model.safetensors": put(root, "models/m/model.safetensors", b"weights"),
                            "models/m/config.json": put(root, "models/m/config.json", b"{}")}},
        "runtime": {"python": platform.python_version(), "packages": {"pytest": metadata.version("pytest")}},
    }
    return tmp_path, root, plan


def save_plan(tmp_path, plan):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path, sha(path.read_bytes())


def never(plan):
    raise AssertionError("compute must not run")


def test_valid_plan_records_receipt_before_compute_and_result_after(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    seen = {}

    def compute(verified):
        seen["receipt_existed"] = (out / "pin_receipt.json").is_file()
        seen["result_existed"] = (out / "result.json").exists()
        return {"value": 1}

    result = pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert seen == {"receipt_existed": True, "result_existed": False}
    receipt_bytes = (out / "pin_receipt.json").read_bytes()
    receipt = json.loads(receipt_bytes)
    assert receipt["plan_sha256"] == plan_sha
    assert receipt["files"] == {
        "data/candles/A-USD.json": sha(b"[[1,2,3,4,5,6]]"),
        "data/candles/B-USD.json": sha(b"[[7,8,9,10,11,12]]"),
        "data/candles/SHA256SUMS": plan["input_sets"][0]["sums_sha256"],
        "data/excl.csv": plan["inputs"]["data/excl.csv"],
        "docs/prereg.md": plan["preregistration"]["sha256"],
        "models/m/config.json": sha(b"{}"),
        "models/m/model.safetensors": sha(b"weights"),
        "scripts/run.py": plan["sources"]["scripts/run.py"],
    }
    assert receipt["model_revision"] == plan["model"]["revision"]
    assert receipt["runtime"] == {"python": platform.python_version(), "pytest": metadata.version("pytest")}
    saved = json.loads((out / "result.json").read_bytes())
    assert saved == result
    assert saved["value"] == 1
    assert saved["pinned_inputs"] == {"plan_sha256": plan_sha, "receipt_sha256": sha(receipt_bytes)}


def _replace_with_symlink(root, rel):
    target = root.parent / ("copy_" + Path(rel).name)
    target.write_bytes((root / rel).read_bytes())
    (root / rel).unlink()
    os.symlink(target, root / rel)


TAMPER = {
    "prereg_changed": (lambda r, p: (r / "docs/prereg.md").write_bytes(b"edited rule\n"),
                       "hash_mismatch:docs/prereg.md"),
    "input_changed": (lambda r, p: (r / "data/excl.csv").write_bytes(b"market\n"),
                      "hash_mismatch:data/excl.csv"),
    "input_missing": (lambda r, p: (r / "data/excl.csv").unlink(), "missing:data/excl.csv"),
    "source_changed": (lambda r, p: (r / "scripts/run.py").write_bytes(b"print('other')\n"),
                       "hash_mismatch:scripts/run.py"),
    "model_weights_changed": (lambda r, p: (r / "models/m/model.safetensors").write_bytes(b"other"),
                              "hash_mismatch:models/m/model.safetensors"),
    "set_member_changed": (lambda r, p: (r / "data/candles/A-USD.json").write_bytes(b"[]"),
                           "hash_mismatch:data/candles/A-USD.json"),
    "set_member_missing": (lambda r, p: (r / "data/candles/B-USD.json").unlink(),
                           "missing:data/candles/B-USD.json"),
    "set_unlisted_file": (lambda r, p: (r / "data/candles/C-USD.json").write_bytes(b"[]"),
                          "unlisted_file:data/candles/C-USD.json"),
    "sums_changed": (lambda r, p: (r / "data/candles/SHA256SUMS").write_bytes(b""),
                     "hash_mismatch:data/candles/SHA256SUMS"),
    "input_symlinked": (lambda r, p: _replace_with_symlink(r, "data/excl.csv"),
                        "symlink_refused:data/excl.csv"),
    # Review findings F6, F9, F11, F14 (2026-10-19 GATE review)
    "pinned_path_is_directory": (lambda r, p: p["inputs"].update({"data/candles": "0" * 64}),
                                 "not_a_regular_file:data/candles"),
    "model_null": (lambda r, p: p.update(model=None), "bad_model_pin"),
    "runtime_empty": (lambda r, p: p.update(runtime={}), "empty_runtime_pin"),
    "runtime_empty_package_name": (lambda r, p: p["runtime"]["packages"].update({"": "1"}), "bad_runtime"),
    "set_unlisted_empty_directory": (lambda r, p: (r / "data/candles/emptydir").mkdir(),
                                     "unlisted_directory:data/candles/emptydir"),
    "set_case_duplicate_entry": (lambda r, p: p["input_sets"][0].update(sums_sha256=write_sums(
        r, [("A-USD.json", sha(b"[[1,2,3,4,5,6]]")), ("a-usd.json", sha(b"[[1,2,3,4,5,6]]")),
            ("B-USD.json", sha(b"[[7,8,9,10,11,12]]"))])), "colliding_sums_entry:a-usd.json"),
    "set_member_symlinked": (lambda r, p: _replace_with_symlink(r, "data/candles/A-USD.json"),
                             "symlink_refused:data/candles/A-USD.json"),
    "parent_dir_symlinked": (lambda r, p: (os.symlink(r / "data", r / "link"),
                                           p["inputs"].update({"link/excl.csv": p["inputs"].pop("data/excl.csv")})),
                             "symlink_refused:link/excl.csv"),
    "path_traversal": (lambda r, p: p["inputs"].update({"../outside.csv": "0" * 64}),
                       "path_outside_root:../outside.csv"),
    "absolute_path": (lambda r, p: p["inputs"].update({str(r / "data/excl.csv"): "0" * 64}),
                      "path_outside_root:"),
    "bad_hash_format": (lambda r, p: p["sources"].update({"scripts/run.py": p["sources"]["scripts/run.py"].upper()}),
                        "bad_hash_format:scripts/run.py"),
    "unknown_plan_key": (lambda r, p: p.update(input={}), "unknown_plan_keys:input"),
    "no_preregistration": (lambda r, p: p.pop("preregistration"), "preregistration_pin_required"),
    "no_sources": (lambda r, p: p.update(sources={}), "source_pins_required"),
    "no_inputs": (lambda r, p: p.update(inputs={}, input_sets=[]), "input_pins_required"),
    "relative_root": (lambda r, p: p.update(root="repo"), "root_must_be_absolute"),
    "model_revision_not_commit": (lambda r, p: p["model"].update(revision="main"),
                                  "bad_hash_format:model_revision"),
    "model_without_files": (lambda r, p: p["model"].update(files={}), "bad_model_pin"),
    "python_version_differs": (lambda r, p: p["runtime"].update(python="0.0.0"), "runtime_mismatch:python"),
    "package_version_differs": (lambda r, p: p["runtime"]["packages"].update(pytest="0.0.0"),
                                "runtime_mismatch:pytest"),
    "package_missing": (lambda r, p: p["runtime"]["packages"].update({"no-such-package-cbp": "1.0"}),
                        "runtime_missing:no-such-package-cbp"),
}


@pytest.mark.parametrize("case", sorted(TAMPER))
def test_any_failed_pin_refuses_before_compute_and_creates_no_output(study, case):
    tmp_path, root, plan = study
    change, reason = TAMPER[case]
    change(root, plan)
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, never, plan_sha256=plan_sha)
    assert any(failure.startswith(reason) for failure in error.value.failures), error.value.failures
    assert not out.exists()


def test_sums_file_listing_itself_is_refused(study):
    tmp_path, root, plan = study
    entries = [("A-USD.json", sha(b"[[1,2,3,4,5,6]]")), ("B-USD.json", sha(b"[[7,8,9,10,11,12]]")),
               ("SHA256SUMS", "0" * 64)]
    plan["input_sets"][0]["sums_sha256"] = write_sums(root, entries)
    path, plan_sha = save_plan(tmp_path, plan)
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=plan_sha)
    assert "hash_mismatch:data/candles/SHA256SUMS" in error.value.failures


def test_every_failure_is_reported_not_only_the_first(study):
    tmp_path, root, plan = study
    (root / "docs/prereg.md").write_bytes(b"edited\n")
    (root / "models/m/config.json").write_bytes(b"{\"x\":1}")
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert error.value.failures == ["hash_mismatch:docs/prereg.md", "hash_mismatch:models/m/config.json"]


def test_plan_file_itself_must_match_its_pin(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256="0" * 64)
    assert error.value.failures == ["plan_hash_mismatch"]
    assert not (tmp_path / "out").exists()


def test_non_finite_constant_in_plan_is_refused(study):
    tmp_path, root, plan = study
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan)[:-1] + ', "note": NaN}')
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=sha(path.read_bytes()))
    assert error.value.failures == ["non_finite_json:NaN"]


def test_input_changed_during_compute_leaves_receipt_but_no_result(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    original = plan["inputs"]["data/excl.csv"]

    def compute(verified):
        (root / "data/excl.csv").write_bytes(b"changed mid-run\n")
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert error.value.failures == ["hash_mismatch:data/excl.csv"]
    assert json.loads((out / "pin_receipt.json").read_bytes())["files"]["data/excl.csv"] == original
    assert not (out / "result.json").exists()


def test_compute_error_leaves_no_result(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert (out / "pin_receipt.json").is_file()
    assert not (out / "result.json").exists()


@pytest.mark.parametrize("returned", [None, [1], {"x": float("nan")}])
def test_non_dict_or_non_finite_result_is_not_written(study, returned):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    with pytest.raises(ValueError):
        pins.run_pinned(path, out, lambda verified: returned, plan_sha256=plan_sha)
    assert not (out / "result.json").exists()


def test_existing_output_directory_is_never_reused(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    (tmp_path / "out").mkdir()
    with pytest.raises(FileExistsError):
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=plan_sha)
    assert list((tmp_path / "out").iterdir()) == []


# ---- Regressions for the 2026-10-19 independent review findings (F1-F14) ----

def test_f1_compute_cannot_redirect_the_post_run_check(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    clean = tmp_path / "clean"
    import shutil
    shutil.copytree(root, clean)

    def compute(verified):
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        verified["root"] = str(clean)
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert "hash_mismatch:data/excl.csv" in error.value.failures
    assert not (out / "result.json").exists()
    assert json.loads((out / "refused.json").read_bytes())["failures"] == error.value.failures


def test_f1_compute_receives_a_copy_so_clearing_it_changes_nothing(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        verified.clear()
        return {"value": 2}

    assert pins.run_pinned(path, out, compute, plan_sha256=plan_sha)["value"] == 2
    assert pins.check_output(out)["value"] == 2


@pytest.mark.parametrize("name", ["result.json", "extra.txt"])
def test_f2_any_file_written_by_compute_is_refused_and_output_check_fails(study, name):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        (out / name).write_text('{"value": 999}')
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert error.value.failures == ["unexpected_output_files:" + name]
    assert (out / "refused.json").is_file()
    with pytest.raises(pins.PinError, match="output_incomplete_or_refused"):
        pins.check_output(out)


def test_f3_symlinked_root_is_refused_before_compute(study):
    tmp_path, root, plan = study
    os.symlink(root, tmp_path / "rootlink")
    plan["root"] = str(tmp_path / "rootlink")
    path, plan_sha = save_plan(tmp_path, plan)
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=plan_sha)
    assert error.value.failures == ["root_not_canonical"]
    assert not (tmp_path / "out").exists()


def test_f3_dotdot_in_root_is_refused(study):
    tmp_path, root, plan = study
    plan["root"] = str(root / ".." / "repo")
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert error.value.failures == ["root_not_canonical"]


def test_f4_unreadable_subdirectory_in_a_set_is_reported(study, monkeypatch):
    tmp_path, root, plan = study
    (root / "data/candles/locked").mkdir()
    (root / "data/candles/locked/extra.json").write_bytes(b"[]")
    real = pins._list_entries

    def denied(dir_fd, label):
        if label.endswith("locked"):
            raise PermissionError(13, "Permission denied", label)
        return real(dir_fd, label)

    monkeypatch.setattr(pins, "_list_entries", denied)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert "unreadable_directory:data/candles/locked" in error.value.failures


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no FIFOs on this platform")
@pytest.mark.parametrize("where", ["input", "set_member"])
def test_f5_fifo_is_refused_without_opening_it(study, where):
    tmp_path, root, plan = study
    if where == "input":
        os.mkfifo(root / "data/fifo")
        plan["inputs"]["data/fifo"] = "0" * 64
        reason = "not_a_regular_file:data/fifo"
    else:
        (root / "data/candles/B-USD.json").unlink()
        os.mkfifo(root / "data/candles/B-USD.json")
        reason = "not_a_regular_file:data/candles/B-USD.json"
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert reason in error.value.failures


def test_f6_structural_and_file_failures_are_reported_together(study):
    tmp_path, root, plan = study
    del plan["preregistration"]["sha256"]
    (root / "scripts/run.py").write_bytes(b"changed\n")
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert error.value.failures == ["preregistration_pin_required", "hash_mismatch:scripts/run.py"]


def test_f6_failed_checksum_list_says_its_members_were_not_checked(study):
    tmp_path, root, plan = study
    (root / "data/candles/SHA256SUMS").write_bytes(b"")
    (root / "data/candles/A-USD.json").write_bytes(b"[]")
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert error.value.failures == ["hash_mismatch:data/candles/SHA256SUMS",
                                    "set_members_not_checked:data/candles"]


def test_f7_plan_file_changed_during_compute_is_refused(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        path.write_text(json.dumps({**plan, "inputs": {}}))
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert error.value.failures == ["plan_changed_during_run"]
    assert not (out / "result.json").exists()


def test_f8_duplicate_plan_keys_are_refused(study):
    tmp_path, root, plan = study
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan)[:-1] + ', "model": null}')
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=sha(path.read_bytes()))
    assert error.value.failures == ["duplicate_json_key:model"]


def test_f10_output_directory_inside_a_pinned_set_is_refused_before_compute(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = root / "data/candles/out"
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, never, plan_sha256=plan_sha)
    assert error.value.failures == ["out_dir_inside_pinned_set:data/candles"]
    assert not out.exists()


def test_f11_listed_nested_file_is_still_accepted(study):
    tmp_path, root, plan = study
    nested = put(root, "data/candles/sub/C-USD.json", b"[]")
    entries = [("A-USD.json", sha(b"[[1,2,3,4,5,6]]")), ("B-USD.json", sha(b"[[7,8,9,10,11,12]]")),
               ("sub/C-USD.json", nested)]
    plan["input_sets"][0]["sums_sha256"] = write_sums(root, entries)
    assert pins.verify(plan)["files"]["data/candles/sub/C-USD.json"] == nested


def test_check_output_requires_receipt_link(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    pins.run_pinned(path, out, lambda verified: {"value": 3}, plan_sha256=plan_sha)
    assert pins.check_output(out)["value"] == 3
    receipt = out / "pin_receipt.json"
    receipt.write_bytes(receipt.read_bytes().replace(b'"schema"', b'"schema" ', 1))
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_link_mismatch"]


def test_compute_error_records_refusal(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert json.loads((out / "refused.json").read_bytes())["failures"] == ["compute_error:RuntimeError"]
    with pytest.raises(pins.PinError):
        pins.check_output(out)


# ---- Regressions for the second independent review findings (R1-R11) ----

import shutil
import unicodedata


def _valid_run(tmp_path, plan, value=1):
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    pins.run_pinned(path, out, lambda verified: {"value": value}, plan_sha256=plan_sha)
    return out, plan_sha


def _relink(out, receipt):
    data = (json.dumps(receipt) + "\n").encode()
    (out / "pin_receipt.json").write_bytes(data)
    result = json.loads((out / "result.json").read_bytes())
    result["pinned_inputs"]["receipt_sha256"] = sha(data)
    (out / "result.json").write_text(json.dumps(result))


def test_r1_minimal_handmade_pair_is_rejected(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    receipt = b'{"schema": "pinned-run-receipt-v1"}'
    (out / "pin_receipt.json").write_bytes(receipt)
    (out / "result.json").write_text(json.dumps({"v": 42, "pinned_inputs": {"receipt_sha256": sha(receipt)}}))
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_bad_receipt"]


@pytest.mark.parametrize("change", ["drop_key", "plan_hash_none", "files_empty", "revision_not_commit",
                                    "bad_timestamp", "prereg_not_in_files", "runtime_not_text"])
def test_r1_structurally_incomplete_receipt_is_rejected_even_when_linked(study, change):
    tmp_path, root, plan = study
    out, plan_sha = _valid_run(tmp_path, plan)
    receipt = json.loads((out / "pin_receipt.json").read_bytes())
    if change == "drop_key":
        del receipt["verified_utc"]
    elif change == "plan_hash_none":
        receipt["plan_sha256"] = None
    elif change == "files_empty":
        receipt["files"] = {}
    elif change == "revision_not_commit":
        receipt["model_revision"] = "main"
    elif change == "bad_timestamp":
        receipt["verified_utc"] = "yesterday"
    elif change == "prereg_not_in_files":
        receipt["preregistration_sha256"] = "0" * 64
    else:
        receipt["runtime"] = {"python": 3}
    _relink(out, receipt)
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_bad_receipt"]


def test_r1_link_must_carry_matching_plan_hash(study):
    tmp_path, root, plan = study
    out, plan_sha = _valid_run(tmp_path, plan)
    result = json.loads((out / "result.json").read_bytes())
    del result["pinned_inputs"]["plan_sha256"]
    (out / "result.json").write_text(json.dumps(result))
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_link_mismatch"]


def test_r1_expected_plan_hash_binds_the_output(study):
    tmp_path, root, plan = study
    out, plan_sha = _valid_run(tmp_path, plan, value=7)
    assert pins.check_output(out, expected_plan_sha256=plan_sha)["value"] == 7
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out, expected_plan_sha256="0" * 64)
    assert error.value.failures == ["output_plan_mismatch"]


def _move_out_to_symlink(out, tmp_path):
    os.rename(out, tmp_path / "moved_out")
    (tmp_path / "elsewhere").mkdir()
    os.symlink(tmp_path / "elsewhere", out)


R2_ACTIONS = {
    "delete_receipt": (lambda out, tmp: (out / "pin_receipt.json").unlink(), "receipt_changed_during_run"),
    "edit_receipt": (lambda out, tmp: (out / "pin_receipt.json").write_text("{}"), "receipt_changed_during_run"),
    "receipt_replaced_by_directory": (lambda out, tmp: ((out / "pin_receipt.json").unlink(),
                                                        (out / "pin_receipt.json").mkdir()),
                                      "receipt_changed_during_run"),
    "out_dir_recreated": (lambda out, tmp: (shutil.rmtree(out), out.mkdir()), "out_dir_replaced_during_run"),
    "out_dir_removed": (lambda out, tmp: shutil.rmtree(out), "out_dir_replaced_during_run"),
    "out_dir_swapped_for_symlink": (_move_out_to_symlink, "out_dir_replaced_during_run"),
}


@pytest.mark.parametrize("case", sorted(R2_ACTIONS))
def test_r2_receipt_and_output_directory_must_survive_compute(study, case):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    action, reason = R2_ACTIONS[case]

    def compute(verified):
        action(out, tmp_path)
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert reason in error.value.failures
    assert not (out / "result.json").exists()
    assert not (tmp_path / "elsewhere" / "result.json").exists()
    assert not (tmp_path / "moved_out" / "result.json").exists()


def test_r3_unencodable_deep_result_is_refused_with_record(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    deep = []
    for _ in range(200_000):
        deep = [deep]

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, lambda verified: {"deep": deep}, plan_sha256=plan_sha)
    assert error.value.failures == ["result_not_encodable"]
    assert json.loads((out / "refused.json").read_bytes())["failures"] == ["result_not_encodable"]
    assert not (out / "result.json").exists()


def test_r4_compute_changing_directory_does_not_redirect_relative_paths(study, monkeypatch):
    tmp_path, root, plan = study
    save_plan(tmp_path, plan)
    plan_sha = sha((tmp_path / "plan.json").read_bytes())
    (tmp_path / "other").mkdir()
    monkeypatch.chdir(tmp_path)

    def compute(verified):
        os.chdir(tmp_path / "other")
        return {"value": 4}

    pins.run_pinned("plan.json", "out", compute, plan_sha256=plan_sha)
    assert pins.check_output(tmp_path / "out", expected_plan_sha256=plan_sha)["value"] == 4
    assert list((tmp_path / "other").iterdir()) == []


def test_r5_compute_written_result_is_set_aside_even_if_refusal_write_fails(study, monkeypatch):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"
    real_write = pins._write_new

    def failing_refusal(dir_fd, name, data):
        if name == pins.REFUSED_NAME:
            raise OSError(28, "No space left on device")
        return real_write(dir_fd, name, data)

    monkeypatch.setattr(pins, "_write_new", failing_refusal)

    def compute(verified):
        receipt = (out / "pin_receipt.json").read_bytes()
        forged = {"value": 9, "pinned_inputs": {"plan_sha256": plan_sha, "receipt_sha256": sha(receipt)}}
        (out / "result.json").write_text(json.dumps(forged))
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        return {"value": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert sorted(p.name for p in out.iterdir()) == ["pin_receipt.json", "result.json.unguarded"]
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_r6_compute_written_refusal_record_is_set_aside(study):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def compute(verified):
        (out / "refused.json").write_text('{"failures": [], "note": "all good"}')
        return {"value": 1}

    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, compute, plan_sha256=plan_sha)
    assert error.value.failures == ["unexpected_output_files:refused.json"]
    assert json.loads((out / "refused.json").read_bytes())["failures"] == error.value.failures
    assert "all good" in (out / "refused.json.unguarded").read_text()


def test_r7_output_path_aliasing_a_pinned_set_is_refused_by_identity(study, monkeypatch):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    os.symlink(root / "data/candles", tmp_path / "view")
    out = tmp_path / "view" / "out"
    monkeypatch.setattr(pins.os.path, "realpath", lambda value: str(Path(value)))  # mount realpath cannot see
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, never, plan_sha256=plan_sha)
    assert error.value.failures == ["out_dir_inside_pinned_set:data/candles"]
    assert not (root / "data/candles/out").exists()


def test_r8_parent_directory_swapped_for_symlink_mid_check_is_not_followed(study, monkeypatch):
    tmp_path, root, plan = study
    real_stat = os.stat
    swapped = []

    def racing_stat(target, *, dir_fd=None, follow_symlinks=True):
        result = real_stat(target, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        if target == "data" and dir_fd is not None and not swapped:
            swapped.append(True)
            os.rename(root / "data", tmp_path / "data_real")
            shutil.copytree(tmp_path / "data_real", tmp_path / "data_copy")
            os.symlink(tmp_path / "data_copy", root / "data")
        return result

    monkeypatch.setattr(os, "stat", racing_stat)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert swapped
    assert "symlink_or_replaced:data/excl.csv" in error.value.failures


@pytest.mark.parametrize("change,reason", [
    (lambda p: p.update(root="/tmp/bad\x00root"), "bad_root"),
    (lambda p: p["inputs"].update({"data/\udcff.csv": "0" * 64}), "bad_path:"),
])
def test_r9_odd_paths_are_reported_not_raised(study, change, reason):
    tmp_path, root, plan = study
    change(plan)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert any(failure.startswith(reason) for failure in error.value.failures), error.value.failures


def test_r9_deeply_nested_plan_is_reported_not_raised(study):
    tmp_path, root, plan = study
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan)[:-1] + ', "x": ' + "[" * 100_000 + "]" * 100_000 + "}")
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=sha(path.read_bytes()))
    assert error.value.failures == ["bad_json:plan"]


def test_r9_check_output_on_missing_or_symlinked_directory(tmp_path):
    with pytest.raises(pins.PinError) as error:
        pins.check_output(tmp_path / "absent")
    assert error.value.failures == ["output_unreadable"]
    (tmp_path / "real").mkdir()
    os.symlink(tmp_path / "real", tmp_path / "link")
    with pytest.raises(pins.PinError) as error:
        pins.check_output(tmp_path / "link")
    assert error.value.failures == ["output_unreadable"]


def test_r10_new_parent_directories_are_flushed(study, monkeypatch):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    flushed = []
    real = pins._fsync_path
    monkeypatch.setattr(pins, "_fsync_path", lambda p: (flushed.append(Path(p)), real(p)))
    out = tmp_path / "a" / "b" / "out"
    pins.run_pinned(path, out, lambda verified: {"value": 1}, plan_sha256=plan_sha)
    assert flushed == [tmp_path, tmp_path / "a", tmp_path / "a" / "b"]


def test_r11_unicode_normalisation_variants_collide(study):
    tmp_path, root, plan = study
    nfc = unicodedata.normalize("NFC", "café.json")
    nfd = unicodedata.normalize("NFD", "café.json")
    assert nfc != nfd
    entries = [("A-USD.json", sha(b"[[1,2,3,4,5,6]]")), ("B-USD.json", sha(b"[[7,8,9,10,11,12]]")),
               (nfc, "0" * 64), (nfd, "0" * 64)]
    plan["input_sets"][0]["sums_sha256"] = write_sums(root, entries)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert "colliding_sums_entry:" + nfd in error.value.failures


@pytest.mark.parametrize("swap,reason", [("file", "replaced_while_opening:data/excl.csv"),
                                         ("symlink", "unreadable_or_replaced:data/excl.csv")])
def test_file_swapped_between_stat_and_open_is_refused(study, monkeypatch, swap, reason):
    tmp_path, root, plan = study
    target = root / "data/excl.csv"
    real_open = os.open
    done = []

    def racing_open(path, flags, *args, dir_fd=None, **kwargs):
        if path == "excl.csv" and dir_fd is not None and not done:
            done.append(True)
            replacement = tmp_path / "swap"
            replacement.write_bytes(target.read_bytes())  # identical content, new inode
            if swap == "file":
                os.replace(replacement, target)
            else:
                target.unlink()
                os.symlink(replacement, target)
        return real_open(path, flags, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(os, "open", racing_open)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert done
    assert reason in error.value.failures


@pytest.mark.parametrize("name", ["result.json", "pin_receipt.json"])
def test_check_output_rejects_symlinked_or_directory_members(study, name):
    tmp_path, root, plan = study
    out, plan_sha = _valid_run(tmp_path, plan)
    real = tmp_path / ("real_" + name)
    shutil.move(out / name, real)
    os.symlink(real, out / name)
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_not_regular_file:" + name]
    (out / name).unlink()
    (out / name).mkdir()
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_not_regular_file:" + name]


def test_r1_link_with_a_different_plan_hash_is_rejected(study):
    tmp_path, root, plan = study
    out, plan_sha = _valid_run(tmp_path, plan)
    result = json.loads((out / "result.json").read_bytes())
    result["pinned_inputs"]["plan_sha256"] = "f" * 64
    (out / "result.json").write_text(json.dumps(result))
    with pytest.raises(pins.PinError) as error:
        pins.check_output(out)
    assert error.value.failures == ["output_link_mismatch"]


def test_r3_unexpected_error_in_post_run_checks_is_refused_with_record(study, monkeypatch):
    tmp_path, root, plan = study
    path, plan_sha = save_plan(tmp_path, plan)
    out = tmp_path / "out"

    def broken(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(pins, "_post_run", broken)
    with pytest.raises(pins.PinError) as error:
        pins.run_pinned(path, out, lambda verified: {"value": 1}, plan_sha256=plan_sha)
    assert error.value.failures == ["post_run_check_error:RuntimeError"]
    assert json.loads((out / "refused.json").read_bytes())["failures"] == error.value.failures
    assert not (out / "result.json").exists()


def test_subdirectory_swapped_during_set_scan_is_refused(study, monkeypatch):
    tmp_path, root, plan = study
    nested = put(root, "data/candles/sub/C-USD.json", b"[]")
    entries = [("A-USD.json", sha(b"[[1,2,3,4,5,6]]")), ("B-USD.json", sha(b"[[7,8,9,10,11,12]]")),
               ("sub/C-USD.json", nested)]
    plan["input_sets"][0]["sums_sha256"] = write_sums(root, entries)
    real_open = os.open
    done = []

    def racing_open(path, flags, *args, dir_fd=None, **kwargs):
        if path == "sub" and dir_fd is not None and not done:
            done.append(True)
            os.rename(root / "data/candles/sub", tmp_path / "sub_old")
            shutil.copytree(tmp_path / "sub_old", root / "data/candles/sub")
        return real_open(path, flags, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(os, "open", racing_open)
    with pytest.raises(pins.PinError) as error:
        pins.verify(plan)
    assert done
    assert error.value.failures == ["replaced_while_opening:data/candles/sub"]
