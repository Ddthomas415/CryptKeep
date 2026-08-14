from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/SUPPLY_CHAIN_RELEASE_POLICY.md"

CURRENT_BOUNDARY = {
    "Runtime dependencies are pinned through `requirements-pinned.txt`",
    "CI installs pinned runtime dependencies in the main validation workflow",
    "Release workflows already produce artifact hash manifests",
    "unsigned builds remain allowed for current paper/research operation",
}

CAPPED_LIVE_PACKET = {
    "dependency lockfile freshness review",
    "vulnerability audit output or an explicit accepted waiver",
    "final artifact hash manifest",
    "signed/notarized artifact proof if desktop artifacts are part of the live",
    "verification that release/signing secrets are present only in GitHub Actions",
    "a record of the exact Git SHA used for deployment",
}

WAIVER_FIELDS = {
    "package or artifact affected",
    "severity and exploit path",
    "whether the affected code is reachable in paper, shadow, or live mode",
    "compensating controls",
    "expiry date for the waiver",
    "owner responsible for revisiting it",
}

FUTURE_GATES = {
    "`pip-audit` or equivalent advisory audit over pinned requirements",
    "SBOM generation for release artifacts",
    "Hash-locked dependency installs for release jobs",
    "Signed provenance/attestation for release artifacts",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_supply_chain_policy_preserves_current_boundary() -> None:
    text = _normalized(DOC)

    assert "This policy does not add a new CI gate by itself." in text
    for item in CURRENT_BOUNDARY:
        assert item in text
    assert "No hash-locked `--require-hashes` install path is enforced." in text
    assert "No dependency vulnerability audit is a required release gate." in text
    assert "No SBOM is generated as a required artifact." in text


def test_supply_chain_policy_preserves_capped_live_packet_requirements() -> None:
    text = _normalized(DOC)

    assert "Before capped-live approval, the launch packet must include:" in text
    for item in CAPPED_LIVE_PACKET:
        assert item in text
    assert "rather than silently expanding the fast PR path" in text


def test_supply_chain_policy_preserves_waiver_requirements() -> None:
    text = _normalized(DOC)

    assert "A vulnerability or missing verification step may be waived only when" in text
    for field in WAIVER_FIELDS:
        assert field in text
    assert "Waivers must not be indefinite for live/capped-live operation." in text


def test_supply_chain_policy_preserves_incremental_future_gate_rule() -> None:
    text = _normalized(DOC)

    for gate in FUTURE_GATES:
        assert gate in text
    assert "Do not add all four at once." in text
    assert "keep docs-only PR fast paths unchanged unless the branch-protection policy" in text


def test_launch_checklist_links_supply_chain_policy() -> None:
    launch = _text("docs/LAUNCH_CHECKLIST.md")
    ci_docs = _text("docs/CI_GITHUB_ACTIONS.md")
    backlog = _text("REMAINING_TASKS.md")

    assert DOC in launch
    assert DOC in ci_docs
    assert DOC in backlog
    assert (REPO / DOC).is_file()
