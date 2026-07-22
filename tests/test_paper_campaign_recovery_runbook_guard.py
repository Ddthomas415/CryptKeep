from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "PAPER_CAMPAIGN_RECOVERY.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8", errors="replace")


def _flat_text() -> str:
    return " ".join(_text().split())


def test_recovery_runbook_has_executable_guard_note() -> None:
    text = _text()

    assert "Executable guard: `tests/test_paper_campaign_recovery_runbook_guard.py`" in text
    assert "operator-facing recovery contract" in text


def test_status_commands_preserve_local_and_hetzner_split() -> None:
    text = _text()

    assert "make status-paper-all" in text
    assert "make status-paper-campaigns" in text
    assert "make status-paper-soak" in text
    assert "make status-paper-hetzner" in text
    assert "configs/paper_evidence_campaigns.laptop.json" in text
    assert "configs/paper_evidence_campaigns.hetzner.example.json" in text
    assert "`es_daily_trend_v1` and `breakout_default` run on the laptop" in text
    assert "`ema_cross_default` is owned by the Hetzner host" in text


def test_restore_and_recover_commands_keep_restart_explicit() -> None:
    text = _flat_text()

    assert "make restore-paper-campaigns" in text
    assert "starts only dead collectors" in text
    assert "run_paper_strategy_evidence_collector.py --daily-loop --detach" in text
    assert "make recover-paper-campaigns" in text
    assert "--restart-unhealthy" in text
    assert "preflight must pass before an alive unhealthy collector is stopped" in text
    assert "The default restore path does not replace live processes." in text


def test_ohlcv_blocked_state_does_not_consume_attempt_budget() -> None:
    text = _flat_text()

    assert "Public-OHLCV campaigns fail closed" in text
    assert "`reason=ohlcv_source_unreachable`" in text
    assert "`retry_budget_consumed=false`" in text
    assert "no campaign attempt starts while the source remains unreachable" in text
    assert "Known source outages do not consume that budget under current code." in text


def test_recovery_attempt_override_is_audit_preserving() -> None:
    text = _flat_text()

    assert "grants exactly one fresh same-day recovery attempt" in text
    assert "`recovery_attempt_override`" in text
    assert "does not erase or rewrite historical session evidence" in text


def test_current_campaign_tables_pin_owned_campaigns() -> None:
    text = _text()

    assert "`es_daily_trend_v1` | `sma_200_trend` | `public_ohlcv_1d`" in text
    assert "`breakout_default` | `breakout_donchian` | `public_ohlcv_5m`" in text
    assert "`ema_cross_default` | `ema_cross` | `public_ohlcv_5m`" in text


def test_safety_boundary_rejects_automatic_os_login_start() -> None:
    text = _flat_text()

    assert "does not automatically start these campaigns at OS login" in text
    assert "without a current operator action" in text
    assert "one explicit, idempotent operation" in text
