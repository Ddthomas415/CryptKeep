from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import run_bot_safe


def test_pf_get_supports_dict_and_object() -> None:
    assert run_bot_safe._pf_get({"ok": True}, "ok") is True
    assert run_bot_safe._pf_get(SimpleNamespace(ok=False), "ok") is False
    assert run_bot_safe._pf_get({}, "missing", "fallback") == "fallback"


def test_main_exits_when_preflight_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        run_bot_safe,
        "_invoke_preflight",
        lambda *, venue, symbols: {"ok": False, "dry_run": True, "checks": ["blocked"]},
    )
    monkeypatch.setattr(run_bot_safe, "_start_strategy_runner", lambda: (_ for _ in ()).throw(AssertionError("runner should not start")))

    with pytest.raises(SystemExit) as excinfo:
        run_bot_safe.main(["--venue", "coinbase", "--symbols", "BTC/USD"])

    assert excinfo.value.code == 2


def test_main_starts_real_strategy_runner_path(monkeypatch) -> None:
    monkeypatch.setattr(
        run_bot_safe,
        "_invoke_preflight",
        lambda *, venue, symbols: {"ok": True, "dry_run": False, "checks": []},
    )
    monkeypatch.setattr(run_bot_safe, "_start_strategy_runner", lambda: 17)

    out = run_bot_safe.main(["--venue", "coinbase", "--symbols", "BTC/USD,ETH/USD"])

    assert out == 17
