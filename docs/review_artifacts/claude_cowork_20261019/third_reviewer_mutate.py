"""Reviewer's own mutation check of v3 protections against the shipped tests (copies only)."""
import shutil
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
SRC = W / "repo"
PY = sys.argv[1]
MOD = "scripts/research/pinned_run_inputs.py"

MUTANTS = {
    "M01_root_ident_check": ("if _ident(os.fstat(fd)) != root.ident:", "if False:"),
    "M02_eloop_enotdir_map": ("if error.errno in (errno.ELOOP, errno.ENOTDIR):", "if False:"),
    "M03_chain_child_ident": ("            if _ident(os.fstat(fd)) != _ident(st):\n                raise PinError([\"replaced_while_opening:\" + label])",
                              "            if False:\n                raise PinError([\"replaced_while_opening:\" + label])"),
    "M04_dir_flags_follow": ('_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW',
                             '_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)'),
    "M05_chain_stat_symlink": ("            if stat.S_ISLNK(st.st_mode):\n                raise PinError([\"symlink_refused:\" + label])",
                               "            if False:\n                raise PinError([\"symlink_refused:\" + label])"),
    "M06_out_identity": ("if not stat.S_ISDIR(st.st_mode) or _ident(st) != out_id:", "if False:"),
    "M07_receipt_bytes": ("if _read_at(out_fd, RECEIPT_NAME) != receipt_bytes:", "if False:"),
    "M08_no_set_aside": ("for name in (RESULT_NAME, REFUSED_NAME):", "for name in ():"),
    "M09_no_ancestor_identity": ("for ancestor in (out, *out.parents):", "for ancestor in ():"),
    "M10_casefold_only": ('return unicodedata.normalize("NFC", name).casefold()', "return name.casefold()"),
    "M11_link_exact_keys": ('or set(link) != {"plan_sha256", "receipt_sha256"}', "or False"),
    "M12_expected_plan": ("if expected_plan_sha256 is not None and receipt[\"plan_sha256\"] != expected_plan_sha256:", "if False:"),
    "M13_prereg_in_files": ('and receipt["preregistration_sha256"] in files.values()', "and True"),
    "M14_read_at_ident": ("        if _ident(os.fstat(fd)) != _ident(st):\n            return None", "        if False:\n            return None"),
    "M15_no_post_run_catch": ("        except Exception as error:\n            failures, data, payload = [\"post_run_check_error:\"",
                              "        except ZeroDivisionError as error:\n            failures, data, payload = [\"post_run_check_error:\""),
    "M16_out_not_absolute": ("out = Path(os.path.abspath(out_dir))", "out = Path(out_dir)"),
    "M17_no_parent_fsync": ("        _fsync_path(created.parent)", "        pass"),
    "M18_walk_ident": ("if _ident(os.fstat(child)) != _ident(st):", "if False:"),
    "M19_file_ident": ("if not stat.S_ISREG(opened.st_mode) or _ident(opened) != _ident(before):", "if False:"),
    "M20_no_excl": ("_NEW_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW", "_NEW_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC"),
    "M21_receipt_revision": ('(receipt["model_revision"] is None\n', '(True or receipt["model_revision"] is None\n'),
    "M22_receipt_timestamp": ("        stamped = True\n    except (TypeError, ValueError):\n        stamped = False",
                              "        stamped = True\n    except (TypeError, ValueError):\n        stamped = True"),
    "M23_receipt_runtime_text": ('and type(runtime) is dict and all(_text_ok(k) and _text_ok(v) for k, v in runtime.items()))',
                                 'and type(runtime) is dict)'),
    "M24_no_deepcopy": ("result = compute(copy.deepcopy(plan))", "result = compute(plan)"),
    "M25_no_compute_error_refusal": ('            _refuse(out_fd, ["compute_error:" + type(error).__name__])\n', ""),
    "M26_no_plan_rehash": ("if hashlib.sha256(plan_path.read_bytes()).hexdigest() != plan_sha:", "if False:"),
    "M27_out_set_lexical": ("if target == pinned or pinned in target.parents:", "if False:"),
    "M28_check_output_follow": ("dir_fd = os.open(Path(out_dir), _DIR_FLAGS)", "dir_fd = os.open(Path(out_dir), os.O_RDONLY)"),
    "M29_files_hex": ("and all(_text_ok(k) and type(v) is str and _HEX64.fullmatch(v) for k, v in files.items())", "and True"),
    "M30_refuse_write_new": ('        _write_new(out_fd, REFUSED_NAME, _encode({"schema": REFUSAL_SCHEMA, "failures": failures,\n',
                             '        0 and _write_new(out_fd, REFUSED_NAME, _encode({"schema": REFUSAL_SCHEMA, "failures": failures,\n'),
}

base = (SRC / MOD).read_text()
(W / "mut_bt").mkdir(exist_ok=True)
MUTANTS = {"M00_CONTROL_unmutated": ("SCHEMA = \"pinned-run-inputs-v1\"", "SCHEMA = \"pinned-run-inputs-v1\""), **MUTANTS}
for name, (old, new) in MUTANTS.items():
    if base.count(old) != 1:
        print(name, "PATTERN_COUNT", base.count(old))
        continue
    dest = W / "mut" / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("probes_*", "v2tests", "__pycache__"))
    (dest / MOD).write_text(base.replace(old, new))
    r = subprocess.run(["timeout", "300", PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x",
                        f"--basetemp={W}/mut_bt/{name}", "tests/test_pinned_run_inputs.py"],
                       cwd=dest, capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    print(f"{name:32s} {'CAUGHT' if r.returncode else 'SURVIVED'}  {last}")
