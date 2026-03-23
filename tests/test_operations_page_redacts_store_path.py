from pathlib import Path

def test_operations_page_does_not_render_store_path() -> None:
    text = Path("dashboard/pages/60_Operations.py").read_text()
    assert "report.get('store_path')" not in text
    assert '"Store: redacted"' in text
