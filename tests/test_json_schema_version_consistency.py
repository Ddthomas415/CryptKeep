from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_schema_version_consistency():
    targets = [
        "scripts/check_repo_alignment.py",
        "scripts/validate.py",
        "scripts/pre_release_sanity.py",
    ]
    for path in targets:
        txt = _read(path)
        assert "SCHEMA_VERSION = 1" in txt, path
        assert "\"schema_version\": SCHEMA_VERSION" in txt, path
