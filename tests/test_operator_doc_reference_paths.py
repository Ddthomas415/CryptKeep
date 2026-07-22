from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OPERATOR_DOCS = (
    "docs/GOLDEN_PATH.md",
    "docs/RUNBOOKS.md",
    "docs/PAPER_CAMPAIGN_RECOVERY.md",
    "docs/EVIDENCE_MODEL.md",
    "docs/LAUNCH_CHECKLIST.md",
    "docs/RELEASE_CHECKLIST.md",
)

REPO_PATH_RE = re.compile(
    r"(?P<path>"
    r"docs/[A-Za-z0-9_./-]+\.md|"
    r"scripts/[A-Za-z0-9_./-]+\.py|"
    r"configs/[A-Za-z0-9_./-]+\.(?:json|yaml|example\.json)"
    r")"
)


def _referenced_repo_paths(doc_rel: str) -> set[str]:
    text = (ROOT / doc_rel).read_text(encoding="utf-8", errors="replace")
    return {match.group("path") for match in REPO_PATH_RE.finditer(text)}


def test_operator_docs_exist() -> None:
    for doc_rel in OPERATOR_DOCS:
        assert (ROOT / doc_rel).is_file(), doc_rel


def test_operator_docs_do_not_reference_missing_repo_paths() -> None:
    missing: list[str] = []

    for doc_rel in OPERATOR_DOCS:
        for ref in sorted(_referenced_repo_paths(doc_rel)):
            if not (ROOT / ref).is_file():
                missing.append(f"{doc_rel} -> {ref}")

    assert not missing, "Missing operator-doc repo references:\n" + "\n".join(missing)


def test_operator_docs_still_cover_core_command_and_policy_surfaces() -> None:
    refs_by_doc = {doc_rel: _referenced_repo_paths(doc_rel) for doc_rel in OPERATOR_DOCS}

    assert "scripts/check_promotion_gates.py" in refs_by_doc["docs/GOLDEN_PATH.md"]
    assert "scripts/run_paper_strategy_evidence_collector.py" in refs_by_doc["docs/GOLDEN_PATH.md"]
    assert "docs/EVIDENCE_MODEL.md" in refs_by_doc["docs/GOLDEN_PATH.md"]
    assert "docs/PAPER_CAMPAIGN_RECOVERY.md" in refs_by_doc["docs/GOLDEN_PATH.md"]
    assert "scripts/restore_paper_campaigns.py" in refs_by_doc["docs/PAPER_CAMPAIGN_RECOVERY.md"]
    assert "configs/paper_evidence_campaigns.laptop.json" in refs_by_doc["docs/PAPER_CAMPAIGN_RECOVERY.md"]
    assert "docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md" in refs_by_doc["docs/RUNBOOKS.md"]
    assert "docs/SINGLE_OPERATOR_CONTINUITY.md" in refs_by_doc["docs/RUNBOOKS.md"]
    assert "scripts/release_checklist.py" in refs_by_doc["docs/RELEASE_CHECKLIST.md"]
