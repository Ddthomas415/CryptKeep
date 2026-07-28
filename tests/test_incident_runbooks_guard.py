from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "RUNBOOKS.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8", errors="replace")


def _flat_text() -> str:
    return " ".join(_text().split())


def test_runbooks_document_has_executable_guard_note() -> None:
    text = _text()

    assert "Executable guard: `tests/test_incident_runbooks_guard.py`" in text
    assert "halt-first/resume-later boundaries" in text


def test_severity_matrix_preserves_capital_risk_boundaries() -> None:
    text = _flat_text()

    assert "## Severity Matrix" in text
    assert "**SEV-1** | Live capital at risk." in text
    assert "Immediate | Runbook R1" in text
    assert "**SEV-2** | Live trading halted by system. No capital at risk." in text
    assert "Within 15 minutes | Runbook R2" in text
    assert "**SEV-3** | Degraded operation. Paper mode only or informational." in text
    assert "Within 1 hour | Runbook R3" in text


def test_escalation_rules_keep_halt_before_investigation() -> None:
    text = _text()

    assert "SEV-1: Do not investigate before halting. Halt first, investigate after." in text
    assert "SEV-2: Do not resume without completing the relevant runbook checklist." in text
    assert "SEV-3: Document the issue before fixing. Do not rush." in text
    assert "Downgrade only after confirming the capital risk has been eliminated." in text
    assert "All SEV-1 events require a written post-incident summary within 24 hours." in text


def test_r1_uncontrolled_orders_forces_halt_and_exchange_verification() -> None:
    text = _flat_text()

    assert "## R1 — Executor won't halt / orders uncontrolled" in text
    assert "Step 1 — Force halt via CLI (do this first, before anything else)" in text
    assert "disable_live_now" in text
    assert "python3 scripts/stop_bot.py --all" in text
    assert "pkill -f \"live_executor\"" in text
    assert "Verify halt at exchange level" in text
    assert "Cancel any open orders that should not be there." in text
    assert "Do not resume until root cause is identified" in text


def test_r2_resume_requires_state_reconcile_and_guarded_resume() -> None:
    text = _flat_text()

    assert "## R2 — Live trading halted by system, needs operator resolution" in text
    assert "from services.admin.live_disable_wizard import status" in text
    assert "from services.admin.state_report import get_state_report" in text
    assert "Resolve any stuck intents" in text
    assert "Log into Coinbase/Binance" in text
    assert "from services.admin.resume_gate import resume_if_safe" in text
    assert "If resume is blocked, the output will show the reason." in text
    assert "Monitor for one full cycle after resume" in text


def test_r3_degraded_paper_response_stays_informational_and_escalates_on_recurrence() -> None:
    text = _flat_text()

    assert "## R3 — Degraded operation (paper mode / informational)" in text
    assert "Paper fill rate dropped. Evidence collector stopped." in text
    assert "from services.preflight.preflight import run_preflight" in text
    assert "python3 scripts/bot_status.py" in text
    assert "from services.admin.system_diagnostics import run_diagnostics" in text
    assert "If the same SEV-3 issue recurs within 24 hours, escalate to SEV-2." in text


def test_duplicate_order_and_config_change_runbooks_start_with_halt() -> None:
    text = _flat_text()

    assert "## R4 — Duplicate order suspected" in text
    assert "Step 1 — Halt immediately See R1 Step 1." in text
    assert "Check exchange directly" in text
    assert "Cancel any duplicate open orders immediately." in text
    assert "## R5 — Config change caused unexpected behavior" in text
    assert "git diff HEAD~1 config/" in text
    assert "git revert HEAD" in text
    assert "Run preflight to confirm revert is clean" in text
    assert "Resume only after preflight passes" in text


def test_post_incident_summary_template_preserves_required_fields() -> None:
    text = _text()

    for field in (
        "Date and time of incident:",
        "Severity:",
        "Duration (from first alert to resolution):",
        "What capital was at risk (if any):",
        "How was it detected:",
        "How was it halted:",
        "Root cause:",
        "Fix applied:",
        "How to prevent recurrence:",
        "Git commit(s) that fix the issue:",
        "Reviewed by:",
        "Date of review:",
    ):
        assert field in text
