"""Adversarial probes for pinned_run_inputs. Each test asserts the behaviour
the reviewer considers correct (fail closed) unless named obs_* (observation of
actual behaviour, used as evidence)."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from importlib import metadata

import pytest

from scripts.research import pinned_run_inputs as pins

REPO = Path(pins.__file__).resolve().parents[2]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def put(root, rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return sha(data)


A, B = b"[[1,2,3,4,5,6]]", b"[[7,8,9,10,11,12]]"


def sums_bytes(entries, sep="  ", eol="\n"):
    return "".join(f"{d}{sep}{n}{eol}" for n, d in entries).encode()


@pytest.fixture
def study(tmp_path):
    root = tmp_path / "repo"
    put(root, "data/candles/A-USD.json", A)
    put(root, "data/candles/B-USD.json", B)
    s = put(root, "data/candles/SHA256SUMS", sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))]))
    plan = {
        "schema": pins.SCHEMA, "root": str(root),
        "preregistration": {"path": "docs/prereg.md", "sha256": put(root, "docs/prereg.md", b"rule\n")},
        "inputs": {"data/excl.csv": put(root, "data/excl.csv", b"x\n")},
        "input_sets": [{"dir": "data/candles", "sums": "data/candles/SHA256SUMS", "sums_sha256": s}],
        "sources": {"scripts/run.py": put(root, "scripts/run.py", b"pass\n")},
        "model": {"revision": "a" * 40, "files": {"models/m.bin": put(root, "models/m.bin", b"weights")}},
        "runtime": {"python": platform.python_version(), "packages": {"pytest": metadata.version("pytest")}},
    }
    return tmp_path, root, plan


def save(tmp_path, plan, text=None):
    p = tmp_path / "plan.json"
    p.write_text(text if text is not None else json.dumps(plan))
    return p, sha(p.read_bytes())


def set_sums(root, plan, raw):
    plan["input_sets"][0]["sums_sha256"] = put(root, "data/candles/SHA256SUMS", raw)


def refused(tmp_path, plan, reason_prefix=None):
    path, h = save(tmp_path, plan)
    called = []
    with pytest.raises(Exception) as e:
        pins.run_pinned(path, tmp_path / "out", lambda p: called.append(1) or {"v": 1}, plan_sha256=h)
    assert not called, "compute ran"
    assert not (tmp_path / "out" / "result.json").exists()
    if reason_prefix:
        assert isinstance(e.value, pins.PinError), repr(e.value)
        assert any(f.startswith(reason_prefix) for f in e.value.failures), e.value.failures
    return e.value


def accepted(tmp_path, plan):
    path, h = save(tmp_path, plan)
    return pins.run_pinned(path, tmp_path / "out", lambda p: {"v": 1}, plan_sha256=h)


# ---- symlinks / special files -------------------------------------------------

def test_symlinked_root_component_is_refused(study):
    tmp_path, root, plan = study
    link = tmp_path / "rootlink"
    os.symlink(root, link)
    plan["root"] = str(link)
    refused(tmp_path, plan, "symlink_refused")


def test_pinned_path_that_is_directory_is_refused(study):
    tmp_path, root, plan = study
    (root / "data/dirpin").mkdir()
    plan["inputs"]["data/dirpin"] = "0" * 64
    refused(tmp_path, plan, "not_a_regular_file:data/dirpin")


def _run_child(code, timeout=6):
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run([sys.executable, "-c", code], env=env, timeout=timeout, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""


def test_fifo_listed_in_sums_does_not_hang(study):
    tmp_path, root, plan = study
    os.mkfifo(root / "data/candles/F")
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("F", "0" * 64)]))
    rc, out = _run_child(f"from scripts.research import pinned_run_inputs as p; import json\n"
                         f"p.verify(json.loads({json.dumps(json.dumps(plan))}))")
    assert rc != "TIMEOUT", "verify blocked forever opening a FIFO"


def test_fifo_as_pinned_input_does_not_hang(study):
    tmp_path, root, plan = study
    os.mkfifo(root / "data/fifo")
    plan["inputs"]["data/fifo"] = "0" * 64
    rc, out = _run_child(f"from scripts.research import pinned_run_inputs as p; import json\n"
                         f"p.verify(json.loads({json.dumps(json.dumps(plan))}))")
    assert rc != "TIMEOUT", "verify blocked forever opening a FIFO"


def test_unlisted_fifo_in_set_is_refused(study):
    tmp_path, root, plan = study
    os.mkfifo(root / "data/candles/F")
    refused(tmp_path, plan, "unlisted_file:data/candles/F")


def test_hidden_unlisted_file_refused(study):
    tmp_path, root, plan = study
    put(root, "data/candles/.hidden", b"x")
    refused(tmp_path, plan, "unlisted_file:data/candles/.hidden")


def test_nested_unlisted_file_refused(study):
    tmp_path, root, plan = study
    put(root, "data/candles/sub/C.json", b"x")
    refused(tmp_path, plan, "unlisted_file:data/candles/sub/C.json")


def test_nested_listed_file_accepted(study):
    tmp_path, root, plan = study
    c = put(root, "data/candles/sub/C.json", b"x")
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("sub/C.json", c)]))
    assert accepted(tmp_path, plan)["v"] == 1


def test_obs_empty_extra_subdirectory_accepted(study):
    tmp_path, root, plan = study
    (root / "data/candles/emptydir").mkdir()
    assert accepted(tmp_path, plan)["v"] == 1


def test_symlinked_subdir_in_set_refused(study):
    tmp_path, root, plan = study
    (tmp_path / "elsewhere").mkdir()
    os.symlink(tmp_path / "elsewhere", root / "data/candles/lnk")
    refused(tmp_path, plan, "symlink_refused:data/candles/lnk")


# ---- sums format ----------------------------------------------------------------

def test_sums_crlf_accepted_and_bytes_pinned(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))], eol="\r\n"))
    assert accepted(tmp_path, plan)["v"] == 1


def test_sums_bom_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, b"\xef\xbb\xbf" + sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))]))
    refused(tmp_path, plan, "bad_sums_line")


def test_sums_trailing_space_name_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json ", sha(A)), ("B-USD.json", sha(B))]))
    refused(tmp_path, plan, "missing:data/candles/A-USD.json ")


def test_sums_binary_marker_accepted(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))], sep=" *"))
    assert accepted(tmp_path, plan)["v"] == 1


def test_sums_name_with_spaces_accepted(study):
    tmp_path, root, plan = study
    c = put(root, "data/candles/C USD.json", b"c")
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("C USD.json", c)]))
    assert accepted(tmp_path, plan)["v"] == 1


def test_sums_duplicate_entry_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("A-USD.json", sha(A))]))
    refused(tmp_path, plan, "duplicate_sums_entry:A-USD.json")


def test_sums_dotdot_name_refused(study):
    tmp_path, root, plan = study
    (root / "data/candles/sub").mkdir()
    set_sums(root, plan, sums_bytes([("sub/../A-USD.json", sha(A)), ("B-USD.json", sha(B))]))
    refused(tmp_path, plan, "path_outside_root:sub/../A-USD.json")


def test_sums_escape_dir_name_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("../excl.csv", sha(b"x\n"))]))
    refused(tmp_path, plan, "path_outside_root")


def test_obs_sums_trailing_blank_line_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))]) + b"\n")
    refused(tmp_path, plan, "bad_sums_line")


def test_sums_single_space_bsd_style_refused(study):
    tmp_path, root, plan = study
    set_sums(root, plan, sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))], sep=" "))
    refused(tmp_path, plan, "bad_sums_line")


# ---- plan types -------------------------------------------------------------------

def test_same_file_two_groups_different_hash_refused(study):
    tmp_path, root, plan = study
    plan["sources"]["data/excl.csv"] = "1" * 64
    refused(tmp_path, plan, "hash_mismatch:data/excl.csv")


@pytest.mark.parametrize("mut,reason", [
    (lambda p: p["preregistration"].update(path=None), "bad_path"),
    (lambda p: p["preregistration"].update(sha256=5), "bad_hash_format"),
    (lambda p: p.update(inputs=None), "input_pins_required"),
    (lambda p: p.update(input_sets=[None]), "bad_input_set"),
    (lambda p: p.update(input_sets={"dir": "x"}), "input_pins_required"),
    (lambda p: p.update(sources=["scripts/run.py"]), "source_pins_required"),
    (lambda p: p.update(model=[]), "bad_model_pin"),
    (lambda p: p["model"].update(revision=None), "bad_hash_format:model_revision"),
    (lambda p: p.update(runtime=None), "bad_runtime"),
    (lambda p: p["runtime"].update(extra=1), "bad_runtime"),
    (lambda p: p["runtime"].update(packages=[]), "bad_runtime"),
    (lambda p: p["runtime"]["packages"].update({"bad name!": "1"}), "runtime_missing"),
    (lambda p: p.update(root=None), "root_must_be_absolute"),
    (lambda p: p.update(schema=None), "bad_schema"),
])
def test_wrong_types_refused(study, mut, reason):
    tmp_path, root, plan = study
    mut(plan)
    refused(tmp_path, plan, reason)


def test_model_null_does_not_disable_model_pin(study):
    tmp_path, root, plan = study
    (root / "models/m.bin").write_bytes(b"TAMPERED")
    plan["model"] = None
    refused(tmp_path, plan)


def test_empty_runtime_is_not_silently_accepted(study):
    tmp_path, root, plan = study
    plan["runtime"] = {}
    refused(tmp_path, plan)


def test_empty_package_name_reported_as_pin_failure(study):
    tmp_path, root, plan = study
    plan["runtime"]["packages"][""] = "1"
    e = refused(tmp_path, plan)
    assert isinstance(e, pins.PinError), repr(e)


def test_duplicate_json_keys_in_plan_refused(study):
    tmp_path, root, plan = study
    (root / "models/m.bin").write_bytes(b"TAMPERED")
    text = json.dumps(plan)[:-1] + ', "model": null}'
    path, h = save(tmp_path, plan, text)
    called = []
    with pytest.raises(Exception):
        pins.run_pinned(path, tmp_path / "out", lambda p: called.append(1) or {"v": 1}, plan_sha256=h)
    assert not called


# ---- all failures reported --------------------------------------------------------

def test_sums_mismatch_does_not_hide_member_failures(study):
    tmp_path, root, plan = study
    (root / "data/candles/SHA256SUMS").write_bytes(b"x")
    (root / "data/candles/A-USD.json").write_bytes(b"tampered")
    e = refused(tmp_path, plan)
    assert any("A-USD.json" in f for f in e.failures), e.failures


def test_structural_error_does_not_hide_file_failures(study):
    tmp_path, root, plan = study
    (root / "scripts/run.py").write_bytes(b"evil\n")
    plan["preregistration"] = {"path": "docs/prereg.md"}
    e = refused(tmp_path, plan)
    assert any("scripts/run.py" in f for f in e.failures), e.failures


# ---- out_dir / compute behaviour --------------------------------------------------

def test_out_dir_inside_pinned_set_leaves_no_result(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = root / "data/candles/out"
    called = []
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, lambda p: called.append(1) or {"v": 1}, plan_sha256=h)
    assert "unlisted_file:data/candles/out/pin_receipt.json" in e.value.failures
    assert called == [1]  # compute DID run; refusal only post-run
    assert not (out / "result.json").exists()


def test_compute_mutating_plan_cannot_redirect_post_check(study):
    tmp_path, root, plan = study
    copy = tmp_path / "pristine"
    shutil.copytree(root, copy)
    path, h = save(tmp_path, plan)

    def compute(p):
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        p["root"] = str(copy)
        return {"v": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)
    assert not (tmp_path / "out/result.json").exists()


def test_compute_dropping_plan_entry_is_refused(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)

    def compute(p):
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        p["inputs"].pop("data/excl.csv")
        return {"v": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)
    assert not (tmp_path / "out/result.json").exists()


def test_compute_written_result_does_not_survive_tamper(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        (out / "result.json").write_text('{"v": 999}')
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        return {"v": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert not (out / "result.json").exists(), (out / "result.json").read_text()


def test_obs_change_reverted_before_post_check_undetected(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)

    def compute(p):
        f = root / "data/excl.csv"
        orig = f.read_bytes()
        f.write_bytes(b"TAMPERED\n")
        seen = f.read_bytes()
        f.write_bytes(orig)
        return {"read": seen.decode()}

    r = pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)
    assert r["read"] == "TAMPERED\n"  # stated limit, reproduced


def test_plan_file_changed_during_compute_is_detected(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)

    def compute(p):
        path.write_text(json.dumps({**plan, "inputs": {}}))
        return {"v": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)


def test_unreadable_subdir_with_unlisted_file_is_refused(study):
    tmp_path, root, plan = study
    put(root, "data/candles/locked/extra.json", b"x")
    os.chmod(root / "data/candles/locked", 0o000)
    code = (f"import json\n"
            f"from scripts.research import pinned_run_inputs as p\n"
            f"try:\n p.verify(json.loads({json.dumps(json.dumps(plan))})); print('ACCEPTED')\n"
            f"except Exception as e: print('REFUSED', e)")
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    # root without DAC override behaves like an unprivileged owner for 000 dirs
    r = subprocess.run(["setpriv", "--bounding-set", "-dac_override,-dac_read_search", "--inh-caps",
                        "-dac_override,-dac_read_search", sys.executable, "-c", code],
                       env=env, capture_output=True, text=True, timeout=20)
    os.chmod(root / "data/candles/locked", 0o755)
    out = r.stdout + r.stderr
    assert "REFUSED" in out, out
