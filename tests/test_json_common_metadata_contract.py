from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_common_metadata_contract():
    targets = [
        "scripts/check_repo_alignment.py",
        "scripts/validate.py",
        "scripts/pre_release_sanity.py",
    ]
    required_tokens = [
        "\"schema_version\": SCHEMA_VERSION",
        "\"mode\"",
        "\"ok\"",
        "\"started_at\"",
        "\"finished_at\"",
        "\"duration_seconds\"",
    ]
    for path in targets:
        txt = _read(path)
        for token in required_tokens:
            assert token in txt, f"{path}: missing {token}"
