"""Fail-closed pinned-input guard for future pre-registered research runs.

Stdlib only; POSIX (Linux, macOS). Nothing is computed until the plan file and
every pinned input verify: the preregistration, data files, checksum-listed
data directories, runner sources, model files and runtime versions. A receipt
is written and flushed before computing. Afterwards the plan file, every pin,
the output directory's identity and the receipt's bytes are checked again
against the guard's own copy of the plan, and the output directory must hold
nothing but the receipt. Only then is result.json written. Any refusal raises
PinError and, once the output directory exists, writes refused.json.

Plan (JSON), all paths relative to "root", every SHA256 64 lowercase hex:

    {"schema": "pinned-run-inputs-v1",
     "root": "/abs/canonical/path",
     "preregistration": {"path": "docs/.../PREREGISTRATION.md", "sha256": "..."},
     "inputs": {"data/exclusions.csv": "..."},
     "input_sets": [{"dir": "data/candles", "sums": "data/candles/SHA256SUMS",
                     "sums_sha256": "..."}],
     "sources": {"scripts/research/run_x.py": "..."},
     "model": {"revision": "<40-hex commit>", "files": {"models/x/model.safetensors": "..."}},
     "runtime": {"python": "3.12.7", "packages": {"numpy": "2.1.0"}}}

Rules:
- "preregistration" and "sources" are required, plus at least one of "inputs"
  or "input_sets". "model" and "runtime" are optional; if a key is present it
  must be a complete pin (null or an empty runtime is refused).
- root must be absolute and canonical (no symlink or ".." anywhere in it).
  Pinned paths are opened one directory at a time relative to root with
  O_NOFOLLOW, so no symlink is followed even if one is swapped in during the
  check; only regular files are hashed and special files are never opened.
- A checksum-listed directory must contain exactly the listed files (the sums
  file itself excepted), no other directories, no symlinks and nothing
  unreadable. Listed names must stay distinct after Unicode NFC normalisation
  and case folding, so a set means the same files on macOS and Linux (names
  that differ only by case are refused even on Linux). Members of a set are not
  evaluated if its checksum list fails; that is reported as set_members_not_checked.
- Duplicate JSON keys, non-finite numbers and unparseable JSON are refused.
- verify() reports every failure it can evaluate. File checks are skipped when
  root is invalid; structural failures are still all reported.

Usage in a runner. compute receives a deep copy of the plan and must return ALL
of its results in one JSON-serialisable dict (tables as lists of rows); it must
not write files. The output directory ends with exactly pin_receipt.json and
result.json:

    run_pinned(plan_path, out_dir, compute, plan_sha256="<operator-pinned>")
    check_output(out_dir, expected_plan_sha256="<operator-pinned>")  # consumers

If compute writes result.json or refused.json itself, the guard refuses the run
and renames those files to "<name>.unguarded" (never deletes them) before
writing its own refused.json.

Trust boundary and limits:
- compute and the runner are trusted, hash-pinned code in the same process.
  The guard detects input drift, operator error and accidental misuse; it is
  not a sandbox against compute code that deliberately subverts it (e.g.
  patching this module or forging output files).
- check_output() rejects incomplete, refused, malformed or mismatched output
  directories. It has no secret key, so it cannot prove that hand-made files
  were not produced outside run_pinned; pass expected_plan_sha256 to bind the
  output to the operator-pinned plan. It does not re-verify inputs.
- compute reads files after they were verified. The post-run check catches a
  change still present at the end; a change reverted before the end is not detected.
- Runtime pins compare installed version strings, not package contents. The
  model revision is a recorded label; model identity is enforced by file hashes.
- The root path itself is checked for canonicality once per verify(); its
  directory identity (device, inode) is then enforced on every open.
- This module does not make VOLFC-1 or any other frozen study re-verifiable
  after the fact; it applies to runs started through it.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import errno
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import unicodedata

SCHEMA = "pinned-run-inputs-v1"
RECEIPT_SCHEMA = "pinned-run-receipt-v1"
REFUSAL_SCHEMA = "pinned-run-refusal-v1"
PLAN_KEYS = {"schema", "root", "preregistration", "inputs", "input_sets", "sources", "model", "runtime"}
RECEIPT_KEYS = {"schema", "files", "preregistration_sha256", "model_revision", "runtime",
                "plan_sha256", "verified_utc"}
RECEIPT_NAME, RESULT_NAME, REFUSED_NAME = "pin_receipt.json", "result.json", "refused.json"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_SUMS_LINE = re.compile(r"([0-9a-f]{64}) [ *](.+)")
_CHUNK = 1 << 20
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW
_FILE_FLAGS = os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
_NEW_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW
_FD_SUPPORT = (os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
               and os.rename in os.supports_dir_fd and os.listdir in os.supports_fd
               and bool(_NOFOLLOW))


class PinError(ValueError):
    """Raised with every failed pin; reasons look like 'reason:path'."""

    def __init__(self, failures):
        self.failures = list(failures)
        super().__init__("pinned_inputs_refused: " + "; ".join(self.failures))


def _now():
    return datetime.now(timezone.utc).isoformat()


def _text_ok(value):
    if type(value) is not str or not value or "\x00" in value:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _rel(value):
    if not _text_ok(value) or "\\" in value:
        raise PinError(["bad_path:" + repr(value)[:80]])
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise PinError(["path_outside_root:" + value])
    return path


def _hex(value, pattern, label):
    if type(value) is not str or not pattern.fullmatch(value):
        raise PinError(["bad_hash_format:" + label])
    return value


def _ident(st):
    return (st.st_dev, st.st_ino)


class _Root:
    __slots__ = ("path", "ident")

    def __init__(self, path, ident):
        self.path, self.ident = path, ident


def _open_dir_chain(root, parts, label):
    """Open root and then each directory in parts without following symlinks; return its fd."""
    fd = os.open(root.path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        if _ident(os.fstat(fd)) != root.ident:
            raise PinError(["root_replaced"])
        for part in parts:
            st = os.stat(part, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode):
                raise PinError(["symlink_refused:" + label])
            if not stat.S_ISDIR(st.st_mode):
                raise PinError(["not_a_directory:" + label])
            try:
                child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            except OSError as error:
                if error.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise PinError(["symlink_or_replaced:" + label]) from None
                raise
            os.close(fd)
            fd = child
            if _ident(os.fstat(fd)) != _ident(st):
                raise PinError(["replaced_while_opening:" + label])
        return fd
    except BaseException:
        os.close(fd)
        raise


def _hash_regular(root, rel, keep=False):
    """Hash a regular file under root; never follow a symlink or open a special file."""
    rel = _rel(rel) if isinstance(rel, str) else rel
    name = rel.as_posix()
    try:
        parent = _open_dir_chain(root, rel.parts[:-1], name)
    except FileNotFoundError:
        raise PinError(["missing:" + name]) from None
    except OSError:
        raise PinError(["unreadable:" + name]) from None
    try:
        try:
            before = os.stat(rel.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            raise PinError(["missing:" + name]) from None
        except OSError:
            raise PinError(["unreadable:" + name]) from None
        if stat.S_ISLNK(before.st_mode):
            raise PinError(["symlink_refused:" + name])
        if not stat.S_ISREG(before.st_mode):
            raise PinError(["not_a_regular_file:" + name])
        try:
            fd = os.open(rel.name, _FILE_FLAGS, dir_fd=parent)
        except OSError:
            raise PinError(["unreadable_or_replaced:" + name]) from None
    finally:
        os.close(parent)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _ident(opened) != _ident(before):
            raise PinError(["replaced_while_opening:" + name])
        digest, kept = hashlib.sha256(), []
        while chunk := os.read(fd, _CHUNK):
            digest.update(chunk)
            if keep:
                kept.append(chunk)
    except OSError:
        raise PinError(["unreadable:" + name]) from None
    finally:
        os.close(fd)
    return digest.hexdigest(), b"".join(kept)


def file_sha256(root, rel):
    """SHA256 of root/rel under the same no-symlink rules (root must be canonical)."""
    failures = []
    checked = _root(str(root), failures)
    if checked is None:
        raise PinError(failures)
    return _hash_regular(checked, rel)[0]


def _check(root, rel, expected, seen, failures, keep=False):
    try:
        path = _rel(rel)
        _hex(expected, _HEX64, rel)
        actual, data = _hash_regular(root, path, keep)
    except PinError as error:
        failures.extend(error.failures)
        return None
    seen[path.as_posix()] = actual
    if actual != expected:
        failures.append("hash_mismatch:" + path.as_posix())
        return None
    return data


def _collision_key(name):
    return unicodedata.normalize("NFC", name).casefold()


def _parse_sums(data, label, failures):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        failures.append("bad_sums_encoding:" + label)
        return None
    listed, keys = {}, set()
    for number, line in enumerate(text.splitlines(), 1):
        match = _SUMS_LINE.fullmatch(line)
        if not match:
            failures.append(f"bad_sums_line:{label}:{number}")
            return None
        name = match.group(2)
        try:
            _rel(name)
        except PinError as error:
            failures.extend(error.failures)
            return None
        if name in listed:
            failures.append("duplicate_sums_entry:" + name)
            return None
        if _collision_key(name) in keys:
            failures.append("colliding_sums_entry:" + name)
            return None
        listed[name] = match.group(1)
        keys.add(_collision_key(name))
    if not listed:
        failures.append("empty_sums:" + label)
        return None
    return listed


def _ancestors(names):
    found = set()
    for name in names:
        parent = PurePosixPath(name).parent
        while parent.as_posix() != ".":
            found.add(parent.as_posix())
            parent = parent.parent
    return found


def _list_entries(dir_fd, label):
    """Names in an open directory (label is for diagnostics and tests)."""
    return os.listdir(dir_fd)


def _walk(dir_fd, prefix, directory, allowed_dirs, present, failures):
    here = (directory / prefix).as_posix() if prefix else directory.as_posix()
    try:
        names = sorted(_list_entries(dir_fd, here))
    except OSError:
        failures.append("unreadable_directory:" + here)
        return
    for name in names:
        member = f"{prefix}/{name}" if prefix else name
        shown = (directory / member).as_posix()
        try:
            st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        except OSError:
            failures.append("unreadable:" + shown)
            continue
        if stat.S_ISLNK(st.st_mode):
            failures.append("symlink_refused:" + shown)
        elif stat.S_ISDIR(st.st_mode):
            if member not in allowed_dirs:
                failures.append("unlisted_directory:" + shown)
            try:
                child = os.open(name, _DIR_FLAGS, dir_fd=dir_fd)
            except OSError:
                failures.append("unreadable_directory:" + shown)
                continue
            try:
                if _ident(os.fstat(child)) != _ident(st):
                    failures.append("replaced_while_opening:" + shown)
                else:
                    _walk(child, member, directory, allowed_dirs, present, failures)
            finally:
                os.close(child)
        else:
            present.add(member)


def _check_set(root, spec, seen, failures):
    if type(spec) is not dict or set(spec) != {"dir", "sums", "sums_sha256"}:
        failures.append("bad_input_set:" + repr(spec)[:80])
        return
    try:
        directory, sums = _rel(spec["dir"]), _rel(spec["sums"])
    except PinError as error:
        failures.extend(error.failures)
        return
    label = directory.as_posix()
    data = _check(root, spec["sums"], spec["sums_sha256"], seen, failures, keep=True)
    listed = None if data is None else _parse_sums(data, sums.as_posix(), failures)
    if listed is None:
        failures.append("set_members_not_checked:" + label)
        return
    try:
        dir_fd = _open_dir_chain(root, directory.parts, label)
    except FileNotFoundError:
        failures.append("missing:" + label)
        return
    except OSError:
        failures.append("unreadable_directory:" + label)
        return
    except PinError as error:
        failures.extend(error.failures)
        return
    prefix = label + "/"
    expected_files = set(listed)
    if sums.as_posix().startswith(prefix):
        expected_files.add(sums.as_posix()[len(prefix):])
    present = set()
    try:
        _walk(dir_fd, "", directory, _ancestors(expected_files), present, failures)
    finally:
        os.close(dir_fd)
    for name in sorted(present - expected_files):
        failures.append("unlisted_file:" + (directory / name).as_posix())
    for name in sorted(listed):
        _check(root, (directory / name).as_posix(), listed[name], seen, failures)


def _check_runtime(spec, failures):
    if type(spec) is not dict or not set(spec) <= {"python", "packages"}:
        failures.append("bad_runtime")
        return {}
    packages = spec.get("packages", {})
    if (("python" in spec and not _text_ok(spec["python"])) or type(packages) is not dict
            or any(not _text_ok(k) or not _text_ok(v) for k, v in packages.items())):
        failures.append("bad_runtime")
        return {}
    if "python" not in spec and not packages:
        failures.append("empty_runtime_pin")
        return {}
    observed = {}
    if "python" in spec:
        observed["python"] = platform.python_version()
        if observed["python"] != spec["python"]:
            failures.append("runtime_mismatch:python")
    for name, expected in sorted(packages.items()):
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            failures.append("runtime_missing:" + name)
            continue
        observed[name] = version
        if version != expected:
            failures.append("runtime_mismatch:" + name)
    return observed


def _root(value, failures):
    if type(value) is not str or not os.path.isabs(value):
        failures.append("root_must_be_absolute")
        return None
    if not _text_ok(value):
        failures.append("bad_root")
        return None
    if not _FD_SUPPORT:
        failures.append("platform_unsupported")
        return None
    if os.path.realpath(value) != str(Path(value)):
        failures.append("root_not_canonical")
        return None
    try:
        st = os.stat(value)
    except OSError:
        failures.append("missing_root")
        return None
    if not stat.S_ISDIR(st.st_mode):
        failures.append("missing_root")
        return None
    return _Root(Path(value), _ident(st))


def verify(plan):
    """Check every pin; return a receipt or raise PinError listing every failure found."""
    if type(plan) is not dict:
        raise PinError(["bad_schema"])
    failures, seen = [], {}
    if plan.get("schema") != SCHEMA:
        failures.append("bad_schema")
    unknown = set(plan) - PLAN_KEYS
    if unknown:
        failures.append("unknown_plan_keys:" + ",".join(sorted(map(str, unknown))))
    root = _root(plan.get("root"), failures)
    prereg = plan.get("preregistration")
    if type(prereg) is not dict or set(prereg) != {"path", "sha256"}:
        failures.append("preregistration_pin_required")
        prereg = None
    sources = plan.get("sources")
    if type(sources) is not dict or not sources:
        failures.append("source_pins_required")
        sources = {}
    inputs, sets = plan.get("inputs", {}), plan.get("input_sets", [])
    if type(inputs) is not dict:
        failures.append("bad_inputs")
        inputs = {}
    if type(sets) is not list:
        failures.append("bad_input_sets")
        sets = []
    if not inputs and not sets:
        failures.append("input_pins_required")
    model = None
    if "model" in plan:
        candidate = plan["model"]
        if (type(candidate) is not dict or set(candidate) != {"revision", "files"}
                or type(candidate["files"]) is not dict or not candidate["files"]):
            failures.append("bad_model_pin")
        else:
            model = candidate
            try:
                _hex(model["revision"], _HEX40, "model_revision")
            except PinError as error:
                failures.extend(error.failures)
    runtime = _check_runtime(plan["runtime"], failures) if "runtime" in plan else {}
    if root is not None:
        if prereg is not None:
            _check(root, prereg["path"], prereg["sha256"], seen, failures)
        for group in (inputs, sources):
            for rel, expected in sorted(group.items(), key=lambda item: str(item[0])):
                _check(root, rel, expected, seen, failures)
        for spec in sets:
            _check_set(root, spec, seen, failures)
        if model is not None:
            for rel, expected in sorted(model["files"].items(), key=lambda item: str(item[0])):
                _check(root, rel, expected, seen, failures)
    if failures:
        raise PinError(failures)
    return {"schema": RECEIPT_SCHEMA, "files": dict(sorted(seen.items())),
            "preregistration_sha256": prereg["sha256"],
            "model_revision": model["revision"] if model else None, "runtime": runtime}


def _refuse_constant(name):
    raise PinError(["non_finite_json:" + name])


def _unique_pairs(pairs):
    keys = set()
    for key, _ in pairs:
        if key in keys:
            raise PinError(["duplicate_json_key:" + key])
        keys.add(key)
    return dict(pairs)


def _load_json(raw, label):
    try:
        return json.loads(raw, parse_constant=_refuse_constant, object_pairs_hook=_unique_pairs)
    except PinError:
        raise
    except (ValueError, RecursionError):
        raise PinError(["bad_json:" + label]) from None


def _encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _fsync_fd(fd):
    try:
        os.fsync(fd)
    except OSError as error:
        if error.errno not in (errno.EINVAL, errno.ENOTSUP, errno.EBADF):
            raise


def _fsync_path(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        _fsync_fd(fd)
    finally:
        os.close(fd)


def _write_new(dir_fd, name, data):
    fd = os.open(name, _NEW_FLAGS, 0o644, dir_fd=dir_fd)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_fd(dir_fd)


def _read_at(dir_fd, name):
    """Bytes of a regular, non-symlink file in an open directory, else None."""
    try:
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode):
            return None
        fd = os.open(name, _FILE_FLAGS, dir_fd=dir_fd)
    except OSError:
        return None
    try:
        if _ident(os.fstat(fd)) != _ident(st):
            return None
        chunks = []
        while chunk := os.read(fd, _CHUNK):
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError:
        return None
    finally:
        os.close(fd)


def _make_out(out):
    """Create out (and missing parents), fsync each new entry; return (fd, identity)."""
    missing, probe = [], out
    while not os.path.lexists(probe):
        missing.append(probe)
        probe = probe.parent
    if not missing:
        raise FileExistsError(errno.EEXIST, "output directory exists", str(out))
    out.mkdir(parents=True, exist_ok=False)
    for created in reversed(missing):
        _fsync_path(created.parent)
    fd = os.open(out, _DIR_FLAGS)
    return fd, _ident(os.fstat(fd))


def _set_aside(dir_fd, name, names):
    for index in range(100):
        target = f"{name}.unguarded" + (f".{index}" if index else "")
        if target not in names:
            os.rename(name, target, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            names.add(target)
            return
    raise OSError(errno.EEXIST, "no free name to set aside " + name)


def _refuse(out_fd, failures):
    """Record a refusal in the guard's own output directory (best effort)."""
    try:
        names = set(os.listdir(out_fd))
        for name in (RESULT_NAME, REFUSED_NAME):
            if name in names:
                _set_aside(out_fd, name, names)
    except (OSError, ValueError):
        pass
    try:
        _write_new(out_fd, REFUSED_NAME, _encode({"schema": REFUSAL_SCHEMA, "failures": failures,
                                                  "refused_utc": _now()}))
    except (OSError, ValueError, TypeError):
        pass  # the refusal is still raised; check_output rejects any directory without a valid result


