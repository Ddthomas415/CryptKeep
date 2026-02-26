from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_mode_contract_consistency():
    alignment = _read("scripts/check_repo_alignment.py")
    assert "\"mode\": \"list-tests\"" in alignment
    assert "mode = \"full_skip_guards\" if skip_guards else \"full\"" in alignment

    validate = _read("scripts/validate.py")
    assert "mode = \"quick\" if args.quick else \"full\"" in validate

    pre = _read("scripts/pre_release_sanity.py")
    assert "\"quick\" if all(skip_flags) else (\"full\" if not any(skip_flags) else \"custom\")" in pre
