from pathlib import Path


def test_governance_doc_has_canonical_metadata():
    p = Path("docs/governance/governance_signoff.md")
    text = p.read_text(encoding="utf-8")

    assert p.exists()
    assert "Version:" in text
    assert "Status: Frozen" in text
    assert "Owner:" in text
    assert "Effective Date:" in text
