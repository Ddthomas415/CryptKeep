from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_verify_no_direct_create_order_skips_venv_variants() -> None:
    txt = (ROOT / "scripts" / "verify_no_direct_create_order.py").read_text(
        encoding="utf-8", errors="replace"
    )
    assert 'part.startswith(".venv")' in txt
    assert '"tools"' in txt
    assert '"attic"' in txt


def test_repo_doctor_skips_venv_variants_in_samples() -> None:
    txt = (ROOT / "tools" / "repo_doctor.py").read_text(
        encoding="utf-8", errors="replace"
    )
    assert 'part.startswith(".venv")' in txt
    assert 'attic/' in txt
