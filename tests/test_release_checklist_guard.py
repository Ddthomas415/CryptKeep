from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def test_release_checklist_preserves_root_entrypoint_and_guard():
    text = _read("docs/RELEASE_CHECKLIST.md")
    wrapper = _read("scripts/release_checklist.py")

    assert "python scripts/release_checklist.py [options]" in text
    assert "tests/test_release_checklist_guard.py" in text
    assert "root compatibility entrypoint" in text
    assert 'run_module("scripts.release.release_checklist", run_name="__main__")' in wrapper


def test_release_checklist_preserves_common_command_surface():
    text = _read("docs/RELEASE_CHECKLIST.md")

    for command in (
        "python scripts/release_checklist.py --dry-run",
        "python scripts/release_checklist.py --bump patch --sync-requires",
        "python scripts/release_checklist.py --pyinstaller",
        "python scripts/release_checklist.py --briefcase",
        "python scripts/release_checklist.py --bump patch --sync-requires --briefcase",
    ):
        assert command in text


def test_release_checklist_preserves_manifest_outputs():
    text = _read("docs/RELEASE_CHECKLIST.md")

    assert "Writes a manifest JSON under `releases/`" in text
    for field in (
        "build metadata",
        "step results (stdout/stderr truncated)",
        "artifact SHA-256 hashes for everything in dist/, build/, data/reconcile_reports/",
    ):
        assert field in text


def test_release_checklist_preserves_opt_in_signing_boundary():
    text = _read("docs/RELEASE_CHECKLIST.md")

    assert "Signing is FAIL-CLOSED and requires env vars. Nothing is stored in the repo." in text
    for env_name in (
        "RELEASE_SIGN_WINDOWS",
        "SIGN_PFX_PATH",
        "SIGN_PFX_PASSWORD",
        "SIGN_CERT_THUMBPRINT",
        "SIGN_TIMESTAMP_URL",
        "RELEASE_NOTARIZE_MAC",
        "MAC_SIGN_IDENTITY",
        "MAC_BUNDLE_ID",
        "MAC_NOTARY_PROFILE",
    ):
        assert env_name in text


def test_release_checklist_is_listed_in_script_index():
    scripts = _read("scripts/SCRIPTS.md")

    assert "`release_checklist.py` — release checklist wrapper." in scripts
    assert "`generate_release_notes.py` — release-notes generator." in scripts
