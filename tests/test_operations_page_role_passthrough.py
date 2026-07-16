from pathlib import Path

def test_operations_page_passes_authenticated_role() -> None:
    text = Path("dashboard/pages/60_Operations.py").read_text()
    needle = 'current_role=str(AUTH_STATE.get("role") or "VIEWER")'
    assert text.count(needle) >= 14


def test_operations_page_strategy_config_saves_are_operator_audited() -> None:
    text = Path("dashboard/pages/60_Operations.py").read_text()
    assert "from services.admin.strategy_config_audit import record_strategy_config_change" in text
    assert text.count("record_strategy_config_change(") == 2
    assert "operations_strategy_params" in text
    assert "operations_strategy_preset:" in text
    assert "rolled back because operator-event " in text
    assert "audit failed:" in text
