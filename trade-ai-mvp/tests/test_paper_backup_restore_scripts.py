from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_paper_backup_script_contains_required_tables():
    script = (ROOT / "scripts" / "paper_backup.sh").read_text()
    assert "--table=paper_orders" in script
    assert "--table=paper_fills" in script
    assert "--table=paper_positions" in script
    assert "--table=paper_balances" in script
    assert "--table=paper_equity_curve" in script
    assert "--table=paper_performance_rollups" in script


def test_paper_restore_script_enforces_input_and_psql_restore():
    script = (ROOT / "scripts" / "paper_restore.sh").read_text()
    assert "usage:" in script
    assert "ON_ERROR_STOP=1" in script
    assert "docker compose exec -T postgres psql" in script
