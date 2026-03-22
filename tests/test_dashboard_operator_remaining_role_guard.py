import pytest
from dashboard.services import operator

def test_start_crypto_edge_collector_loop_requires_operator() -> None:
    with pytest.raises(PermissionError):
        operator.start_crypto_edge_collector_loop(interval_sec=30, current_role="VIEWER")

def test_stop_crypto_edge_collector_loop_requires_operator() -> None:
    with pytest.raises(PermissionError):
        operator.stop_crypto_edge_collector_loop(current_role="VIEWER")

def test_run_full_system_diagnostics_requires_operator() -> None:
    with pytest.raises(PermissionError):
        operator.run_full_system_diagnostics(current_role="VIEWER")

def test_export_diagnostics_bundle_requires_operator() -> None:
    with pytest.raises(PermissionError):
        operator.export_diagnostics_bundle(current_role="VIEWER")
