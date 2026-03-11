from __future__ import annotations

import scripts.smoke_binance as smoke_binance
import scripts.smoke_coinbase as smoke_coinbase
import scripts.smoke_exchange as smoke_exchange
import scripts.smoke_gateio as smoke_gateio


def test_smoke_exchange_main_calls_runner(monkeypatch, capsys):
    monkeypatch.setattr(
        smoke_exchange,
        "run_exchange_smoke",
        lambda **kwargs: {"ok": True, "kwargs": kwargs, "checks": []},
    )
    rc = smoke_exchange.main(["--exchange", "coinbase", "--symbol", "BTC/USD", "--sandbox"])
    out = capsys.readouterr().out
    assert rc == 0
    assert '"ok": true' in out.lower()


def test_smoke_exchange_main_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(smoke_exchange, "run_exchange_smoke", lambda **kwargs: {"ok": False, "checks": []})
    rc = smoke_exchange.main(["--exchange", "coinbase"])
    assert rc == 2


def test_per_exchange_wrappers_call_exchange_main(monkeypatch):
    calls: list[list[str]] = []

    def _fake_main(argv):
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(smoke_exchange, "main", _fake_main)
    assert smoke_coinbase.main() == 0
    assert smoke_binance.main() == 0
    assert smoke_gateio.main() == 0
    assert calls[0][:2] == ["--exchange", "coinbase"]
    assert calls[1][:2] == ["--exchange", "binance"]
    assert calls[2][:2] == ["--exchange", "gateio"]

