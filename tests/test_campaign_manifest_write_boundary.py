from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_active_paper_campaign_manifests_are_only_written_by_governed_writer() -> None:
    """Active paper-campaign manifest writes must stay behind the audit helper."""

    scanned_roots = [ROOT / "dashboard", ROOT / "scripts", ROOT / "services"]
    allowed = {
        Path("services/admin/campaign_manifest_audit.py"),
        Path("scripts/update_paper_campaign_manifest.py"),
    }
    manifest_tokens = {
        "paper_evidence_campaigns.json",
        "paper_evidence_campaigns.laptop.json",
        "paper_evidence_campaigns.hetzner.example.json",
    }
    write_tokens = {
        ".write_text(",
        ".open(\"w\"",
        ".open('w'",
        "open(",
        "os.replace(",
    }

    violations: list[str] = []
    for scan_root in scanned_roots:
        for path in sorted(scan_root.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if not any(token in text for token in manifest_tokens):
                continue
            if any(token in text for token in write_tokens):
                violations.append(str(rel))

    assert violations == []
