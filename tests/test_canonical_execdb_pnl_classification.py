from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "architecture" / "canonical_execdb_pnl_classification.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_canonical_execdb_pnl_classification_is_linked_from_indexes() -> None:
    rel = "docs/architecture/canonical_execdb_pnl_classification.md"

    assert rel in _text(REPO / "docs" / "ARCHITECTURE.md")
    assert rel in _text(REPO / "docs" / "REPO_LAYOUT.md")
    assert rel in _text(REPO / "docs" / "CORE.md")
    assert rel in _text(REPO / "docs" / "architecture" / "SYSTEM_BLUEPRINT.md")


def test_canonical_execdb_pnl_classification_preserves_scope_and_rules() -> None:
    text = _text(DOC)
    compact = " ".join(text.split())

    assert "classification record only" in text
    assert "does not change fill accounting, risk gates, promotion gates, live execution, or paper evidence" in compact
    assert "`canonical_fills.realized_pnl_usd`" in text
    assert "`source_supplied_realized_pnl_or_null`" in text
    assert "`canonical_fills.fee_usd`" in text
    assert "`separate_fee_column`" in text
    assert "`risk_daily.realized_pnl`" in text
    assert "`gross_realized_pnl_when_locally_computed`" in text
    assert "`risk_daily.snapshot()[\"pnl\"]`" in text
    assert "`net_realized_after_fees`" in text
    assert "Do not compare canonical ExecDB realized PnL directly with paper-fill" in text


def test_canonical_fill_sink_keeps_source_pnl_boundary_and_risk_daily_net(tmp_path: Path) -> None:
    from services.journal.fill_sink import CanonicalFillSink
    from services.risk.risk_daily import snapshot

    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    assert sink.on_fill(
        {
            "venue": "coinbase",
            "fill_id": "buy-1",
            "symbol": "BTC/USD",
            "side": "buy",
            "qty": 0.01,
            "price": 60000.0,
            "ts": "2026-08-21T00:00:00Z",
            "fee_usd": 1.25,
        }
    ) == {"ok": True}
    assert sink.on_fill(
        {
            "venue": "coinbase",
            "fill_id": "sell-1",
            "symbol": "BTC/USD",
            "side": "sell",
            "qty": 0.01,
            "price": 58000.0,
            "ts": "2026-08-21T01:00:00Z",
            "fee_usd": 1.50,
        }
    ) == {"ok": True}

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = [
        dict(row)
        for row in con.execute(
            """
            SELECT fill_id, fee_usd, realized_pnl_usd
            FROM canonical_fills
            ORDER BY fill_id
            """
        ).fetchall()
    ]
    con.close()

    assert rows == [
        {"fill_id": "buy-1", "fee_usd": 1.25, "realized_pnl_usd": None},
        {"fill_id": "sell-1", "fee_usd": 1.50, "realized_pnl_usd": None},
    ]

    snap = snapshot(exec_db=db)
    assert snap["realized_pnl"] == pytest.approx(-20.0)
    assert snap["fees"] == pytest.approx(2.75)
    assert snap["pnl"] == pytest.approx(-22.75)
