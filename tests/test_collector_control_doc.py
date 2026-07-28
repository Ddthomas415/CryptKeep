from __future__ import annotations

from pathlib import Path

from dashboard.services import operator


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_CONTROL = ROOT / "docs" / "COLLECTOR_CONTROL.md"


def _flat() -> str:
    return " ".join(COLLECTOR_CONTROL.read_text(encoding="utf-8", errors="replace").split())


def test_collector_control_doc_uses_existing_dashboard_script_path() -> None:
    text = _flat()
    script = operator.CRYPTO_EDGE_COLLECTOR_SCRIPT

    assert script == "scripts/data/run_crypto_edge_collector_loop.py"
    assert (ROOT / script).is_file()
    assert script in text
    assert "scripts/run_crypto_edge_collector_loop.py" not in text


def test_collector_control_doc_pins_dashboard_control_surface() -> None:
    text = _flat()

    assert "dashboard.services.operator.start_crypto_edge_collector_loop(...)" in text
    assert "dashboard.services.operator.stop_crypto_edge_collector_loop(...)" in text
    assert "services.analytics.crypto_edge_collector_service.load_runtime_status()" in text
    assert "OPERATOR users" in text
    assert "read-only crypto structural-edge collector loop" in text


def test_collector_control_doc_pins_boundaries() -> None:
    text = _flat()

    assert "does NOT replace existing paper evidence collectors" in text
    assert "reviewed systemd/timer deployment paths" in text
    assert "this collector is read-only research infrastructure" in text
    assert "dashboard controls require OPERATOR role" in text
    assert "missing script paths must fail closed" in text
