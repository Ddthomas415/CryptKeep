from pathlib import Path

def test_ops_services_do_not_log_raw_exception_text() -> None:
    paths = [
        "services/ops/risk_gate_service.py",
        "services/ops/signal_adapter_service.py",
        "services/analytics/paper_strategy_evidence_service.py",
    ]
    for path in paths:
        text = Path(path).read_text()
        assert 'str(exc)' not in text, path
        assert 'error_type' in text, path
