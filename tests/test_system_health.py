from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest


def _setup(monkeypatch, tmp_path: Path):
    import services.risk.system_health as sh

    data = tmp_path / "data"
    data.mkdir(parents=True, exist_ok=True)
    db = str(data / "execution.sqlite")

    monkeypatch.setattr(sh, "_data_dir", lambda: data)
    monkeypatch.setattr(sh, "_exec_db", lambda: db)

    return sh, data, db


def _write_flag(path: Path, payload: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("" if payload is None else json.dumps(payload), encoding="utf-8")


def _seed_db(db: str, *, canonical: list[dict], risk: list[dict]) -> None:
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS canonical_fills(
            venue TEXT,
            fill_id TEXT,
            symbol TEXT,
            side TEXT,
            qty REAL,
            price REAL,
            ts TEXT,
            fee_usd REAL,
            realized_pnl_usd REAL,
            client_order_id TEXT,
            order_id TEXT,
            raw_json TEXT,
            created_at TEXT,
            PRIMARY KEY(venue, fill_id)
        );

        CREATE TABLE IF NOT EXISTS risk_daily_fills(
            venue TEXT,
            fill_id TEXT,
            day TEXT,
            created_at TEXT,
            PRIMARY KEY(venue, fill_id)
        );
    """)

    for row in canonical:
        con.execute(
            """
            INSERT OR IGNORE INTO canonical_fills
                (venue, fill_id, symbol, side, qty, price, ts, fee_usd,
                 realized_pnl_usd, client_order_id, order_id, raw_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["venue"],
                row["fill_id"],
                row.get("symbol", "BTC/USD"),
                row.get("side", "buy"),
                row.get("qty", 0.01),
                row.get("price", 60000.0),
                row.get("ts", "2026-04-30T10:00:00Z"),
                row.get("fee_usd", 0.0),
                row.get("realized_pnl_usd", 0.0),
                "",
                "",
                "",
                row.get("created_at", "2026-04-30T10:00:00Z"),
            ),
        )

    for row in risk:
        con.execute(
            """
            INSERT OR IGNORE INTO risk_daily_fills
                (venue, fill_id, day, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                row["venue"],
                row["fill_id"],
                "2026-04-30",
                "2026-04-30T10:00:00Z",
            ),
        )

    con.commit()
    con.close()


def test_healthy_when_no_flags_and_invariant_ok(monkeypatch, tmp_path):
    sh, data, db = _setup(monkeypatch, tmp_path)
    _seed_db(
        db,
        canonical=[{"venue": "coinbase", "fill_id": "f1"}],
        risk=[{"venue": "coinbase", "fill_id": "f1"}],
    )

    assert sh.get_system_health() == {"state": "HEALTHY", "reasons": []}


def test_halt_flag_returns_halted(monkeypatch, tmp_path):
    sh, data, db = _setup(monkeypatch, tmp_path)
    _write_flag(data / "system_halted.flag")

    result = sh.get_system_health()

    assert result["state"] == "HALTED"
    assert any("halted" in reason for reason in result["reasons"])


def test_risk_sink_flag_returns_degraded(monkeypatch, tmp_path):
    sh, data, db = _setup(monkeypatch, tmp_path)
    _write_flag(
        data / "risk_sink_failed.flag",
        {
            "failed_at": time.time(),
            "venue": "coinbase",
            "fill_id": "fill-001",
            "reason": "db_locked",
        },
    )

    result = sh.get_system_health()

    assert result["state"] == "DEGRADED"
    assert any("risk_sink_failed" in reason for reason in result["reasons"])


def test_missing_risk_daily_row_returns_degraded(monkeypatch, tmp_path):
    sh, data, db = _setup(monkeypatch, tmp_path)
    _seed_db(
        db,
        canonical=[{"venue": "coinbase", "fill_id": "missing-risk"}],
        risk=[],
    )

    result = sh.get_system_health()

    assert result["state"] == "DEGRADED"
    assert any("accounting_invariant_violated" in reason for reason in result["reasons"])


def test_enforce_system_health_raises_on_degraded(monkeypatch):
    import services.execution.place_order as po

    monkeypatch.setattr(
        "services.risk.system_health.get_system_health",
        lambda: {"state": "DEGRADED", "reasons": ["test_reason"]},
    )

    with pytest.raises(RuntimeError) as exc_info:
        po._enforce_system_health()

    msg = str(exc_info.value)
    assert "CBP_ORDER_BLOCKED:system_health:DEGRADED" in msg
    assert "test_reason" in msg


def test_enforce_system_health_raises_on_halted(monkeypatch):
    import services.execution.place_order as po

    monkeypatch.setattr(
        "services.risk.system_health.get_system_health",
        lambda: {"state": "HALTED", "reasons": ["operator_halt"]},
    )

    with pytest.raises(RuntimeError) as exc_info:
        po._enforce_system_health()

    assert "CBP_ORDER_BLOCKED:system_health:HALTED" in str(exc_info.value)


def test_enforce_system_health_returns_none_on_healthy(monkeypatch):
    import services.execution.place_order as po

    monkeypatch.setattr(
        "services.risk.system_health.get_system_health",
        lambda: {"state": "HEALTHY", "reasons": []},
    )

    assert po._enforce_system_health() is None


def test_enforce_system_health_fails_closed_on_health_check_error(monkeypatch):
    import services.execution.place_order as po

    def _raise():
        raise RuntimeError("health check exploded")

    monkeypatch.setattr("services.risk.system_health.get_system_health", _raise)

    with pytest.raises(RuntimeError) as exc_info:
        po._enforce_system_health()

    assert "CBP_ORDER_BLOCKED:system_health_check_failed" in str(exc_info.value)
