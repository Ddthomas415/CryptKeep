"""Third (GATE) reviewer probes for pinned_run_inputs v3.

want_*: behaviour this reviewer considers required (a failure is a finding).
obs_*:  record actual v3 behaviour as evidence (passing = the observation holds; not necessarily a defect).
"""
import errno
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import unicodedata

import pytest

from scripts.research import pinned_run_inputs as pins

REPO = Path(pins.__file__).resolve().parents[2]
V2 = Path("/tmp/claude-0/-home-claude/81d74672-3e95-58a2-a3c6-4138159ec2a3/scratchpad/"
          "c4v3_review_input/context/v2/pinned_run_inputs_v2.py")
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


def save(tmp_path, plan, name="plan.json"):
    p = tmp_path / name
    p.write_text(json.dumps(plan))
    return p, sha(p.read_bytes())


def nfds():
    return len(os.listdir("/proc/self/fd"))


def never(p):
    raise AssertionError("compute must not run")


def child(code, timeout=60, drop=True):
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-c", code]
    if drop:
        cmd = ["setpriv", "--bounding-set", "-dac_override,-dac_read_search", "--inh-caps",
               "-dac_override,-dac_read_search"] + cmd
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    return r.stdout + r.stderr


VERIFY_CHILD = ("import json, importlib.util\n"
                "from scripts.research import pinned_run_inputs as p\n"
                "mod = p\n"
                "if {v2!r}:\n"
                "    s = importlib.util.spec_from_file_location('v2', {v2path!r}); mod = importlib.util.module_from_spec(s)\n"
                "    s.loader.exec_module(mod)\n"
                "try:\n    mod.verify(json.loads({plan!r})); print('ACCEPTED')\n"
                "except mod.PinError as e: print('REFUSED', json.dumps(e.failures))\n"
                "except Exception as e: print('RAW', type(e).__name__, e)\n")


def verify_unprivileged(plan, v2=False):
    return child(VERIFY_CHILD.format(v2=v2, v2path=str(V2), plan=json.dumps(plan)))


# ---- 1. fd leaks on every error path of the dir_fd chain ------------------------------------

def _hook_open(monkeypatch, name, err):
    real = os.open

    def hooked(path, flags, *a, dir_fd=None, **k):
        if path == name and dir_fd is not None:
            raise OSError(err, os.strerror(err), name)
        return real(path, flags, *a, dir_fd=dir_fd, **k)
    monkeypatch.setattr(os, "open", hooked)


CHAIN_CASES = {
    "child_dir_ELOOP": (lambda mp, r, t: _hook_open(mp, "data", errno.ELOOP), "symlink_or_replaced:data/excl.csv"),
    "child_dir_ENOTDIR": (lambda mp, r, t: _hook_open(mp, "data", errno.ENOTDIR), "symlink_or_replaced:data/excl.csv"),
    "child_dir_EACCES": (lambda mp, r, t: _hook_open(mp, "data", errno.EACCES), "unreadable:data/excl.csv"),
    "child_dir_EMFILE": (lambda mp, r, t: _hook_open(mp, "data", errno.EMFILE), "unreadable:data/excl.csv"),
    "file_EACCES": (lambda mp, r, t: _hook_open(mp, "excl.csv", errno.EACCES), "unreadable_or_replaced:data/excl.csv"),
    "parent_is_file": (lambda mp, r, t: None, "not_a_directory:data/excl.csv/x"),
    "parent_missing": (lambda mp, r, t: None, "missing:nope/x"),
    "parent_symlink": (lambda mp, r, t: None, "symlink_refused:lnk/excl.csv"),
}


@pytest.mark.parametrize("case", sorted(CHAIN_CASES))
def test_want_chain_error_paths_report_reason_and_leak_no_fd(study, monkeypatch, case):
    tmp_path, root, plan = study
    plan["input_sets"] = []
    os.symlink(root / "data", root / "lnk")
    plan["inputs"].update({"data/excl.csv/x": "0" * 64, "nope/x": "0" * 64, "lnk/excl.csv": "0" * 64})
    hook, reason = CHAIN_CASES[case]
    hook(monkeypatch, root, tmp_path)
    before = nfds()
    for _ in range(30):
        with pytest.raises(pins.PinError) as e:
            pins.verify(plan)
        assert reason in e.value.failures, e.value.failures
    assert nfds() == before


