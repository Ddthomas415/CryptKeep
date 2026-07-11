from __future__ import annotations

import json
from pathlib import Path

from scripts.compat import run_intent_consumer as compat


def test_legacy_compat_run_refuses_with_stable_reason(capsys):
    rc = compat.main(["run", "--json"])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out == {
        "ok": False,
        "reason": "legacy_intent_consumer_retired",
        "canonical_entrypoint": "scripts/run_intent_consumer_safe.py",
    }


def test_legacy_compat_run_does_not_import_run_forever():
    assert not hasattr(compat, "run_forever")


def test_legacy_compat_stop_remains_available(monkeypatch, capsys):
    monkeypatch.setattr(compat, "_request_stop", lambda: {"ok": True, "stopped": True})

    rc = compat.main(["stop"])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out == {"ok": True, "stopped": True}


def test_canonical_safe_wrapper_uses_live_consumer_not_legacy_consumer():
    source = Path("scripts/run_intent_consumer_safe.py").read_text(encoding="utf-8")

    assert "scripts.live.run_live_intent_consumer" in source
    assert "services.execution.intent_consumer" not in source
