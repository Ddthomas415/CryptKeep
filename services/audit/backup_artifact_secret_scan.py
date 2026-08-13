from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audit.jsonl_secret_scan import _is_safely_redacted, _is_sensitive_key

REPORT_TYPE = "backup_artifact_secret_scan"
SCHEMA_VERSION = 1

_TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".env",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".text",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

_BYTE_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("pem_private_key", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github_classic_token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("github_fine_grained_token", re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("aws_access_key_id", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(rb"\bxox[abprs]-[A-Za-z0-9-]{20,}\b")),
    ("openai_api_key", re.compile(rb"\bsk-[A-Za-z0-9]{24,}\b")),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _manifest_path(root: Path) -> Path:
    return root / "backup_manifest.json"


def _safe_rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def _value_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {"type": "str", "length": len(value)}
    if isinstance(value, list):
        return {"type": "list", "length": len(value)}
    if isinstance(value, dict):
        return {"type": "dict", "keys": len(value)}
    return {"type": type(value).__name__}


def _scan_json_value(
    value: Any,
    *,
    root: Path,
    source: Path,
    json_path: str,
    findings: list[dict[str, Any]],
) -> None:
    if isinstance(value, dict):
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            child_path = f"{json_path}.{key}" if json_path else key
            if _is_sensitive_key(key):
                if not _is_safely_redacted(raw_value):
                    findings.append(
                        {
                            "path": _safe_rel(root, source),
                            "reason": "sensitive_key_unredacted",
                            "json_path": child_path,
                            "value": _value_summary(raw_value),
                        }
                    )
                continue
            _scan_json_value(raw_value, root=root, source=source, json_path=child_path, findings=findings)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_json_value(item, root=root, source=source, json_path=f"{json_path}[{idx}]", findings=findings)


def _scan_structured_file(root: Path, path: Path, findings: list[dict[str, Any]]) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(
                {
                    "path": _safe_rel(root, path),
                    "reason": "json_unreadable",
                    "error": type(exc).__name__,
                }
            )
            return
        _scan_json_value(payload, root=root, source=path, json_path="", findings=findings)
        return

    if suffix == ".jsonl":
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            findings.append(
                {
                    "path": _safe_rel(root, path),
                    "reason": "jsonl_unreadable",
                    "error": type(exc).__name__,
                }
            )
            return
        for line_no, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception as exc:
                findings.append(
                    {
                        "path": _safe_rel(root, path),
                        "reason": "jsonl_line_unreadable",
                        "line": line_no,
                        "error": type(exc).__name__,
                    }
                )
                continue
            _scan_json_value(payload, root=root, source=path, json_path=f"line[{line_no}]", findings=findings)


def _scan_bytes(root: Path, path: Path, findings: list[dict[str, Any]]) -> None:
    try:
        data = path.read_bytes()
    except Exception as exc:
        findings.append(
            {
                "path": _safe_rel(root, path),
                "reason": "file_unreadable",
                "error": type(exc).__name__,
            }
        )
        return
    for reason, pattern in _BYTE_PATTERNS:
        match = pattern.search(data)
        if match:
            findings.append(
                {
                    "path": _safe_rel(root, path),
                    "reason": reason,
                    "byte_offset": int(match.start()),
                }
            )


def _iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def scan_backup_artifact(backup_dir: Path) -> dict[str, Any]:
    root = Path(backup_dir)
    findings: list[dict[str, Any]] = []
    if not root.exists():
        findings.append({"reason": "backup_dir_missing", "path": str(root)})
        return _report(root, files_scanned=0, text_files_scanned=0, findings=findings)
    if not root.is_dir():
        findings.append({"reason": "backup_dir_not_directory", "path": str(root)})
        return _report(root, files_scanned=0, text_files_scanned=0, findings=findings)
    if not _manifest_path(root).is_file():
        findings.append({"reason": "backup_manifest_missing", "path": "backup_manifest.json"})

    files = _iter_files(root)
    text_count = 0
    for path in files:
        if path.suffix.lower() in _TEXT_SUFFIXES:
            text_count += 1
            _scan_structured_file(root, path, findings)
        _scan_bytes(root, path, findings)
    return _report(root, files_scanned=len(files), text_files_scanned=text_count, findings=findings)


def _report(root: Path, *, files_scanned: int, text_files_scanned: int, findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "created": _utc_now(),
        "read_only": True,
        "backup_dir": str(root),
        "manifest_exists": _manifest_path(root).is_file(),
        "files_scanned": int(files_scanned),
        "text_files_scanned": int(text_files_scanned),
        "finding_count": len(findings),
        "findings": findings,
        "ok": len(findings) == 0,
    }
