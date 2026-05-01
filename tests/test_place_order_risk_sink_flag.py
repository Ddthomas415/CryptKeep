from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


def _write_flag(flag: Path, payload: dict) -> None:
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(json.dumps(payload), encoding="utf-8")


def _valid_payload(
    *,
    venue: str = "coinbase",
    fill_id: str = "fill-001",
    failed_at: float | None = None,
    reason: str = "OperationalError:database is locked",
) -> dict:
    return {
        "failed_at": failed_at if failed_at is not None else time.time(),
        "venue": venue,
        "fill_id": fill_id,
        "reason": reason,
    }


def test_no_flag_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    from services.execution.place_order import _check_risk_sink_flag

    assert _check_risk_sink_flag() is None


def test_valid_flag_raises_order_blocked(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    flag = tmp_path / "data" / "risk_sink_failed.flag"
    _write_flag(flag, _valid_payload(venue="coinbase", fill_id="fill-blocked-001"))

    from services.execution.place_order import _check_risk_sink_flag

    with pytest.raises(RuntimeError) as exc_info:
        _check_risk_sink_flag()

    msg = str(exc_info.value)
    assert "CBP_ORDER_BLOCKED:risk_daily_update_failed" in msg
    assert "coinbase" in msg
    assert "fill-blocked-001" in msg


def test_corrupt_flag_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    flag = tmp_path / "data" / "risk_sink_failed.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text("{this is not valid json!!!", encoding="utf-8")

    from services.execution.place_order import _check_risk_sink_flag

    with pytest.raises(RuntimeError) as exc_info:
        _check_risk_sink_flag()

    assert "CBP_ORDER_BLOCKED:risk_sink_flag_unreadable" in str(exc_info.value)


def test_empty_flag_file_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    flag = tmp_path / "data" / "risk_sink_failed.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_bytes(b"")

    from services.execution.place_order import _check_risk_sink_flag

    with pytest.raises(RuntimeError) as exc_info:
        _check_risk_sink_flag()

    assert "CBP_ORDER_BLOCKED" in str(exc_info.value)


def test_stale_flag_still_blocks_orders(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    seven_days_ago = time.time() - (7 * 24 * 3600)
    flag = tmp_path / "data" / "risk_sink_failed.flag"
    _write_flag(
        flag,
        _valid_payload(
            venue="coinbase",
            fill_id="fill-stale-001",
            failed_at=seven_days_ago,
            reason="stale_test",
        ),
    )

    from services.execution.place_order import _check_risk_sink_flag

    with pytest.raises(RuntimeError) as exc_info:
        _check_risk_sink_flag()

    msg = str(exc_info.value)
    assert "CBP_ORDER_BLOCKED" in msg
    assert "risk_daily_update_failed" in msg


def test_flag_fields_appear_in_error_message(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    failed_at = time.time() - 42.0
    flag = tmp_path / "data" / "risk_sink_failed.flag"
    _write_flag(
        flag,
        _valid_payload(
            venue="testexchange",
            fill_id="fill-trace-999",
            failed_at=failed_at,
            reason="db_locked",
        ),
    )

    from services.execution.place_order import _check_risk_sink_flag

    with pytest.raises(RuntimeError) as exc_info:
        _check_risk_sink_flag()

    msg = str(exc_info.value)
    assert "testexchange" in msg
    assert "fill-trace-999" in msg
