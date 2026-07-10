from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import hashlib
import json
import shutil
import sqlite3
import time
from datetime import datetime, timezone

from services.os.app_paths import data_dir, runtime_dir

MANIFEST_NAME = "backup_manifest.json"
MANIFEST_VERSION = 1
ARCHIVE_SUBDIR = "state"  # archive-internal namespace (not the repo data dir)

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_BLOCKED = 2


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_sqlite(path: Path) -> bool:
    if path.suffix in (".sqlite", ".db", ".sqlite3"):
        return True
    try:
        with path.open("rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except Exception:
        return False


def _snapshot_sqlite(src: Path, dest: Path) -> None:
    """Consistent point-in-time snapshot via the sqlite backup API. A plain
    file copy of a live database tears pages under WAL/concurrent writes;
    the backup API takes a transactionally consistent snapshot even while
    writers are active."""
    src_con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        dest_con = sqlite3.connect(dest)
        try:
            src_con.backup(dest_con)
        finally:
            dest_con.close()
    finally:
        src_con.close()


def _integrity_ok(path: Path) -> bool:
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = con.execute("PRAGMA integrity_check").fetchone()
            return bool(row) and row[0] == "ok"
        finally:
            con.close()
    except Exception:
        return False


def _iter_state_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith((".tmp", ".json.tmp", "-wal", "-shm", ".lock")):
            continue  # ephemera; sqlite snapshots fold WAL content in
        yield path


def _manifest_rel_path(raw: object) -> Path | None:
    try:
        rel = Path(str(raw))
    except Exception:
        return None
    if rel.is_absolute():
        return None
    if rel.parts[:1] != (ARCHIVE_SUBDIR,):
        return None
    if ".." in rel.parts:
        return None
    return rel


def create_backup(dest_root: Path) -> dict:
    """Back up the durable state (data dir) into dest_root with a
    checksummed manifest. Safe to run while services are live."""
    src = data_dir()
    if not src.exists():
        return {"ok": False, "reason": f"data_dir_missing:{src}"}
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_dir = dest_root / f"cbp-state-backup-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)

    entries = []
    for path in _iter_state_files(src):
        rel = path.relative_to(src)
        dest = out_dir / ARCHIVE_SUBDIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        kind = "sqlite" if _is_sqlite(path) else "file"
        if kind == "sqlite":
            _snapshot_sqlite(path, dest)
            if not _integrity_ok(dest):
                return {"ok": False, "reason": f"snapshot_integrity_failed:{rel}"}
        else:
            shutil.copy2(path, dest)
        entries.append({
            "rel": str(Path(ARCHIVE_SUBDIR) / rel),
            "kind": kind,
            "bytes": dest.stat().st_size,
            "sha256": _sha256(dest),
        })

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "created": _iso_now(),
        "source_data_dir": str(src),
        "file_count": len(entries),
        "files": entries,
    }
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"ok": True, "backup_dir": str(out_dir), "file_count": len(entries)}


def verify_backup(backup_dir: Path) -> dict:
    """Verify every manifest checksum and sqlite integrity; read-only."""
    manifest_path = backup_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return {"ok": False, "reason": "manifest_missing"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"manifest_unreadable:{type(exc).__name__}"}
    problems = []
    files = manifest.get("files") or []
    for entry in files:
        rel = _manifest_rel_path(entry.get("rel"))
        if rel is None:
            problems.append(f"invalid_rel:{entry.get('rel')}")
            continue
        path = backup_dir / rel
        if not path.exists():
            problems.append(f"missing:{entry.get('rel')}")
            continue
        if _sha256(path) != entry.get("sha256"):
            problems.append(f"checksum_mismatch:{entry.get('rel')}")
            continue
        if entry.get("kind") == "sqlite" and not _integrity_ok(path):
            problems.append(f"integrity_failed:{entry.get('rel')}")
    if len(files) != int(manifest.get("file_count") or -1):
        problems.append("file_count_mismatch")
    return {"ok": not problems, "problems": problems, "file_count": len(files)}


def _live_locks(target_data: Path) -> list[str]:
    root = target_data.parent
    locks = []
    for pattern in ("*.lock",):
        locks += [str(p) for p in root.rglob(pattern)]
    return sorted(locks)


def restore_backup(backup_dir: Path, *, force: bool = False) -> dict:
    """
    Restore a verified backup into the CURRENT state dir's data directory.

    Hard safety guards (fail closed, in order):
    1. the backup must verify completely before anything is touched;
    2. any *.lock file under the state dir blocks restore — a live process
       writing during restore corrupts both worlds; stop services first;
    3. a non-empty data dir requires --force, and even then the existing
       data dir is moved aside to data.pre-restore-<stamp>, never deleted.
    """
    verdict = verify_backup(backup_dir)
    if not verdict["ok"]:
        return {"ok": False, "reason": "backup_verify_failed", "problems": verdict.get("problems")}

    target = data_dir()
    locks = _live_locks(target if target.exists() else runtime_dir())
    if locks:
        return {"ok": False, "reason": "live_locks_present", "locks": locks}

    aside = None
    if target.exists() and any(target.iterdir()):
        if not force:
            return {"ok": False, "reason": "target_not_empty_use_force", "target": str(target)}
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        aside = target.parent / f"data.pre-restore-{stamp}"
        target.rename(aside)
    target.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((backup_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        rel = _manifest_rel_path(entry["rel"])
        if rel is None:
            return {
                "ok": False,
                "reason": "backup_manifest_invalid_rel",
                "rel": entry.get("rel"),
                "moved_aside": str(aside) if aside else None,
            }
        path = backup_dir / rel
        dest = target / rel.relative_to(ARCHIVE_SUBDIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    post = []
    for entry in manifest["files"]:
        rel = _manifest_rel_path(entry["rel"])
        if rel is None:
            post.append(f"invalid_rel:{entry['rel']}")
            continue
        restored = target / rel.relative_to(ARCHIVE_SUBDIR)
        if not restored.exists() or _sha256(restored) != entry["sha256"]:
            post.append(f"post_restore_mismatch:{entry['rel']}")
    if post:
        return {"ok": False, "reason": "post_restore_verify_failed", "problems": post, "moved_aside": str(aside) if aside else None}
    return {"ok": True, "restored_files": len(manifest["files"]), "target": str(target), "moved_aside": str(aside) if aside else None}


def main() -> int:
    ap = argparse.ArgumentParser(description="CryptKeep full-state backup/restore (sqlite-API-consistent).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup", help="create a checksummed backup of the data dir (safe while live)")
    b.add_argument("--dest", required=True, help="directory to create the backup under")
    v = sub.add_parser("verify", help="verify a backup's manifest, checksums, and sqlite integrity")
    v.add_argument("backup_dir")
    r = sub.add_parser("restore", help="restore a verified backup into the current state dir (services must be stopped)")
    r.add_argument("backup_dir")
    r.add_argument("--force", action="store_true", help="allow restoring over a non-empty data dir (moved aside, never deleted)")
    args = ap.parse_args()

    if args.cmd == "backup":
        out = create_backup(Path(args.dest))
    elif args.cmd == "verify":
        out = verify_backup(Path(args.backup_dir))
    else:
        out = restore_backup(Path(args.backup_dir), force=args.force)

    print(json.dumps(out, indent=2))
    if out.get("ok"):
        return EXIT_OK
    return EXIT_BLOCKED if out.get("reason") in ("live_locks_present", "target_not_empty_use_force") else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
