import pytest
from dashboard.services import operator

def test_run_op_requires_operator_role() -> None:
    with pytest.raises(PermissionError):
        operator.run_op(["start", "--name", "tick_publisher"], current_role="VIEWER")

def test_run_repo_script_requires_operator_role() -> None:
    with pytest.raises(PermissionError):
        operator.run_repo_script("scripts/run_crypto_edge_collector_loop.py", current_role="VIEWER")

def test_start_repo_script_background_requires_operator_role() -> None:
    with pytest.raises(PermissionError):
        operator.start_repo_script_background("scripts/run_crypto_edge_collector_loop.py", current_role="VIEWER")
