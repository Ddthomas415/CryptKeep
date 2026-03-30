import pytest
import scripts.run_bot_safe as run_bot_safe


def test_main_requires_venue_and_symbols():
    with pytest.raises(SystemExit) as exc:
        run_bot_safe.main([])
    assert exc.value.code == 2


def test_main_accepts_explicit_venue_and_symbols(monkeypatch):
    monkeypatch.setattr(run_bot_safe, "_invoke_preflight", lambda venue, symbols: {"ok": True, "dry_run": True, "checks": []})
    monkeypatch.setattr(run_bot_safe, "_start_strategy_runner", lambda: 0)
    rc = run_bot_safe.main(["--venue", "coinbase", "--symbols", "BTC/USD"])
    assert rc == 0
