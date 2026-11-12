env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-probe2.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c '
import pytest

def fingerprint_binding(binding, replacement):
    def probe(archive, monkeypatch):
        from tests.test_runner_decision_capture import make_record, save
        from services.strategies import signal_input_capture as capture
        from services.execution import strategy_runner
        _, _, envelope = save(archive, make_record())
        before = capture._runner_code_identity()
        monkeypatch.setattr(strategy_runner, binding, replacement)
        same = before == capture._runner_code_identity()
        try:
            result = capture.replay_runner_decision(envelope)
        except ValueError as exc:
            assert str(exc) == "runner_code_mismatch"
            return
        assert result["status"] != "decision_match", f"binding={binding}; identity_unchanged={same}; replay={result}"
    probe.__name__ = "fingerprint_"+binding
    return probe

class Probes:
    def pytest_collection_modifyitems(self, items):
        parent = items[0].parent
        tests = [fingerprint_binding("_position_aware_signal_action", lambda *_a, **_kw: "buy"), fingerprint_binding("signal_transition", lambda **kw: {"changed": False})]
        items[:] = [pytest.Function.from_parent(parent,name=f.__name__,callobj=f) for f in tests]
raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", "tests/test_runner_decision_capture.py"],plugins=[Probes()]))
'
