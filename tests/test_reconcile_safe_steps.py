from __future__ import annotations

from services.admin import reconcile_safe_steps as rss


def test_run_all_safe_steps_runs_non_destructive_chain(monkeypatch):
    calls: dict[str, object] = {}

    def _journal(venue, symbol=None):
        calls["journal"] = (venue, symbol)
        return {"ok": True, "snapshot_path": "/tmp/journal.json", "counts": {"missing_local": 0}, "signals": {}}

    def _position(venue, symbols=None, mode="spot", require_exchange_ok=True):
        calls["position"] = (venue, symbols, mode, require_exchange_ok)
        return {"ok": True, "snapshot_path": "/tmp/position.json", "mismatch_count": 0}

    monkeypatch.setattr(
        rss,
        "reconcile_journal_vs_exchange",
        _journal,
    )
    monkeypatch.setattr(
        rss,
        "reconcile_positions",
        _position,
    )
    monkeypatch.setattr(rss.wizard_state, "load", lambda: {"step": 1})
    monkeypatch.setattr(rss.wizard_state, "save", lambda st: {"ok": True, "saved_step": st.get("step")})

    out = rss.run_all_safe_steps(venue="coinbase", symbols=["btc/usd"], mode="spot", require_exchange_ok=False)
    assert out["ok"] is True
    assert out["non_destructive"] is True
    assert out["steps"][0]["step"] == "journal_reconcile"
    assert out["steps"][1]["step"] == "position_reconcile"
    assert calls["journal"] == ("coinbase", "BTC/USD")
    assert calls["position"] == ("coinbase", ["BTC/USD"], "spot", False)


def test_run_all_safe_steps_requires_venue():
    out = rss.run_all_safe_steps(venue="", symbols=["BTC/USD"])
    assert out["ok"] is False
    assert out["reason"] == "missing_venue"

def test_run_all_safe_steps_normalizes_multiple_symbols(monkeypatch):
    calls: dict[str, object] = {}

    def _journal(venue, symbol=None):
        calls["journal"] = (venue, symbol)
        return {"ok": True, "snapshot_path": "/tmp/journal.json", "counts": {"missing_local": 0}, "signals": {}}

    def _position(venue, symbols=None, mode="spot", require_exchange_ok=True):
        calls["position"] = (venue, symbols, mode, require_exchange_ok)
        return {"ok": True, "snapshot_path": "/tmp/position.json", "mismatch_count": 0}

    monkeypatch.setattr(rss, "reconcile_journal_vs_exchange", _journal)
    monkeypatch.setattr(rss, "reconcile_positions", _position)
    monkeypatch.setattr(rss.wizard_state, "load", lambda: {"step": 1})
    monkeypatch.setattr(rss.wizard_state, "save", lambda st: {"ok": True, "saved_step": st.get("step")})

    out = rss.run_all_safe_steps(
        venue="coinbase",
        symbols=["btc/usd", "eth/usd"],
        mode="spot",
        require_exchange_ok=False,
    )

    assert out["ok"] is True
    assert calls["journal"] == ("coinbase", "BTC/USD")
    assert calls["position"] == ("coinbase", ["BTC/USD", "ETH/USD"], "spot", False)


def test_run_all_safe_steps_handles_missing_symbols(monkeypatch):
    calls: dict[str, object] = {}

    def _journal(venue, symbol=None):
        calls["journal"] = (venue, symbol)
        return {"ok": True, "snapshot_path": "/tmp/journal.json", "counts": {"missing_local": 0}, "signals": {}}

    def _position(venue, symbols=None, mode="spot", require_exchange_ok=True):
        calls["position"] = (venue, symbols, mode, require_exchange_ok)
        return {"ok": True, "snapshot_path": "/tmp/position.json", "mismatch_count": 0}

    monkeypatch.setattr(rss, "reconcile_journal_vs_exchange", _journal)
    monkeypatch.setattr(rss, "reconcile_positions", _position)
    monkeypatch.setattr(rss.wizard_state, "load", lambda: {"step": 1})
    monkeypatch.setattr(rss.wizard_state, "save", lambda st: {"ok": True, "saved_step": st.get("step")})

    out = rss.run_all_safe_steps(
        venue="coinbase",
        symbols=[],
        mode="spot",
        require_exchange_ok=False,
    )

    assert out["ok"] is True
    assert calls["journal"] == ("coinbase", None)
    assert calls["position"] == ("coinbase", None, "spot", False)

