from __future__ import annotations

import json

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


def test_smoke_exchange_main_writes_evidence(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        smoke_exchange,
        "run_exchange_smoke",
        lambda **kwargs: {
            "ok": True,
            "exchange": kwargs["exchange_id"],
            "symbol": kwargs["symbol"],
            "sandbox": kwargs["sandbox"],
            "checks": [{"name": "build_exchange", "ok": True}],
        },
    )

    rc = smoke_exchange.main(
        [
            "--exchange",
            "binance",
            "--symbol",
            "BTC/USD",
            "--sandbox",
            "--evidence-dest",
            str(tmp_path),
        ]
    )

    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    written = sorted(tmp_path.glob("exchange-sandbox-smoke-*.json"))
    assert len(written) == 1
    artifact = json.loads(written[0].read_text(encoding="utf-8"))
    assert report["evidence_path"] == str(written[0])
    assert artifact["report_type"] == "exchange_sandbox_smoke"
    assert artifact["read_only"] is True
    assert artifact["ok"] is True
    assert artifact["sandbox"] is True


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
    assert "--sandbox" not in calls[0]
    assert calls[1][:2] == ["--exchange", "binance"]
    assert "--sandbox" in calls[1]
    assert calls[2][:2] == ["--exchange", "gateio"]
    assert "--sandbox" in calls[2]
