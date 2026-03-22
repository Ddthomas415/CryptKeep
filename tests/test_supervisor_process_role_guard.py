import pytest
from services.process import supervisor_process as mod

def test_start_requires_admin_role() -> None:
    with pytest.raises(PermissionError):
        mod.start(streamlit_cmd=["python", "-V"], watchdog_cmd=["python", "-V"], cwd=mod.data_dir(), current_role="OPERATOR")

def test_stop_requires_admin_role() -> None:
    with pytest.raises(PermissionError):
        mod.stop(current_role="OPERATOR")

def test_clear_stale_requires_admin_role() -> None:
    with pytest.raises(PermissionError):
        mod.clear_stale(current_role="OPERATOR")