def _refuse_out_inside_sets(plan, out):
    root, target = Path(plan["root"]), Path(os.path.realpath(out))
    identities = {}
    for spec in plan.get("input_sets", []):
        pinned = root / spec["dir"]
        if target == pinned or pinned in target.parents:
            raise PinError(["out_dir_inside_pinned_set:" + spec["dir"]])
        try:
            identities[_ident(os.stat(pinned))] = spec["dir"]
        except OSError:
            raise PinError(["unreadable_directory:" + spec["dir"]]) from None
    for ancestor in (out, *out.parents):  # also catches bind mounts realpath cannot see
        try:
            ident = _ident(os.stat(ancestor))
        except OSError:
            continue
        if ident in identities:
            raise PinError(["out_dir_inside_pinned_set:" + identities[ident]])


def _post_run(plan, plan_path, plan_sha, receipt, receipt_bytes, out, out_fd, out_id, result):
    failures = []
    try:
        if hashlib.sha256(plan_path.read_bytes()).hexdigest() != plan_sha:
            failures.append("plan_changed_during_run")
    except OSError:
        failures.append("plan_unreadable_after_run")
    try:
        after = verify(plan)
    except PinError as error:
        failures.extend(error.failures)
    else:
        if after["files"] != receipt["files"] or after["runtime"] != receipt["runtime"]:
            failures.append("inputs_changed_during_run")
    try:
        st = os.lstat(out)
        if not stat.S_ISDIR(st.st_mode) or _ident(st) != out_id:
            failures.append("out_dir_replaced_during_run")
    except OSError:
        failures.append("out_dir_replaced_during_run")
    if _read_at(out_fd, RECEIPT_NAME) != receipt_bytes:
        failures.append("receipt_changed_during_run")
    extra = sorted(set(os.listdir(out_fd)) - {RECEIPT_NAME})
    if extra:
        failures.append("unexpected_output_files:" + ",".join(extra))
    data = payload = None
    if type(result) is not dict:
        failures.append("compute_must_return_dict")
    else:
        payload = {**result, "pinned_inputs": {"plan_sha256": plan_sha,
                                               "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest()}}
        try:
            data = _encode(payload)
        except Exception:  # NaN, non-JSON types, excessive nesting
            failures.append("result_not_encodable")
    return failures, data, payload


def run_pinned(plan_path, out_dir, compute, *, plan_sha256):
    """Verify, record, compute on a copy, re-verify, then write result.json.

    plan_sha256 pins the plan file itself and is required. out_dir must not
    exist and must not lie inside a checksum-listed directory. Nothing is
    computed unless every pin verifies first. No result is written if compute
    fails, the plan file, any pin, the output directory or the receipt changed,
    compute left any file in out_dir, or the result is not encodable JSON.
    Paths are made absolute on entry and all output is written through an open
    directory descriptor, so compute changing the working directory has no effect.
    """
    expected = _hex(plan_sha256, _HEX64, "plan_sha256")
    plan_path = Path(os.path.abspath(plan_path))
    out = Path(os.path.abspath(out_dir))
    raw = plan_path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise PinError(["plan_hash_mismatch"])
    plan = _load_json(raw, "plan")
    receipt = verify(plan)
    _refuse_out_inside_sets(plan, out)
    receipt.update(plan_sha256=actual, verified_utc=_now())
    receipt_bytes = _encode(receipt)
    out_fd, out_id = _make_out(out)
    try:
        _write_new(out_fd, RECEIPT_NAME, receipt_bytes)
        try:
            result = compute(copy.deepcopy(plan))
        except BaseException as error:
            _refuse(out_fd, ["compute_error:" + type(error).__name__])
            raise
        try:
            failures, data, payload = _post_run(plan, plan_path, actual, receipt, receipt_bytes,
                                                out, out_fd, out_id, result)
        except Exception as error:
            failures, data, payload = ["post_run_check_error:" + type(error).__name__], None, None
        if failures:
            _refuse(out_fd, failures)
            raise PinError(failures)
        _write_new(out_fd, RESULT_NAME, data)
        return payload
    finally:
        os.close(out_fd)


def _receipt_problems(receipt):
    if type(receipt) is not dict or set(receipt) != RECEIPT_KEYS or receipt["schema"] != RECEIPT_SCHEMA:
        return ["output_bad_receipt"]
    files, runtime = receipt["files"], receipt["runtime"]
    try:
        datetime.fromisoformat(receipt["verified_utc"])
        stamped = True
    except (TypeError, ValueError):
        stamped = False
    valid = (stamped
             and type(files) is dict and bool(files)
             and all(_text_ok(k) and type(v) is str and _HEX64.fullmatch(v) for k, v in files.items())
             and type(receipt["plan_sha256"]) is str and bool(_HEX64.fullmatch(receipt["plan_sha256"]))
             and type(receipt["preregistration_sha256"]) is str
             and bool(_HEX64.fullmatch(receipt["preregistration_sha256"]))
             and receipt["preregistration_sha256"] in files.values()
             and (receipt["model_revision"] is None
                  or (type(receipt["model_revision"]) is str and bool(_HEX40.fullmatch(receipt["model_revision"]))))
             and type(runtime) is dict and all(_text_ok(k) and _text_ok(v) for k, v in runtime.items()))
    return [] if valid else ["output_bad_receipt"]


def check_output(out_dir, *, expected_plan_sha256=None):
    """Return the result of a completed guarded run, or raise PinError.

    Requires exactly pin_receipt.json and result.json as regular files (no
    refused.json, no symlinks), a structurally complete receipt, and a result
    whose pinned_inputs link holds exactly that receipt's SHA256 and the same
    64-hex plan SHA256 (and expected_plan_sha256, when given). Without a secret
    key this cannot prove the files were not hand-made; see the module docstring.
    """
    if expected_plan_sha256 is not None:
        _hex(expected_plan_sha256, _HEX64, "expected_plan_sha256")
    try:
        dir_fd = os.open(Path(out_dir), _DIR_FLAGS)
    except (OSError, ValueError):
        raise PinError(["output_unreadable"]) from None
    try:
        names = sorted(os.listdir(dir_fd))
        blobs = {name: _read_at(dir_fd, name) for name in names if name in (RECEIPT_NAME, RESULT_NAME)}
    except OSError:
        raise PinError(["output_unreadable"]) from None
    finally:
        os.close(dir_fd)
    if names != [RECEIPT_NAME, RESULT_NAME]:
        raise PinError(["output_incomplete_or_refused:" + ",".join(names)])
    for name in names:
        if blobs[name] is None:
            raise PinError(["output_not_regular_file:" + name])
    receipt = _load_json(blobs[RECEIPT_NAME], RECEIPT_NAME)
    result = _load_json(blobs[RESULT_NAME], RESULT_NAME)
    problems = _receipt_problems(receipt)
    if problems:
        raise PinError(problems)
    link = result.get("pinned_inputs") if type(result) is dict else None
    if (type(link) is not dict or set(link) != {"plan_sha256", "receipt_sha256"}
            or link["receipt_sha256"] != hashlib.sha256(blobs[RECEIPT_NAME]).hexdigest()
            or link["plan_sha256"] != receipt["plan_sha256"]):
        raise PinError(["output_link_mismatch"])
    if expected_plan_sha256 is not None and receipt["plan_sha256"] != expected_plan_sha256:
        raise PinError(["output_plan_mismatch"])
    return result
