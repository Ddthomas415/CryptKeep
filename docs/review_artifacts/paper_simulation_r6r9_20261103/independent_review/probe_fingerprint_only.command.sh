env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-probe.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c '
import pytest

def loaded_runner_adapter_change(archive, monkeypatch):
    from tests.test_runner_decision_capture import make_record, save
    from services.strategies import signal_input_capture as capture
    from services.execution import strategy_runner
    _, _, envelope = save(archive, make_record())
    before = capture._runner_code_identity()
    monkeypatch.setattr(strategy_runner, "_position_aware_signal_action", lambda *_a, **_kw: "buy")
    after = capture._runner_code_identity()
    assert before != after, "loaded decision adapter changed without changing implementation fingerprint"
    with pytest.raises(ValueError, match="runner_code_mismatch"):
        capture.replay_runner_decision(envelope)

class Probes:
    def pytest_collection_modifyitems(self, items):
        parent = items[0].parent
        items[:] = [pytest.Function.from_parent(parent, name="loaded_runner_adapter_change", callobj=loaded_runner_adapter_change)]
raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", "tests/test_runner_decision_capture.py"], plugins=[Probes()]))
'
