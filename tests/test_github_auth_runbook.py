from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "GITHUB_AUTH_RUNBOOK.md"


def _flat() -> str:
    return " ".join(DOC.read_text(encoding="utf-8", errors="replace").split())


def test_github_auth_runbook_pins_https_recovery_sequence() -> None:
    text = _flat()

    assert "Use HTTPS for this repo unless a separate operator decision switches the host to SSH." in text
    assert "gh auth status" in text
    assert "gh auth login --git-protocol https --web" in text
    assert "gh auth setup-git" in text
    assert "gh auth logout --hostname github.com" in text


def test_github_auth_runbook_keeps_token_handling_out_of_repo_and_chat() -> None:
    text = _flat()

    assert "Do not paste GitHub tokens into chat, docs, work logs, commits, screenshots" in text
    assert "Do not store tokens in this repository or under `.cbp_state/`." in text
    assert "Prefer browser login for local interactive recovery." in text
    assert "never into Codex/chat" in text


def test_github_auth_runbook_separates_local_gh_from_codex_connector() -> None:
    text = _flat()

    assert "ChatGPT Codex Connector/GitHub app and the local `gh` CLI as separate auth surfaces" in text
    assert "Fixing one does not prove the other is authenticated." in text
    assert "not evidence that a repo patch is wrong" in text


def test_github_auth_runbook_does_not_authorize_publish_shortcuts() -> None:
    text = _flat()

    for forbidden in (
        "force-pushing over another branch without an explicit operator instruction",
        "bypassing branch protection",
        "merging with failing checks unless explicitly accepted",
        "changing secrets, GitHub app permissions, or organization policy",
        "changing repo code to work around a local credential problem",
    ):
        assert forbidden in text


def test_github_auth_runbook_defines_verification_and_stop_conditions() -> None:
    text = _flat()

    assert "gh repo view --json nameWithOwner,url" in text
    assert "Do not treat this as permanent." in text
    assert "the intended repository or account differs from `Ddthomas415/CryptKeep`" in text


def test_github_auth_runbook_defines_hetzner_pull_auth_boundary() -> None:
    text = _flat()

    assert "Hetzner checkout sync is a separate auth surface from the local laptop `gh` session." in text
    assert "read-only deploy key" in text
    assert "Do not copy a personal GitHub CLI token or browser token to Hetzner." in text
    assert "Do not enable deploy-key write access." in text
    assert "switching the Hetzner repo remote to SSH" in text