def test_want_read_error_while_hashing_reported_and_no_fd_leak(study, monkeypatch):
    tmp_path, root, plan = study
    real = os.read

    def bad_read(fd, n):
        if os.readlink(f"/proc/self/fd/{fd}").endswith("excl.csv"):
            raise OSError(errno.EIO, "EIO")
        return real(fd, n)
    monkeypatch.setattr(os, "read", bad_read)
    before = nfds()
    for _ in range(30):
        with pytest.raises(pins.PinError) as e:
            pins.verify(plan)
        assert e.value.failures == ["unreadable:data/excl.csv"]
    assert nfds() == before


def test_want_identity_mismatch_in_chain_and_root(study, monkeypatch):
    tmp_path, root, plan = study
    plan["input_sets"] = []
    real_stat = os.stat
    other = real_stat(tmp_path)

    def lying_stat(p, *a, dir_fd=None, follow_symlinks=True):
        if p == "data" and dir_fd is not None:
            return other   # stat says one directory, open yields another
        return real_stat(p, *a, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
    monkeypatch.setattr(os, "stat", lying_stat)
    before = nfds()
    for _ in range(30):
        with pytest.raises(pins.PinError) as e:
            pins.verify(plan)
        assert "replaced_while_opening:data/excl.csv" in e.value.failures
    assert nfds() == before


def test_want_root_swapped_for_identical_copy_after_canonical_check(study, monkeypatch):
    tmp_path, root, plan = study
    real_open = os.open
    done = []

    def racing(path, flags, *a, dir_fd=None, **k):
        if dir_fd is None and str(path) == str(root) and not done:
            done.append(1)
            os.rename(root, tmp_path / "root_old")
            shutil.copytree(tmp_path / "root_old", root)
        return real_open(path, flags, *a, dir_fd=dir_fd, **k)
    monkeypatch.setattr(os, "open", racing)
    before = nfds()
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert done and set(e.value.failures) == {"root_replaced", "set_members_not_checked:data/candles"}, e.value.failures
    assert nfds() == before


def test_want_root_swapped_for_symlink_to_copy_after_canonical_check(study, monkeypatch):
    tmp_path, root, plan = study
    real_open = os.open
    done = []

    def racing(path, flags, *a, dir_fd=None, **k):
        if dir_fd is None and str(path) == str(root) and not done:
            done.append(1)
            os.rename(root, tmp_path / "root_old")
            shutil.copytree(tmp_path / "root_old", tmp_path / "root_copy")
            os.symlink(tmp_path / "root_copy", root)
        return real_open(path, flags, *a, dir_fd=dir_fd, **k)
    monkeypatch.setattr(os, "open", racing)
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert done and "root_replaced" in e.value.failures


@pytest.mark.parametrize("swap,reason", [("symlink", "symlink_or_replaced:data/excl.csv"),
                                         ("regular_file", "symlink_or_replaced:data/excl.csv"),
                                         ("other_dir", "replaced_while_opening:data/excl.csv")])
def test_want_real_swap_of_intermediate_dir_between_stat_and_open(study, monkeypatch, swap, reason):
    tmp_path, root, plan = study
    plan["input_sets"] = []
    real_stat = os.stat
    done = []

    def racing(p, *a, dir_fd=None, follow_symlinks=True):
        st = real_stat(p, *a, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        if p == "data" and dir_fd is not None and not done:
            done.append(1)
            os.rename(root / "data", tmp_path / "data_real")
            if swap == "symlink":
                shutil.copytree(tmp_path / "data_real", tmp_path / "data_copy")
                os.symlink(tmp_path / "data_copy", root / "data")
            elif swap == "regular_file":
                (root / "data").write_bytes(b"x")
            else:
                shutil.copytree(tmp_path / "data_real", root / "data")
        return st
    monkeypatch.setattr(os, "stat", racing)
    before = nfds()
    with pytest.raises(pins.PinError) as e:
        pins.verify(plan)
    assert done and e.value.failures == [reason]
    assert nfds() == before


# ---- 2. fd leaks across run_pinned / check_output paths ------------------------------------

def test_want_no_fd_leak_across_run_and_check_paths(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    before = nfds()
    for i in range(10):
        out = tmp_path / f"ok{i}"
        pins.run_pinned(path, out, lambda p: {"v": 1}, plan_sha256=h)
        pins.check_output(out, expected_plan_sha256=h)
        with pytest.raises(RuntimeError):
            pins.run_pinned(path, tmp_path / f"err{i}", lambda p: (_ for _ in ()).throw(RuntimeError()),
                            plan_sha256=h)
        with pytest.raises(pins.PinError):
            pins.check_output(tmp_path / f"err{i}")

        def tamper(p):
            (root / "data/excl.csv").write_bytes(b"T\n")
            return {"v": 1}
        with pytest.raises(pins.PinError):
            pins.run_pinned(path, tmp_path / f"tam{i}", tamper, plan_sha256=h)
        (root / "data/excl.csv").write_bytes(b"x\n")
        with pytest.raises(pins.PinError):
            pins.run_pinned(path, tmp_path / f"x{i}", never, plan_sha256="0" * 64)
        with pytest.raises(FileExistsError):
            pins.run_pinned(path, out, never, plan_sha256=h)
        with pytest.raises(pins.PinError):
            pins.run_pinned(path, root / "data/candles/o", never, plan_sha256=h)
        with pytest.raises(pins.PinError):
            pins.check_output(tmp_path / "absent")
    assert nfds() == before


# ---- 3. unreadable paths with real permissions (root without DAC capabilities) -------------

def test_want_unreadable_intermediate_dir_refused(study):
    tmp_path, root, plan = study
    os.chmod(root / "data", 0o000)
    try:
        out = verify_unprivileged(plan)
    finally:
        os.chmod(root / "data", 0o755)
    assert out.startswith("REFUSED") and "unreadable:data/excl.csv" in out, out


def test_want_unreadable_pinned_file_refused(study):
    tmp_path, root, plan = study
    os.chmod(root / "data/excl.csv", 0o000)
    try:
        out = verify_unprivileged(plan)
    finally:
        os.chmod(root / "data/excl.csv", 0o644)
    assert out.startswith("REFUSED") and "unreadable_or_replaced:data/excl.csv" in out, out


def test_want_unreadable_listed_subdir_of_set_refused(study):
    tmp_path, root, plan = study
    c = put(root, "data/candles/sub/C.json", b"c")
    plan["input_sets"][0]["sums_sha256"] = put(root, "data/candles/SHA256SUMS", sums_bytes(
        [("A-USD.json", sha(A)), ("B-USD.json", sha(B)), ("sub/C.json", c)]))
    put(root, "data/candles/sub/hidden_extra.json", b"e")
    os.chmod(root / "data/candles/sub", 0o000)
    try:
        out = verify_unprivileged(plan)
    finally:
        os.chmod(root / "data/candles/sub", 0o755)
    assert out.startswith("REFUSED") and "unreadable_directory:data/candles/sub" in out, out


def test_obs_search_only_intermediate_dir_refused_by_v3_accepted_by_v2(study):
    # owner has x but not r on data/: path-based access works, O_RDONLY directory open does not
    tmp_path, root, plan = study
    plan["input_sets"] = []
    os.chmod(root / "data", 0o100)
    try:
        v3 = verify_unprivileged(plan)
        v2 = verify_unprivileged(plan, v2=True)
    finally:
        os.chmod(root / "data", 0o755)
    assert v3.startswith("REFUSED") and "unreadable:data/excl.csv" in v3, v3
    assert v2.startswith("ACCEPTED"), v2


RUN_CHILD = ("import json, os, shutil\nfrom pathlib import Path\n"
             "from scripts.research import pinned_run_inputs as p\n"
             "root, out = Path({root!r}), Path({out!r})\n"
             "def compute(plan):\n{body}\n    return {{'v': 1}}\n"
             "try:\n    p.run_pinned({path!r}, out, compute, plan_sha256={h!r}); print('ACCEPTED')\n"
             "except p.PinError as e: print('REFUSED', json.dumps(e.failures))\n"
             "except Exception as e: print('RAW', type(e).__name__, e)\n"
             "try:\n    p.check_output(out); print('CHECK_OK')\n"
             "except p.PinError as e: print('CHECK_REJECT', json.dumps(e.failures))\n"
             "except Exception as e: print('CHECK_RAW', type(e).__name__)\n")


def run_unprivileged(tmp_path, plan, body, out=None):
    path, h = save(tmp_path, plan)
    out = out or tmp_path / "out"
    return child(RUN_CHILD.format(root=plan["root"], out=str(out), path=str(path), h=h, body=body)), out


def test_want_root_made_unreadable_during_compute_refuses(study):
    tmp_path, root, plan = study
    try:
        res, out = run_unprivileged(tmp_path, plan, "    os.chmod(root, 0o000)")
    finally:
        os.chmod(root, 0o755)
    assert "REFUSED" in res and "unreadable:docs/prereg.md" in res and "CHECK_REJECT" in res, res
    assert not (out / "result.json").exists()
    assert json.loads((out / "refused.json").read_bytes())["failures"]


def test_want_root_moved_away_during_compute_refuses(study):
    tmp_path, root, plan = study
    res, out = run_unprivileged(tmp_path, plan, f"    os.rename(root, {str(tmp_path / 'gone')!r})")
    assert "REFUSED" in res and "missing_root" in res and "CHECK_REJECT" in res, res
    assert not (out / "result.json").exists()


# ---- 4. check_output vs what run_pinned really produces ------------------------------------

REAL_VARIANTS = {
    "no_model": lambda p: p.pop("model"),
    "no_runtime": lambda p: p.pop("runtime"),
    "no_sets": lambda p: p.update(input_sets=[]),
    "only_python_runtime": lambda p: p["runtime"].pop("packages"),
}


@pytest.mark.parametrize("variant", sorted(REAL_VARIANTS))
@pytest.mark.parametrize("result", [{}, {"s": "\udcff café  "}, {"pinned_inputs": "compute's own"},
                                    {"rows": [[1, 2.5, None, True]] * 50}])
def test_want_every_real_run_passes_check_output(study, variant, result):
    tmp_path, root, plan = study
    REAL_VARIANTS[variant](plan)
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    payload = pins.run_pinned(path, out, lambda p: result, plan_sha256=h)
    assert pins.check_output(out, expected_plan_sha256=h) == payload
    assert sorted(os.listdir(out)) == ["pin_receipt.json", "result.json"]


def test_obs_check_output_accepts_receipt_timestamp_run_pinned_never_writes(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    pins.run_pinned(path, out, lambda p: {"v": 1}, plan_sha256=h)
    receipt = json.loads((out / "pin_receipt.json").read_bytes())
    receipt["verified_utc"] = "2026-10-19"          # naive, date-only
    rb = json.dumps(receipt).encode()
    (out / "pin_receipt.json").write_bytes(rb)
    result = json.loads((out / "result.json").read_bytes())
    result["pinned_inputs"]["receipt_sha256"] = sha(rb)
    result["v"] = 999
    (out / "result.json").write_text(json.dumps(result))
    assert pins.check_output(out, expected_plan_sha256=h)["v"] == 999


DEEP_CHILD = ("import sys, json\nsys.setrecursionlimit(60000)\n"
              "from scripts.research import pinned_run_inputs as p\n"
              "x = []\nfor _ in range({n}):\n    x = [x]\n"
              "try:\n    p.run_pinned({path!r}, {out!r}, lambda plan: {{'deep': x}}, plan_sha256={h!r}); print('RUN_OK')\n"
              "except Exception as e: print('RUN', type(e).__name__, e)\n")


def test_obs_deep_result_written_under_raised_recursion_limit(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    res = child(DEEP_CHILD.format(n=20000, path=str(path), out=str(out), h=h), drop=False)
    check = child(f"from scripts.research import pinned_run_inputs as p\n"
                  f"try:\n    p.check_output({str(out)!r}); print('CHECK_OK')\n"
                  f"except Exception as e: print('CHECK', type(e).__name__, e)\n", drop=False)
    print(res, check)
    if sys.version_info[:2] == (3, 12):   # guard writes it; a default-limit consumer cannot load it
        assert "RUN_OK" in res, res
        assert "CHECK PinError" in check and "bad_json:result.json" in check, check
    else:                                 # 3.13: the guard's encoder refuses it
        assert "RUN PinError" in res and "result_not_encodable" in res, res


# ---- 5. _refuse / _set_aside ---------------------------------------------------------------

def _forged(out, h):
    rb = (out / "pin_receipt.json").read_bytes()
    return json.dumps({"v": 666, "pinned_inputs": {"plan_sha256": h, "receipt_sha256": sha(rb)}})


def test_want_set_aside_picks_free_name_and_keeps_existing(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        (out / "result.json.unguarded").write_text("older")
        (out / "result.json").write_text(_forged(out, h))
        return {"v": 1}
    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert sorted(os.listdir(out)) == ["pin_receipt.json", "refused.json", "result.json.unguarded",
                                       "result.json.unguarded.1"]
    assert (out / "result.json.unguarded").read_text() == "older"
    assert '"v": 666' in (out / "result.json.unguarded.1").read_text()
    with pytest.raises(pins.PinError):
        pins.check_output(out)


@pytest.mark.parametrize("kind", ["refused_dir", "result_dir", "result_symlink", "refused_symlink"])
def test_want_odd_compute_entries_set_aside_without_touching_targets(study, kind):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    outside = tmp_path / "outside.txt"
    outside.write_text("untouched")

    def compute(p):
        name = "refused.json" if kind.startswith("refused") else "result.json"
        if kind.endswith("dir"):
            (out / name).mkdir()
            (out / name / "inner").write_text("x")
        else:
            os.symlink(outside, out / name)
        return {"v": 1}
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert outside.read_text() == "untouched"
    assert (out / "refused.json").is_file() and not (out / "refused.json").is_symlink()
    assert json.loads((out / "refused.json").read_bytes())["failures"] == e.value.failures
    assert not os.path.lexists(out / "result.json")
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def test_want_no_free_set_aside_name_still_rejected_by_check_output(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        (out / "result.json.unguarded").write_text("x")
        for i in range(1, 100):
            (out / f"result.json.unguarded.{i}").write_text("x")
        (out / "result.json").write_text(_forged(out, h))
        return {"v": 1}
    with pytest.raises(pins.PinError):
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert (out / "result.json").exists() and (out / "refused.json").is_file()
    with pytest.raises(pins.PinError, match="output_incomplete_or_refused"):
        pins.check_output(out)


def test_obs_forged_result_survives_when_compute_makes_out_unwritable(study):
    # deliberate subversion (outside the stated trust boundary): rename and refusal write both fail
    tmp_path, root, plan = study
    body = ("    rb = (out / 'pin_receipt.json').read_bytes()\n"
            "    import hashlib\n"
            "    link = {'plan_sha256': json.loads(rb)['plan_sha256'], 'receipt_sha256': hashlib.sha256(rb).hexdigest()}\n"
            "    (out / 'result.json').write_text(json.dumps({'v': 666, 'pinned_inputs': link}))\n"
            "    (root / 'data/excl.csv').write_bytes(b'TAMPERED')\n"
            "    os.chmod(out, 0o500)")
    res, out = run_unprivileged(tmp_path, plan, body)
    os.chmod(out, 0o755)
    assert "REFUSED" in res and "hash_mismatch:data/excl.csv" in res, res
    assert sorted(os.listdir(out)) == ["pin_receipt.json", "result.json"]
    assert "CHECK_OK" in res, res


def test_want_accidental_result_with_unwritable_out_rejected(study):
    tmp_path, root, plan = study
    body = ("    (out / 'result.json').write_text(json.dumps({'v': 1}))\n"
            "    os.chmod(out, 0o500)")
    res, out = run_unprivileged(tmp_path, plan, body)
    os.chmod(out, 0o755)
    assert "REFUSED" in res and "CHECK_REJECT" in res, res


# ---- 6. out_dir identity and moves ----------------------------------------------------------

def test_want_recreated_out_dir_gets_new_inode_and_is_refused(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    seen = {}

    def compute(p):
        seen["old"] = os.stat(out).st_ino
        for _ in range(50):          # give the allocator many chances to reuse the number
            shutil.rmtree(out)
            out.mkdir()
            if os.stat(out).st_ino == seen["old"]:
                break
        seen["new"] = os.stat(out).st_ino
        shutil.copy(tmp_path / "plan.json", out / "pin_receipt.json")
        return {"v": 1}
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert seen["old"] != seen["new"]
    assert "out_dir_replaced_during_run" in e.value.failures
    assert not (out / "result.json").exists()


def test_want_out_dir_moved_away_and_back_is_accepted(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        os.rename(out, tmp_path / "parked")
        os.rename(tmp_path / "parked", out)
        return {"v": 5}
    assert pins.run_pinned(path, out, compute, plan_sha256=h)["v"] == 5
    assert pins.check_output(out, expected_plan_sha256=h)["v"] == 5


def test_want_out_dir_moved_away_refusal_goes_to_moved_dir_only(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        os.rename(out, tmp_path / "moved")
        return {"v": 1}
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert e.value.failures == ["out_dir_replaced_during_run"]
    assert not os.path.lexists(out)
    assert sorted(os.listdir(tmp_path / "moved")) == ["pin_receipt.json", "refused.json"]


def test_want_out_dir_moved_into_pinned_set_refused(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        os.rename(out, root / "data/candles/out")
        return {"v": 1}
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    assert "out_dir_replaced_during_run" in e.value.failures
    assert "unlisted_directory:data/candles/out" in e.value.failures
    assert not (root / "data/candles/out/result.json").exists()


def test_obs_receipt_replaced_by_identical_bytes_new_inode_accepted(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        data = (out / "pin_receipt.json").read_bytes()
        (out / "pin_receipt.json").unlink()
        (out / "pin_receipt.json").write_bytes(data)
        return {"v": 1}
    assert pins.run_pinned(path, out, compute, plan_sha256=h)["v"] == 1


# ---- 7. _make_out ---------------------------------------------------------------------------

def test_want_dangling_symlink_out_never_written_through(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    os.symlink(tmp_path / "target", tmp_path / "out")
    with pytest.raises(FileExistsError):
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=h)
    assert not os.path.lexists(tmp_path / "target")


def test_want_dangling_symlink_parent_creates_nothing(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    os.symlink(tmp_path / "nowhere/deeper", tmp_path / "par")
    with pytest.raises(OSError):
        pins.run_pinned(path, tmp_path / "par/out", never, plan_sha256=h)
    assert not os.path.lexists(tmp_path / "nowhere")


def test_want_parent_is_regular_file(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    (tmp_path / "f").write_text("x")
    with pytest.raises(OSError):
        pins.run_pinned(path, tmp_path / "f/out", never, plan_sha256=h)


def test_obs_raw_exceptions_for_odd_arguments(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    with pytest.raises(ValueError) as e:
        pins.run_pinned(path, str(tmp_path / "o\x00ut"), never, plan_sha256=h)
    assert not isinstance(e.value, pins.PinError)
    with pytest.raises(ValueError) as e:
        pins.run_pinned(str(path) + "\x00", tmp_path / "out2", never, plan_sha256=h)
    assert not isinstance(e.value, pins.PinError)
    with pytest.raises(TypeError):
        pins.check_output(None)
    assert not (tmp_path / "out2").exists()


def test_obs_plan_path_fifo_blocks_run_pinned(study):
    tmp_path, root, plan = study
    os.mkfifo(tmp_path / "plan.fifo")
    res = child(f"from scripts.research import pinned_run_inputs as p\n"
                f"p.run_pinned({str(tmp_path / 'plan.fifo')!r}, {str(tmp_path / 'o')!r}, lambda x: {{}}, "
                f"plan_sha256='0'*64)\n", timeout=5, drop=False)
    assert res == "TIMEOUT"


# ---- 8. out inside sets: nested sets, root-level out ---------------------------------------

def _nested_sets(root, plan):
    inner_sums = plan["input_sets"][0]["sums_sha256"]
    plan["input_sets"].append({"dir": "data", "sums": "SUMS_DATA", "sums_sha256": put(root, "SUMS_DATA", sums_bytes(
        [("candles/A-USD.json", sha(A)), ("candles/B-USD.json", sha(B)),
         ("candles/SHA256SUMS", inner_sums), ("excl.csv", sha(b"x\n"))]))})


def test_want_nested_sets_verify_and_refuse_out_in_either(study):
    tmp_path, root, plan = study
    _nested_sets(root, plan)
    assert len(pins.verify(plan)["files"]) == 8   # 7 base files + SUMS_DATA
    path, h = save(tmp_path, plan)
    for out in (root / "data/new/out", root / "data/candles/new/out"):
        with pytest.raises(pins.PinError, match="out_dir_inside_pinned_set"):
            pins.run_pinned(path, out, never, plan_sha256=h)
        assert not (root / "data/new").exists() and not (root / "data/candles/new").exists()


def test_want_out_inside_root_but_outside_sets_is_fine(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = root / "results/run1"
    pins.run_pinned(path, out, lambda p: {"v": 2}, plan_sha256=h)
    assert pins.check_output(out, expected_plan_sha256=h)["v"] == 2
    assert pins.verify(plan)


# ---- 9. NFC + casefold collision key --------------------------------------------------------

def test_obs_collision_key_vs_canonical_caseless_match():
    def canon(s):
        return unicodedata.normalize("NFD", unicodedata.normalize("NFD", s).casefold())
    missed = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        a = chr(cp)
        b = canon(a)
        if a != b and canon(b) == canon(a) and pins._collision_key(a) != pins._collision_key(b):
            missed.append(cp)
    print("missed", len(missed), [hex(c) for c in missed[:12]])
    assert isinstance(missed, list)


# ---- 10. deep structures --------------------------------------------------------------------

@pytest.mark.parametrize("depth", [500, 900, 990, 1100, 1500, 3000, 10000, 50000])
def test_want_deep_plan_values_refused_as_pinerror(study, depth):
    tmp_path, root, plan = study
    text = json.dumps(plan)
    nested = "[" * depth + "]" * depth
    text = text.replace('"input_sets": [', '"input_sets": [' + nested + ", ", 1)
    p = tmp_path / "plan.json"
    p.write_text(text)
    with pytest.raises(pins.PinError):
        pins.run_pinned(p, tmp_path / "out", never, plan_sha256=sha(p.read_bytes()))
    assert not (tmp_path / "out").exists()


def test_obs_deep_directory_tree_in_set_pre_run(study):
    tmp_path, root, plan = study
    d = root / "data/candles"
    fd = os.open(d, os.O_RDONLY)
    for _ in range(1200):
        os.mkdir("d", dir_fd=fd)
        nfd = os.open("d", os.O_RDONLY, dir_fd=fd)
        os.close(fd)
        fd = nfd
    os.close(fd)
    path, h = save(tmp_path, plan)
    with pytest.raises(BaseException) as e:
        pins.run_pinned(path, tmp_path / "out", never, plan_sha256=h)
    print(type(e.value).__name__, str(e.value)[:200])
    assert not (tmp_path / "out").exists()


def test_want_deep_directory_tree_created_during_compute_refused_with_record(study):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"

    def compute(p):
        fd = os.open(root / "data/candles", os.O_RDONLY)
        for _ in range(1200):
            os.mkdir("d", dir_fd=fd)
            nfd = os.open("d", os.O_RDONLY, dir_fd=fd)
            os.close(fd)
            fd = nfd
        os.close(fd)
        return {"v": 1}
    with pytest.raises(pins.PinError) as e:
        pins.run_pinned(path, out, compute, plan_sha256=h)
    print(e.value.failures[:3])
    assert (out / "refused.json").is_file() and not (out / "result.json").exists()


# ---- 11. non-Exception interruptions and write failures after the checks --------------------

def test_obs_keyboard_interrupt_during_post_run_leaves_no_record(study, monkeypatch):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    real = pins.verify
    calls = []

    def verify(p):
        calls.append(1)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(p)
    monkeypatch.setattr(pins, "verify", verify)
    with pytest.raises(KeyboardInterrupt):
        pins.run_pinned(path, out, lambda p: {"v": 1}, plan_sha256=h)
    assert sorted(os.listdir(out)) == ["pin_receipt.json"]
    with pytest.raises(pins.PinError):
        pins.check_output(out)


def _fail_on_result(monkeypatch, which):
    real_write_new, real_write, real_fsync = pins._write_new, os.write, os.fsync
    state = {"on": False}

    def write_new(dir_fd, name, data):
        state["on"] = name == pins.RESULT_NAME
        try:
            return real_write_new(dir_fd, name, data)
        finally:
            state["on"] = False

    def write(fd, data):
        if state["on"] and which == "partial":
            real_write(fd, bytes(data[: len(data) // 2]))
            raise OSError(errno.ENOSPC, "No space left on device")
        return real_write(fd, data)

    def fsync(fd):
        if state["on"] and which == "fsync" and os.readlink(f"/proc/self/fd/{fd}").endswith("result.json"):
            raise OSError(errno.EIO, "EIO")
        return real_fsync(fd)
    monkeypatch.setattr(pins, "_write_new", write_new)
    monkeypatch.setattr(os, "write", write)
    monkeypatch.setattr(os, "fsync", fsync)


def test_obs_partial_result_write_leaves_no_refusal_but_check_output_rejects(study, monkeypatch):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    _fail_on_result(monkeypatch, "partial")
    with pytest.raises(OSError) as e:
        pins.run_pinned(path, out, lambda p: {"v": 1}, plan_sha256=h)
    assert not isinstance(e.value, pins.PinError)
    assert sorted(os.listdir(out)) == ["pin_receipt.json", "result.json"]
    with pytest.raises(pins.PinError, match="bad_json:result.json"):
        pins.check_output(out)


def test_obs_result_fsync_failure_raises_but_check_output_accepts(study, monkeypatch):
    tmp_path, root, plan = study
    path, h = save(tmp_path, plan)
    out = tmp_path / "out"
    _fail_on_result(monkeypatch, "fsync")
    with pytest.raises(OSError):
        pins.run_pinned(path, out, lambda p: {"v": 1}, plan_sha256=h)
    monkeypatch.undo()
    assert pins.check_output(out, expected_plan_sha256=h)["v"] == 1


# ---- 12. file_sha256 helper -----------------------------------------------------------------

def test_obs_file_sha256_purepath_escapes_root_str_does_not(study):
    tmp_path, root, plan = study
    (tmp_path / "outside.txt").write_bytes(b"outside")
    assert pins.file_sha256(root, PurePosixPath("../outside.txt")) == sha(b"outside")
    assert pins.file_sha256(root, PurePosixPath(str(tmp_path / "outside.txt"))) == sha(b"outside")
    with pytest.raises(pins.PinError, match="path_outside_root"):
        pins.file_sha256(root, "../outside.txt")
