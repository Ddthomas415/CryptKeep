from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"

OPERATOR_DOCS = (
    "README.md",
    "scripts/SCRIPTS.md",
    "docs/GOLDEN_PATH.md",
    "docs/PAPER_CAMPAIGN_RECOVERY.md",
    "docs/RUNBOOKS.md",
    "docs/LAUNCH_CHECKLIST.md",
    "docs/RELEASE_CHECKLIST.md",
)

MAKE_COMMAND_RE = re.compile(r"(?<![\w.-])make[ \t]+(?P<target>[A-Za-z0-9_.-]+)")
MAKE_TARGET_RE = re.compile(r"^(?P<target>[A-Za-z0-9_.-]+):", re.MULTILINE)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def _make_targets() -> set[str]:
    return {match.group("target") for match in MAKE_TARGET_RE.finditer(MAKEFILE.read_text(encoding="utf-8", errors="replace"))}


def _documented_make_commands(doc_rel: str) -> set[str]:
    return {match.group("target") for match in MAKE_COMMAND_RE.finditer(_read(doc_rel))}


def test_operator_docs_only_reference_existing_make_targets() -> None:
    known_targets = _make_targets()
    missing: list[str] = []

    for doc_rel in OPERATOR_DOCS:
        for target in sorted(_documented_make_commands(doc_rel)):
            if target not in known_targets:
                missing.append(f"{doc_rel} -> make {target}")

    assert not missing, "Missing Makefile targets referenced by operator docs:\n" + "\n".join(missing)


def test_operator_docs_still_reference_core_make_targets() -> None:
    documented = set().union(*(_documented_make_commands(doc_rel) for doc_rel in OPERATOR_DOCS))

    for target in (
        "status-paper-all",
        "status-paper-soak",
        "status-paper-hetzner",
        "restore-paper-campaigns",
        "recover-paper-campaigns",
        "check-gates",
        "check-gates-json",
        "paper-run",
        "paper-status",
        "paper-stop-now",
        "validate",
        "pre-release-sanity",
    ):
        assert target in documented
