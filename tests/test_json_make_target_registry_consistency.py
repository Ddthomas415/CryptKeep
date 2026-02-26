from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_make_target_registry_consistency():
    mk = _read("Makefile")
    rd = _read("README.md")
    wf = _read("docs/REPO_ALIGNMENT_WORKFLOW.md")

    targets = [
        "check-alignment-list-json",
        "check-alignment-json",
        "check-alignment-json-fast",
        "validate-json-quick",
        "validate-json-fast",
        "validate-json",
        "pre-release-sanity-json-quick",
        "pre-release-sanity-json-fast",
    ]

    for target in targets:
        assert f"{target}:" in mk, target
        assert f"make {target}" in rd, target
        assert f"make {target}" in wf, target
