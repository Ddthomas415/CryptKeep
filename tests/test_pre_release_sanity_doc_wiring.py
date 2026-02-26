from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pre_release_sanity_doc_mentions_alignment_gate_and_skip_ruff():
    txt = (ROOT / "docs" / "PRE_RELEASE_SANITY.md").read_text(encoding="utf-8", errors="replace")
    assert "scripts/check_repo_alignment.py" in txt
    assert "--skip-ruff" in txt
    assert "--json" in txt
    assert "schema_version" in txt
    assert "mode" in txt
    assert "quick" in txt
    assert "full" in txt
    assert "custom" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1" in txt
    assert "started_at" in txt
    assert "finished_at" in txt
    assert "duration_seconds" in txt
