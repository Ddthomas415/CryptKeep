"""Second-reviewer probes for pinned_run_inputs v2.

Tests named want_* assert the behaviour this reviewer considers correct (a failure = finding).
Tests named obs_* record actual behaviour as evidence (they pass when the observation holds).
Tests named ok_* assert a claimed fix or correct behaviour holds.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import unicodedata
from importlib import metadata

import pytest

from scripts.research import pinned_run_inputs as pins

REPO = Path(pins.__file__).resolve().parents[2]
A, B = b"[[1,2,3,4,5,6]]", b"[[7,8,9,10,11,12]]"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def put(root, rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return sha(data)


def sums_bytes(entries):
    return "".join(f"{d}  {n}\n" for n, d in entries).encode()


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


def save(tmp_path, plan, text=None, name="plan.json"):
    p = tmp_path / name
    if isinstance(text, bytes):
        p.write_bytes(text)
    else:
        p.write_text(text if text is not None else json.dumps(plan))
    return p, sha(p.read_bytes())


def run(tmp_path, plan, compute, out=None):
    path, h = save(tmp_path, plan)
    out = out or tmp_path / "out"
    return pins.run_pinned(path, out, compute, plan_sha256=h), out


def good_run(tmp_path, plan):
    payload, out = run(tmp_path, plan, lambda p: {"v": 1})
    return payload, out


# ---- check_output ------------------------------------------------------------------------

def _forge(out, receipt_obj, link):
    out.mkdir(parents=True)
    rb = (json.dumps(receipt_obj) + "\n").encode()
    (out / "pin_receipt.json").write_bytes(rb)
    lk = {k: (sha(rb) if v == "RECEIPT" else v) for k, v in link.items()}
    (out / "result.json").write_text(json.dumps({"v": 42, "pinned_inputs": lk}))


def test_want_check_output_rejects_receipt_without_plan_hash(tmp_path):
    # receipt has only the schema key; result links only receipt_sha256; no plan hash anywhere
    out = tmp_path / "forged"
    _forge(out, {"schema": pins.RECEIPT_SCHEMA}, {"receipt_sha256": "RECEIPT"})
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_obs_check_output_accepts_wellformed_handmade_pair(tmp_path):
    out = tmp_path / "forged2"
    _forge(out, {"schema": pins.RECEIPT_SCHEMA, "plan_sha256": "0" * 64, "files": {}, "runtime": {},
                 "model_revision": None, "preregistration_sha256": "0" * 64, "verified_utc": "x"},
           {"receipt_sha256": "RECEIPT", "plan_sha256": "0" * 64})
    assert pins.check_output(out)["v"] == 42


def test_ok_check_output_rejects_extra_hidden_file(study):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    (out / ".DS_Store").write_bytes(b"")
    with pytest.raises(pins.PinError, match="output_incomplete_or_refused"):
        pins.check_output(out)


@pytest.mark.parametrize("name", ["result.json", "pin_receipt.json"])
def test_ok_check_output_rejects_symlinked_member(study, name):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    real = tmp_path / ("real_" + name)
    shutil.move(out / name, real)
    os.symlink(real, out / name)
    with pytest.raises(pins.PinError) as e:
        pins.check_output(out)
    assert e.value.failures == ["output_not_regular_file:" + name]


def test_ok_check_output_rejects_member_that_is_directory(study):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    (out / "result.json").unlink()
    (out / "result.json").mkdir()
    with pytest.raises(pins.PinError, match="output_not_regular_file:result.json"):
        pins.check_output(out)


def test_ok_check_output_rejects_receipt_edit(study):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    r = json.loads((out / "pin_receipt.json").read_bytes())
    r["files"]["data/excl.csv"] = "f" * 64
    (out / "pin_receipt.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    with pytest.raises(pins.PinError, match="output_link_mismatch"):
        pins.check_output(out)


@pytest.mark.parametrize("which,text", [("result.json", "[]"), ("result.json", "1"),
                                        ("pin_receipt.json", "[]"), ("pin_receipt.json", "null"),
                                        ("result.json", '{"pinned_inputs": [1]}')])
def test_ok_check_output_rejects_non_dict_json(study, which, text):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    (out / which).write_text(text)
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_ok_check_output_rejects_refused_marker(study):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    (out / "refused.json").write_text("{}")
    with pytest.raises(pins.PinError, match="output_incomplete_or_refused"):
        pins.check_output(out)


def test_obs_check_output_missing_dir_raises_raw_oserror(tmp_path):
    with pytest.raises(FileNotFoundError):
        pins.check_output(tmp_path / "nope")


def test_obs_check_output_deeply_nested_result_raises_raw_recursionerror(study):
    tmp_path, root, plan = study
    _, out = good_run(tmp_path, plan)
    (out / "result.json").write_text("[" * 200000 + "]" * 200000)
    with pytest.raises(RecursionError):
        pins.check_output(out)


# ---- compute vs out_dir --------------------------------------------------------------------

def test_obs_compute_precreated_refused_json_keeps_compute_content(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        (out / "refused.json").write_text('{"failures": ["all good"]}')
        return {"v": 1}

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert e.value.failures == ["unexpected_output_files:refused.json"]
    assert json.loads((out / "refused.json").read_text()) == {"failures": ["all good"]}
    assert not (out / "result.json").exists()
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def _receipt_attack(kind, out):
    rc = out / "pin_receipt.json"
    if kind == "delete_receipt":
        rc.unlink()
    elif kind == "edit_receipt":
        rc.write_text(rc.read_text().replace('"schema"', '"note": "edited by runner", "schema"', 1))
    elif kind == "receipt_becomes_dir":
        rc.unlink()
        rc.mkdir()
    elif kind == "recreate_out_dir":
        shutil.rmtree(out)
        out.mkdir()


ATTACKS = ["delete_receipt", "edit_receipt", "receipt_becomes_dir", "recreate_out_dir"]


@pytest.mark.parametrize("kind", ATTACKS)
def test_want_run_refuses_when_compute_removes_or_alters_receipt(study, kind):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        _receipt_attack(kind, out)
        return {"v": 1}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert not (out / "result.json").exists()


@pytest.mark.parametrize("kind", ATTACKS)
def test_obs_receipt_loss_run_succeeds_but_check_output_rejects(study, kind):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        _receipt_attack(kind, out)
        return {"v": 1}

    payload = pins.run_pinned(path, out, compute, plan_sha256=h)
    assert payload["v"] == 1 and (out / "result.json").is_file()
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_ok_compute_creating_subdirectory_is_refused(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        (out / "sub").mkdir()
        return {"v": 1}

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert e.value.failures == ["unexpected_output_files:sub"]
    assert json.loads((out / "refused.json").read_bytes())["failures"] == e.value.failures
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_obs_compute_deleting_out_dir_raises_raw_error_no_result(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        shutil.rmtree(out)
        return {"v": 1}

    with pytest.raises(FileNotFoundError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert not out.exists()


def test_obs_compute_swapping_out_dir_for_symlink_redirects_result(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    elsewhere = tmp_path / "elsewhere"

    def compute(p):
        out.rename(elsewhere)
        os.symlink(elsewhere, out)
        return {"v": 1}

    pins.run_pinned(path, out, compute, plan_sha256=h)
    assert (elsewhere / "result.json").is_file()
    assert pins.check_output(out)["v"] == 1  # listdir follows the symlinked out_dir


def test_want_deeply_nested_result_is_refused_with_refused_json(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        x = []
        for _ in range(200000):
            x = [x]
        return {"deep": x}

    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert (out / "refused.json").is_file()


def test_obs_deeply_nested_result_raises_raw_recursionerror_no_refusal(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        x = []
        for _ in range(200000):
            x = [x]
        return {"deep": x}

    with pytest.raises(RecursionError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert sorted(os.listdir(out)) == ["pin_receipt.json"]


def test_obs_compute_chdir_redirects_relative_out_dir(study, monkeypatch):
    tmp_path, root, plan = study
    work, other = tmp_path / "work", tmp_path / "other"
    work.mkdir()
    other.mkdir()
    save(work, plan)
    _, h = save(other, plan)            # identical plan bytes in the other directory
    (other / "out").mkdir()             # an empty 'out' there
    monkeypatch.chdir(work)

    def compute(p):
        os.chdir(other)
        return {"v": 1}

    pins.run_pinned("plan.json", "out", compute, plan_sha256=h)
    assert (other / "out/result.json").is_file()        # result written to a different directory
    assert sorted(os.listdir(work / "out")) == ["pin_receipt.json"]


def test_ok_keyboard_interrupt_in_compute_records_refusal(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert json.loads((out / "refused.json").read_bytes())["failures"] == ["compute_error:KeyboardInterrupt"]


def test_ok_compute_mutating_nested_copy_does_not_affect_guard(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        put(root, "data/candles/C-USD.json", b"[]")          # leave an unlisted file in the set
        p["input_sets"].clear()
        p["model"]["files"].clear()
        p["root"] = "/"
        return {"v": 1}

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert e.value.failures == ["unlisted_file:data/candles/C-USD.json"]


def test_obs_change_inside_set_reverted_before_end_is_undetected(study):
    tmp_path, root, plan = study

    def compute(p):
        f = root / "data/candles/Z.json"
        f.write_bytes(b"[]")
        f.unlink()
        return {"v": 1}

    payload, out = run(tmp_path, plan, compute)
    assert pins.check_output(out)["v"] == 1


def test_ok_compute_swapping_root_for_symlink_is_refused(study):
    tmp_path, root, plan = study
    clean = tmp_path / "clean"
    shutil.copytree(root, clean)

    def compute(p):
        (root / "data/excl.csv").write_bytes(b"T\n")
        root.rename(tmp_path / "moved")
        os.symlink(clean, root)
        return {"v": 1}

    path, h = save(tmp_path, plan)
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)
    assert e.value.failures == ["root_not_canonical"]


# ---- plan file -----------------------------------------------------------------------------

def test_ok_plan_symlink_repointed_to_different_content_is_refused(study):
    tmp_path, root, plan = study
    real, h = save(tmp_path, plan, name="plan_real.json")
    alt, _ = save(tmp_path, plan, text=json.dumps(plan) + " ", name="plan_alt.json")
    link = tmp_path / "plan_link.json"
    os.symlink(real, link)

    def compute(p):
        link.unlink()
        os.symlink(alt, link)
        return {"v": 1}

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(link, tmp_path / "out", compute, plan_sha256=h)
    assert e.value.failures == ["plan_changed_during_run"]


def test_obs_plan_replaced_by_identical_bytes_is_accepted(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)

    def compute(p):
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data)
        return {"v": 1}

    assert pins.run_pinned(path, tmp_path / "out", compute, plan_sha256=h)["v"] == 1


def test_ok_plan_value_1e400_is_refused(study):
    tmp_path, root, plan = study
    text = json.dumps(plan).replace('"python": "' + platform.python_version() + '"', '"python": 1e400')
    path, h = save(tmp_path, plan, text=text)
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, tmp_path / "out", lambda p: {"v": 1}, plan_sha256=h)
    assert e.value.failures == ["bad_runtime"]


def test_obs_deeply_nested_plan_raises_raw_recursionerror(study):
    tmp_path, root, plan = study
    text = json.dumps(plan)[:-1] + ', "x": ' + "[" * 200000 + "]" * 200000 + "}"
    path, h = save(tmp_path, plan, text=text)
    with pytest.raises(RecursionError):
        pins.run_pinned(path, tmp_path / "out", lambda p: {"v": 1}, plan_sha256=h)
    assert not (tmp_path / "out").exists()


def test_obs_lone_surrogate_path_raises_raw_unicodeerror_before_compute(study):
    tmp_path, root, plan = study
    plan["inputs"]["data/\ud800.csv"] = "0" * 64
    path, h = save(tmp_path, plan)
    called = []
    with pytest.raises(UnicodeEncodeError):
        pins.run_pinned(path, tmp_path / "out", lambda p: called.append(1) or {}, plan_sha256=h)
    assert not called and not (tmp_path / "out").exists()


def test_obs_nul_in_root_raises_raw_valueerror_before_compute(study):
    tmp_path, root, plan = study
    plan["root"] = str(root) + "\x00x"
    with pytest.raises(ValueError) as e:
        pins.verify(plan)
    assert not isinstance(e.value, pins.PinError)


# ---- root canonicality ---------------------------------------------------------------------

@pytest.mark.parametrize("form,accepted", [("{r}/", True), ("{p}//repo", True), ("{p}/./repo", True),
                                           ("{r}/.", True), ("/{r}", False), ("{r}/../repo", False)])
def test_ok_root_spelling(study, form, accepted):
    tmp_path, root, plan = study
    plan["root"] = form.format(r=str(root), p=str(root.parent))
    if accepted:
        assert pins.verify(plan)["files"]
    else:
        with pytest.raises(pins.PinError) as e:
            pins.verify(plan)
        assert e.value.failures == ["root_not_canonical"]


def test_ok_root_slash_with_relative_pins(study):
    tmp_path, root, plan = study
    rel = str(root).lstrip("/")
    plan["root"] = "/"
    plan["preregistration"]["path"] = rel + "/docs/prereg.md"
    plan["inputs"] = {rel + "/data/excl.csv": plan["inputs"]["data/excl.csv"]}
    plan["sources"] = {rel + "/scripts/run.py": plan["sources"]["scripts/run.py"]}
    plan["input_sets"][0].update(dir=rel + "/data/candles", sums=rel + "/data/candles/SHA256SUMS")
    plan["model"]["files"] = {rel + "/models/m.bin": plan["model"]["files"]["models/m.bin"]}
    assert len(pins.verify(plan)["files"]) == 7


# ---- inode / O_NOFOLLOW / fd leak ----------------------------------------------------------

@pytest.mark.parametrize("swap,reason", [("file", "replaced_while_opening"), ("symlink", "unreadable_or_replaced")])
def test_ok_swap_between_lstat_and_open_is_refused(study, monkeypatch, swap, reason):
    tmp_path, root, plan = study
    target = root / "data/excl.csv"
    real_open = os.open
    done = []

    def racing_open(path, flags, *a, **k):
        if str(path) == str(target) and not done:
            done.append(1)
            tmp = tmp_path / "swap"
            tmp.write_bytes(b"x\n")   # identical content, new inode
            if swap == "file":
                os.replace(tmp, target)
            else:
                target.unlink()
                os.symlink(tmp, target)
        return real_open(path, flags, *a, **k)

    monkeypatch.setattr(os, "open", racing_open)
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == [reason + ":data/excl.csv"]


def test_ok_no_fd_leak_on_failure_paths(study, monkeypatch):
    tmp_path, root, plan = study
    (root / "data/dirpin").mkdir()
    plan["inputs"]["data/dirpin"] = "0" * 64
    plan["inputs"]["data/missing"] = "0" * 64
    real_fstat = os.fstat

    def bad_fstat(fd):
        st = real_fstat(fd)
        raise OSError(5, "EIO")

    before = len(os.listdir("/proc/self/fd"))
    for _ in range(100):
        with pytest.raises(pins.PinError):
            pins.verify(plan)
    monkeypatch.setattr(os, "fstat", bad_fstat)
    for _ in range(100):
        with pytest.raises(pins.PinError):
            pins.verify(plan)
    monkeypatch.setattr(os, "fstat", real_fstat)
    assert len(os.listdir("/proc/self/fd")) == before


# ---- os.walk onerror with real permissions (root without DAC caps) ---------------------------

def _child_verify(plan):
    code = (f"import json\nfrom scripts.research import pinned_run_inputs as p\n"
            f"try:\n p.verify(json.loads({json.dumps(json.dumps(plan))})); print('ACCEPTED')\n"
            f"except p.PinError as e: print('REFUSED', json.dumps(e.failures))\n")
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(["setpriv", "--bounding-set", "-dac_override,-dac_read_search", "--inh-caps",
                        "-dac_override,-dac_read_search", sys.executable, "-c", code],
                       env=env, capture_output=True, text=True, timeout=20)
    return r.stdout + r.stderr


@pytest.mark.parametrize("mode,expect", [(0o000, "unreadable_directory:data/candles"),
                                         (0o100, "unreadable_directory:data/candles")])
def test_ok_unreadable_set_dir_itself_is_refused(study, mode, expect):
    tmp_path, root, plan = study
    shutil.move(root / "data/candles/SHA256SUMS", root / "data/CANDLES.SUMS")
    plan["input_sets"][0]["sums"] = "data/CANDLES.SUMS"
    os.chmod(root / "data/candles", mode)
    try:
        out = _child_verify(plan)
    finally:
        os.chmod(root / "data/candles", 0o755)
    assert out.startswith("REFUSED") and expect in out, out


def test_ok_listable_but_not_searchable_subdir_is_refused(study):
    tmp_path, root, plan = study
    put(root, "data/candles/sub/x.json", b"x")
    os.chmod(root / "data/candles/sub", 0o400)
    try:
        out = _child_verify(plan)
    finally:
        os.chmod(root / "data/candles/sub", 0o755)
    assert out.startswith("REFUSED"), out


# ---- set structure -------------------------------------------------------------------------

def _resum(root, plan, entries, sums="data/candles/SHA256SUMS"):
    plan["input_sets"][0]["sums"] = sums
    plan["input_sets"][0]["sums_sha256"] = put(root, sums, sums_bytes(entries))


def test_ok_nested_listed_file_with_empty_sibling_dir_is_refused(study):
    tmp_path, root, plan = study
    c = put(root, "data/candles/a/b/c.json", b"c")
    (root / "data/candles/a/x").mkdir()
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("a/b/c.json", c)])
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["unlisted_directory:data/candles/a/x"]
    (root / "data/candles/a/x").rmdir()
    assert "data/candles/a/b/c.json" in pins.verify(plan)["files"]


def test_ok_sums_file_in_subdirectory_of_set(study):
    tmp_path, root, plan = study
    (root / "data/candles/SHA256SUMS").unlink()
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B))], sums="data/candles/meta/SHA256SUMS")
    assert len(pins.verify(plan)["files"]) == 7
    put(root, "data/candles/meta/extra", b"e")
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["unlisted_file:data/candles/meta/extra"]


def test_ok_sums_outside_set_and_stray_sums_name_inside(study):
    tmp_path, root, plan = study
    (root / "data/candles/SHA256SUMS").unlink()
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B))], sums="data/CANDLES.SUMS")
    assert len(pins.verify(plan)["files"]) == 7
    put(root, "data/candles/SHA256SUMS", b"anything")
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["unlisted_file:data/candles/SHA256SUMS"]


def test_ok_symlinked_set_dir_with_outside_sums_is_refused(study):
    tmp_path, root, plan = study
    shutil.move(root / "data/candles/SHA256SUMS", root / "data/CANDLES.SUMS")
    plan["input_sets"][0]["sums"] = "data/CANDLES.SUMS"
    shutil.move(root / "data/candles", tmp_path / "outside_candles")
    os.symlink(tmp_path / "outside_candles", root / "data/candles")
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert any(f.startswith("symlink_refused:data/candles") for f in e.value.failures), e.value.failures


def test_ok_listed_member_that_is_a_directory_is_refused(study):
    tmp_path, root, plan = study
    (root / "data/candles/D").mkdir()
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("D", "0" * 64)])
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert "not_a_regular_file:data/candles/D" in e.value.failures


def test_obs_case_distinct_names_on_case_sensitive_fs_are_refused(study):
    tmp_path, root, plan = study
    a2 = put(root, "data/candles/a-usd.json", b"different")
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("a-usd.json", a2)])
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["case_duplicate_sums_entry:a-usd.json", "set_members_not_checked:data/candles"]


def test_obs_sharp_s_and_ss_treated_as_case_duplicates(study):
    tmp_path, root, plan = study
    x, y = put(root, "data/candles/straße", b"1"), put(root, "data/candles/strasse", b"2")
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("straße", x), ("strasse", y)])
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures[0] == "case_duplicate_sums_entry:strasse"


def test_obs_nfc_nfd_spellings_not_detected_as_duplicates(study):
    tmp_path, root, plan = study
    nfc, nfd = unicodedata.normalize("NFC", "café"), unicodedata.normalize("NFD", "café")
    assert nfc != nfd and nfc.casefold() != nfd.casefold()
    h = put(root, "data/candles/" + nfc, b"same")
    put(root, "data/candles/" + nfd, b"same")   # distinct file on Linux; same file on APFS/HFS+
    _resum(root, plan, [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), (nfc, h), (nfd, h)])
    assert len(pins.verify(plan)["files"]) == 9   # accepted: both spellings listed


def test_ok_non_utf8_unlisted_name_is_refused_and_reportable(study):
    tmp_path, root, plan = study
    with open(os.path.join(os.fsencode(root), b"data/candles/\xff.json"), "wb") as f:
        f.write(b"x")
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["unlisted_file:data/candles/\udcff.json"]
    assert pins._encode({"f": e.value.failures})


def test_obs_two_sets_same_dir_refuse_each_other(study):
    tmp_path, root, plan = study
    s2 = put(root, "data/candles/SUMS2", sums_bytes([("A-USD.json", sha(A)), ("B-USD.json", sha(B))]))
    plan["input_sets"].append({"dir": "data/candles", "sums": "data/candles/SUMS2", "sums_sha256": s2})
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert e.value.failures == ["unlisted_file:data/candles/SUMS2", "unlisted_file:data/candles/SHA256SUMS"]


# ---- out_dir placement ---------------------------------------------------------------------

def test_ok_out_dir_via_symlink_into_pinned_set_refused_before_compute(study):
    tmp_path, root, plan = study
    os.symlink(root / "data/candles", tmp_path / "alias")
    path, h = save(tmp_path, plan)
    called = []
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, tmp_path / "alias/out", lambda p: called.append(1) or {}, plan_sha256=h)
    assert e.value.failures == ["out_dir_inside_pinned_set:data/candles"]
    assert not called and not (root / "data/candles/out").exists()


def test_ok_out_dir_via_dotdot_into_pinned_set_refused(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    with pytest.raises(pins.PinError, match="out_dir_inside_pinned_set"):
        pins.run_pinned(path, root / "data/nothere/../candles/new/out", lambda p: {}, plan_sha256=h)
    assert not (root / "data/candles/new").exists()


def test_ok_out_dir_relative_into_pinned_set_refused(study, monkeypatch):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    monkeypatch.chdir(root / "data")
    with pytest.raises(pins.PinError, match="out_dir_inside_pinned_set"):
        pins.run_pinned(path, "candles/out", lambda p: {}, plan_sha256=h)


def test_ok_out_dir_equal_to_root_or_set_is_never_used(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    with pytest.raises(FileExistsError):
        pins.run_pinned(path, root, lambda p: {}, plan_sha256=h)
    with pytest.raises(pins.PinError, match="out_dir_inside_pinned_set"):
        pins.run_pinned(path, root / "data/candles", lambda p: {}, plan_sha256=h)


def test_obs_out_dir_via_bind_mount_of_set_runs_compute_then_refuses(study):
    tmp_path, root, plan = study
    mnt = tmp_path / "mnt"
    mnt.mkdir()
    if subprocess.run(["mount", "--bind", str(root / "data/candles"), str(mnt)]).returncode:
        pytest.skip("bind mount unavailable")
    try:
        path, h = save(tmp_path, plan)
        called = []
        with pytest.raises(pins.PinError) as e:
            pins.run_pinned(path, mnt / "out", lambda p: called.append(1) or {"v": 1}, plan_sha256=h)
        assert called == [1]
        assert "unlisted_directory:data/candles/out" in e.value.failures
        assert not (mnt / "out/result.json").exists()
    finally:
        subprocess.run(["umount", str(mnt)])


# ---- failures ordering / duplication -------------------------------------------------------

def test_ok_post_run_failures_ordered_and_recorded(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        path.write_text(json.dumps(plan) + " ")
        (root / "data/excl.csv").write_bytes(b"T\n")
        (out / "x").write_text("x")
        return [1]

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert e.value.failures == ["plan_changed_during_run", "hash_mismatch:data/excl.csv",
                                "unexpected_output_files:x", "compute_must_return_dict"]
    assert json.loads((out / "refused.json").read_bytes())["failures"] == e.value.failures


def test_ok_v1_and_v2_receipts_agree_on_valid_plan(study):
    import importlib.util
    tmp_path, root, plan = study
    spec = importlib.util.spec_from_file_location(
        "pins_v1", "/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/"
                   "c4v2_review_input/context/v1/pinned_run_inputs_v1.py")
    v1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v1)
    assert v1.verify(plan) == pins.verify(plan)


# ---- F13 fsync ------------------------------------------------------------------------------

def test_obs_out_dir_parent_not_fsynced_after_mkdir(study, monkeypatch):
    tmp_path, root, plan = study
    synced = []
    real = os.fsync

    def rec(fd):
        synced.append(os.readlink(f"/proc/self/fd/{fd}"))
        return real(fd)

    monkeypatch.setattr(os, "fsync", rec)
    _, out = run(tmp_path, plan, lambda p: {"v": 1}, out=tmp_path / "a/b/out")
    assert str(out) in synced and str(out / "result.json") in synced
    assert str(out.parent) not in synced and str(tmp_path) not in synced


# ---- design choice (b): compute-written result.json left in place ----------------------------

def test_obs_linked_compute_result_plus_failed_refusal_write_passes_check_output(study, monkeypatch):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    real_write_new = pins._write_new

    def no_space_for_refusal(p, data):
        if p.name == pins.REFUSED_NAME:
            raise OSError(28, "No space left on device")
        return real_write_new(p, data)

    monkeypatch.setattr(pins, "_write_new", no_space_for_refusal)

    def compute(p):
        (root / "data/excl.csv").write_bytes(b"TAMPERED\n")
        rb = (out / "pin_receipt.json").read_bytes()
        link = {"plan_sha256": json.loads(rb)["plan_sha256"], "receipt_sha256": sha(rb)}
        (out / "result.json").write_text(json.dumps({"v": 666, "pinned_inputs": link}))
        return {"v": 1}

    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert "hash_mismatch:data/excl.csv" in e.value.failures
    assert pins.check_output(out)["v"] == 666   # refused run accepted by check_output


def test_ok_nested_duplicate_keys_refused(study):
    tmp_path, root, plan = study
    text = json.dumps(plan).replace('"inputs": {', '"inputs": {"data/excl.csv": "' + "0" * 64 + '", ', 1)
    path, h = save(tmp_path, plan, text=text)
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, tmp_path / "out", lambda p: {}, plan_sha256=h)
    assert e.value.failures == ["duplicate_json_key:data/excl.csv"]


def test_obs_parent_swapped_to_symlink_after_parent_check_is_followed(study, monkeypatch):
    # race simulated: parent 'data' becomes a symlink after _no_symlink_parents ran, before lstat/open
    tmp_path, root, plan = study
    outside = tmp_path / "outside_data"
    shutil.copytree(root / "data", outside)          # identical content outside root
    target = str(root / "data/excl.csv")
    real_lstat = os.lstat
    done = []

    def racing_lstat(p, *a, **k):
        if str(p) == target and not done:
            done.append(1)
            (root / "data").rename(tmp_path / "data_moved")
            os.symlink(outside, root / "data")
        return real_lstat(p, *a, **k)

    monkeypatch.setattr(os, "lstat", racing_lstat)
    plan = dict(plan, input_sets=[])                  # isolate the single input
    receipt = pins.verify(plan)
    assert done and receipt["files"]["data/excl.csv"] == plan["inputs"]["data/excl.csv"]
