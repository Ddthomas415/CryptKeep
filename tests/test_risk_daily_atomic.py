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


def test_add_pnl_rejects_nonfinite_values_without_mutation(tmp_path):
    exec_db = str(tmp_path / "execution.sqlite")
    db = RiskDailyDB(exec_db)

    try:
        db.add_pnl(realized_pnl_usd=float("nan"), fee_usd=0.5)
    except ValueError as exc:
        assert "invalid_numeric:realized_pnl_usd" in str(exc)
    else:
        raise AssertionError("add_pnl should reject non-finite realized PnL")

    row = db.get()
    assert row["realized_pnl_usd"] == 0.0
    assert row["fees_usd"] == 0.0

    try:
        db.add_pnl(realized_pnl_usd=-1.0, fee_usd=float("inf"))
    except ValueError as exc:
        assert "invalid_numeric:fee_usd" in str(exc)
    else:
        raise AssertionError("add_pnl should reject non-finite fee")

    row = db.get()
    assert row["realized_pnl_usd"] == 0.0
    assert row["fees_usd"] == 0.0


def test_apply_fill_once_rejects_nonfinite_values_and_rolls_back_dedupe(tmp_path):
    db = RiskDailyDB(str(tmp_path / "execution.sqlite"))

    assert db.apply_fill_once(
        venue="coinbase",
        fill_id="fill-bad",
        realized_pnl_usd=float("nan"),
        fee_usd=0.5,
    ) is False

    with db._conn() as con:
        fills = con.execute(
            "SELECT COUNT(*) FROM risk_daily_fills WHERE venue=? AND fill_id=?",
            ("coinbase", "fill-bad"),
        ).fetchone()[0]
        rows = con.execute("SELECT COUNT(*) FROM risk_daily").fetchone()[0]

    assert fills == 0
    assert rows == 0


def test_record_order_attempt_ignores_nonfinite_notional_without_mutation(tmp_path):
    exec_db = str(tmp_path / "execution.sqlite")
    db = RiskDailyDB(exec_db)
    db.get()

    record_order_attempt(notional_usd=float("nan"), exec_db=exec_db)

    row = db.get()
    assert row["trades"] == 0
    assert row["notional_usd"] == 0.0


def test_realized_today_usd_is_net_of_fees_for_daily_loss(tmp_path):
    db = RiskDailyDB(str(tmp_path / "execution.sqlite"))
    db.add_pnl(realized_pnl_usd=-100.0, fee_usd=5.0)

    assert db.realized_today_usd() == -105.0


def test_snapshot_marks_corrupt_numeric_fields_and_realized_today_fails_closed(tmp_path):
    from services.risk.risk_daily import snapshot

    exec_db = str(tmp_path / "execution.sqlite")
    db = RiskDailyDB(exec_db)
    db.get()

    with db._conn() as con:
        con.execute(
            """
            UPDATE risk_daily
            SET trades='nan',
                realized_pnl_usd='nan',
                fees_usd='not-a-number',
                notional_usd='inf'
            """
        )

    snap = snapshot(exec_db=exec_db)

    assert snap["risk_daily_corrupt"] is True
    assert set(snap["risk_daily_corrupt_fields"]) == {
        "trades",
        "realized_pnl_usd",
        "fees_usd",
        "notional_usd",
    }
    assert snap["trades"] == 0
    assert snap["pnl"] == 0.0

    try:
        db.realized_today_usd()
    except ValueError as exc:
        assert "risk_daily_corrupt" in str(exc)
    else:
        raise AssertionError("realized_today_usd should fail closed on corrupt risk_daily")
