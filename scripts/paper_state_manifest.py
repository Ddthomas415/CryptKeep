#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    pass


def _json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _state_dir(path: Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ManifestError("state_dir_missing")
    if not resolved.is_dir():
        raise ManifestError("state_dir_not_directory")
    return resolved


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_output_path(output: Path, state_dir: Path) -> Path:
    resolved = Path(output).expanduser().resolve()
    if _is_relative_to(resolved, state_dir):
        raise ManifestError("manifest_output_inside_state_dir")
    return resolved


def _validate_manifest_relpath(raw: str) -> str:
    value = str(raw or "").strip()
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ManifestError("manifest_path_invalid")
    return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(state_dir: Path) -> dict[str, str]:
    root = _state_dir(state_dir)
    rows: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ManifestError(f"state_dir_symlink_not_supported:{rel}")
        if not path.is_file():
            continue
        rows[rel] = _sha256(path)
    return rows


def manifest_text(rows: dict[str, str]) -> str:
    lines = [f"{digest}  {rel}" for rel, digest in sorted(rows.items())]
    return "\n".join(lines) + ("\n" if lines else "")


def parse_manifest(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            digest, rel = line.split("  ", 1)
        except ValueError as exc:
            raise ManifestError(f"manifest_line_invalid:{lineno}") from exc
        digest = digest.strip().lower()
        if not _SHA256_RE.fullmatch(digest):
            raise ManifestError(f"manifest_digest_invalid:{lineno}")
        rel = _validate_manifest_relpath(rel)
        if rel in rows:
            raise ManifestError(f"manifest_duplicate_path:{rel}")
        rows[rel] = digest
    return rows


def create_manifest(*, state_dir: Path, output: Path) -> dict[str, Any]:
    root = _state_dir(state_dir)
    out = _validate_output_path(output, root)
    rows = build_manifest(root)
    text = manifest_text(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return {
        "ok": True,
        "action": "create",
        "state_dir": str(root),
        "output": str(out),
        "file_count": len(rows),
        "manifest_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def verify_manifest(*, state_dir: Path, manifest: Path) -> dict[str, Any]:
    root = _state_dir(state_dir)
    manifest_path = Path(manifest).expanduser().resolve()
    expected = parse_manifest(manifest_path.read_text(encoding="utf-8"))
    actual = build_manifest(root)

    expected_paths = set(expected)
    actual_paths = set(actual)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    changed = sorted(
        rel for rel in expected_paths & actual_paths if expected[rel] != actual[rel]
    )
    ok = not missing and not extra and not changed
    return {
        "ok": ok,
        "action": "verify",
        "state_dir": str(root),
        "manifest": str(manifest_path),
        "expected_file_count": len(expected),
        "actual_file_count": len(actual),
        "missing": missing,
        "changed": changed,
        "extra": extra,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or verify a deterministic SHA-256 manifest for paper state."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Write a manifest for a paper state directory")
    create.add_argument("--state-dir", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)

    verify = sub.add_parser("verify", help="Verify a paper state directory against a manifest")
    verify.add_argument("--state-dir", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            payload = create_manifest(state_dir=args.state_dir, output=args.output)
        else:
            payload = verify_manifest(state_dir=args.state_dir, manifest=args.manifest)
    except (ManifestError, OSError, UnicodeDecodeError) as exc:
        payload = {
            "ok": False,
            "action": str(getattr(args, "command", "unknown") or "unknown"),
            "reason": str(exc) or type(exc).__name__,
        }
    _json(payload)
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    sys.exit(main())
