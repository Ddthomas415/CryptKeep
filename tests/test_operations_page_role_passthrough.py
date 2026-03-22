from pathlib import Path

def test_operations_page_passes_authenticated_role() -> None:
    text = Path("dashboard/pages/60_Operations.py").read_text()
    needle = 'current_role=str(AUTH_STATE.get("role") or "VIEWER")'
    assert text.count(needle) >= 14
