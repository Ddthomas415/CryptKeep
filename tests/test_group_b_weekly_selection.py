"""Synthetic Group B contract tests; no actual market data or forward results."""
import copy
from datetime import timedelta
import json

import pytest

from services.analytics.group_b_weekly_selection import build_selection, publish_selection
from services.market_data.group_b_selection import (
    FROZEN, UNIVERSE, assign_slots, digest, instant, validate_selection, week_at, weekly_name,
)

RANK = "2026-11-09T00:05:00+00:00"
NOW = "2026-11-09T00:06:00+00:00"


def inputs(eligible=("BTC/USD", "ETH/USD", "SOL/USD"), rank_at=RANK):
    cutoff = instant(rank_at).replace(minute=0)
    bars = [[int((cutoff - timedelta(hours=200 - i)).timestamp() * 1000),
             100 + i, 101 + i, 99 + i, 100 + i, 10000] for i in range(200)]
    return [{"symbol": s, "observed_at": rank_at, "metadata_sha256": "a" * 64,
             **({"product_id": s.replace("/", "-"), "symbol_return_pct": float(n), "ohlcv": copy.deepcopy(bars)}
                if s in eligible else {"product_id": None, "exclusion": "no_coinbase_usd_pair"})}
            for n, s in enumerate(UNIVERSE)]


def selection(eligible=("BTC/USD", "ETH/USD", "SOL/USD"), **kw):
    rank_at = kw.pop("rank_at", RANK)
    generated_at = kw.pop("generated_at", NOW)
    return build_selection(inputs=inputs(eligible, rank_at), rank_at=rank_at, generated_at=generated_at, **kw)


def reseal(artifact):
    artifact["sha256"] = digest({k: v for k, v in artifact.items() if k != "sha256"})
    return artifact


def test_producer_reuses_exact_frozen_ranker_and_records_inputs():
    from services.signals.market_ranker import rank_market
    artifact = selection()
    supplied = [x for x in artifact["inputs"] if x.get("product_id")]
    assert artifact["ranked"] == rank_market(symbols_data=supplied)
    assert artifact["code"] == FROZEN
    assert len(artifact["inputs"]) == 25
    assert set(artifact["slots"]) == {"BTC/USD", "ETH/USD", "SOL/USD"}


def test_retained_coins_keep_slots_and_gaps_do_not_reuse_old_picks():
    old = selection()
    old_slots = old["slots"]
    newer = selection(("ETH/USD", "SOL/USD", "XRP/USD"), rank_at="2026-11-23T00:05:00Z",
                      generated_at="2026-11-23T00:06:00Z", previous=old)
    for s in ("ETH/USD", "SOL/USD"):
        assert newer["slots"].index(s) == old_slots.index(s)
    assert "BTC/USD" not in newer["slots"]
    assert newer["previous_sha256"] == old["sha256"]


def test_slot_assignment_and_tie_order():
    assert assign_slots(["ETH/USD", "BTC/USD"], ["BTC/USD", "SOL/USD", "ETH/USD"]) == ["BTC/USD", None, "ETH/USD"]
    data = inputs()
    for x in data:
        if x.get("product_id"):
            x["symbol_return_pct"] = 0
    artifact = build_selection(inputs=data, rank_at=RANK, generated_at=NOW)
    assert [x["symbol"] for x in artifact["ranked"]] == ["BTC/USD", "ETH/USD", "SOL/USD"]


@pytest.mark.parametrize("bad", ["partial", "ticker", "future", "forming", "gap", "nan", "alias", "exclusion"])
def test_unknown_inputs_never_become_cash_selection(bad):
    data = inputs()
    if bad == "partial":
        data.pop()
    elif bad == "ticker":
        data[0].pop("symbol_return_pct")
    elif bad == "future":
        data[0]["observed_at"] = NOW
    elif bad == "forming":
        data[0]["ohlcv"][-1][0] += 3600000
    elif bad == "gap":
        data[0]["ohlcv"].pop()
    elif bad == "nan":
        data[0]["symbol_return_pct"] = float("nan")
    elif bad == "alias":
        data[0]["product_id"] = "OTHER-USD"
    else:
        data[3]["exclusion"] = "fetch_failed"
    with pytest.raises((ValueError, KeyError)):
        build_selection(inputs=data, rank_at=RANK, generated_at=NOW)


@pytest.mark.parametrize("now", ["2026-11-09T00:04:59Z", "2026-11-16T00:05:00Z"])
def test_selection_is_neither_early_nor_stale(now):
    with pytest.raises(ValueError):
        validate_selection(selection(), now=now)


def test_week_boundary_is_utc_monday_0005():
    assert week_at("2026-11-09T00:04:59Z") == instant("2026-11-02T00:05:00Z")
    assert week_at(RANK) == instant(RANK)


def test_publication_is_dated_complete_and_never_overwrites(tmp_path):
    artifact = selection()
    path = publish_selection(artifact, tmp_path)
    assert path.name == weekly_name(NOW)
    assert json.loads(path.read_text()) == artifact
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        publish_selection(artifact, tmp_path)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob(".group_b_*"))


def test_content_mutation_and_frozen_code_change_refuse(monkeypatch):
    artifact = selection()
    artifact["slots"][0] = None
    with pytest.raises(ValueError, match="hash"):
        validate_selection(artifact, now=NOW)
    monkeypatch.setitem(FROZEN, "services/signals/market_ranker.py", "0" * 64)
    with pytest.raises(ValueError, match="frozen_source_changed"):
        selection()


def test_offline_cli_builds_one_dated_artifact_without_fetching(tmp_path, monkeypatch, capsys):
    import socket
    from scripts.research import build_group_b_weekly_selection as command

    class Clock:
        @staticmethod
        def now(_timezone):
            return instant(NOW)

    monkeypatch.setattr(command, "datetime", Clock)
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("offline producer attempted network"))
    source = tmp_path / "public_inputs.json"
    source.write_text(json.dumps({"inputs": inputs()}))
    output = tmp_path / "slots"
    output.mkdir()
    assert command.main(["--inputs", str(source), "--rank-at", RANK,
                         "--output-directory", str(output)]) == 0
    artifact = json.loads((output / weekly_name(NOW)).read_text())
    assert artifact["generated_at"] == NOW
    assert artifact["sha256"] in capsys.readouterr().out
    validate_selection(artifact, now=NOW)
