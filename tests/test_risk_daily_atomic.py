from __future__ import annotations

from services.risk.risk_daily import RiskDailyDB, record_order_attempt


def test_apply_fill_once_updates_rollup_once(tmp_path):
    db = RiskDailyDB(str(tmp_path / "execution.sqlite"))

    assert db.apply_fill_once(
        venue="coinbase",
        fill_id="fill-1",
        realized_pnl_usd=-12.5,
        fee_usd=1.25,
    ) is True
    assert db.apply_fill_once(
        venue="coinbase",
        fill_id="fill-1",
        realized_pnl_usd=-12.5,
        fee_usd=1.25,
    ) is False

    row = db.get()
    assert row["realized_pnl_usd"] == -12.5
    assert row["fees_usd"] == 1.25


def test_apply_fill_once_rolls_back_dedupe_when_rollup_fails(tmp_path):
    db = RiskDailyDB(str(tmp_path / "execution.sqlite"))

    def broken_rollup(*_args, **_kwargs):
        raise RuntimeError("boom")

    db._apply_pnl_conn = broken_rollup  # type: ignore[method-assign]

    assert db.apply_fill_once(
        venue="coinbase",
        fill_id="fill-rollback",
        realized_pnl_usd=-20.0,
        fee_usd=2.0,
    ) is False

    with db._conn() as con:
        fills = con.execute(
            "SELECT COUNT(*) FROM risk_daily_fills WHERE venue=? AND fill_id=?",
            ("coinbase", "fill-rollback"),
        ).fetchone()[0]
        rows = con.execute("SELECT COUNT(*) FROM risk_daily").fetchone()[0]

    assert fills == 0
    assert rows == 0


def test_risk_daily_increment_helpers_are_additive(tmp_path):
    exec_db = str(tmp_path / "execution.sqlite")
    db = RiskDailyDB(exec_db)

    assert db.incr_trades(2) == 2
    assert db.incr_trades(3) == 5
    row = db.add_pnl(realized_pnl_usd=-3.0, fee_usd=0.5)
    assert row["realized_pnl_usd"] == -3.0
    assert row["fees_usd"] == 0.5

    record_order_attempt(notional_usd=25.0, exec_db=exec_db)
    row = db.get()
    assert row["trades"] == 6
    assert row["notional_usd"] == 25.0
