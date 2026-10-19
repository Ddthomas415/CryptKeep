import copy

import pytest

from services.strategies.execution_identity import identity_evidence
from services.execution import paper_engine


def order():
    payload = {
        "version": 1, "cohort_id": "synthetic-only", "strategy_name": "sma_200_trend",
        "parameters": {"sma_period": 200}, "entry_policy": {"rule": "synthetic"},
        "exit_policy": {"stop": 0}, "sizing": {"qty": 1},
        "costs": {"fee_bps": 7.5, "slippage_bps": 5.0, "quote_currency": "USDT",
                  "basis_version": "paper_fee_inclusive_average_v1"},
        "market": {"venue": "coinbase", "symbol": "BTC/USDT", "timeframe": "1d",
                   "source": "public_ohlcv", "sample_mode": False},
        "implementation": {key: "a"*64 for key in ("signal", "resolver", "exits", "paper_engine")},
    }
    return {"order_id": "synthetic", "venue": "coinbase", "symbol": "BTC/USDT",
            "side": "sell", "qty": 1., "strategy_id": "synthetic-only",
            "meta": identity_evidence(payload)}


def config():
    return {"fee_bps": 7.5, "slippage_bps": 5.0, "quote_currency": "USDT"}


def test_matching_policy_is_detached():
    row = order()
    result = paper_engine._fill_identity_extra(row, config())
    assert result["execution_identity_fill_status"] == "cost_policy_verified"
    row["meta"]["execution_identity"]["parameters"]["sma_period"] = 20
    assert result["execution_identity"]["parameters"]["sma_period"] == 200


@pytest.mark.parametrize("field,value", [("fee_bps", 8.), ("slippage_bps", 6.), ("quote_currency", "USD")])
def test_cost_mismatch_excludes_identity(field, value):
    cfg = config()
    cfg[field] = value
    result = paper_engine._fill_identity_extra(order(), cfg)
    assert result["execution_identity_fill_status"] == "invalid"
    assert "execution_identity" not in result


@pytest.mark.parametrize("field,value", [("symbol", "ETH/USDT"), ("venue", "kraken")])
def test_order_market_mismatch(field, value):
    row = order()
    row[field] = value
    assert paper_engine._fill_identity_extra(row, config())["execution_identity_fill_status"] == "invalid"


@pytest.mark.parametrize("meta", [None, {}, {"execution_identity_capture_status": "failed"},
                                  {"execution_identity": "malformed"}])
def test_legacy_or_incomplete_evidence(meta):
    row = order()
    row["meta"] = meta
    result = paper_engine._fill_identity_extra(row, config())
    assert result == {} if not meta else result["execution_identity_fill_status"] == "invalid"


@pytest.mark.parametrize("side", ["buy", "sell"])
@pytest.mark.parametrize("mode", ["matching", "mismatch", "legacy"])
def test_fill_logging_does_not_change_accounting_result(monkeypatch, side, mode):
    row = order()
    row["side"] = side
    if mode == "mismatch":
        row["meta"]["execution_identity_sha256"] = "b"*64
    elif mode == "legacy":
        row["meta"] = {}
    before = copy.deepcopy(row)
    calls, logged = [], []
    class Database:
        def apply_fill(self, **kwargs):
            calls.append(kwargs)
            return {"ok": True, "realized_pnl_usd": -1.}
    class Logger:
        def __init__(self, strategy):
            pass
        def log_fill(self, **kwargs):
            logged.append(kwargs)
    monkeypatch.setattr("services.strategies.evidence_logger.EvidenceLogger", Logger)
    engine = paper_engine.PaperEngine.__new__(paper_engine.PaperEngine)
    engine.cfg = config()
    engine.db = Database()
    engine._clock = lambda: "2026-10-08T12:00:00Z"
    assert engine._apply_fill(row, 100., 1.) == {"ok": True, "realized_pnl_usd": -1.}
    assert len(calls) == len(logged) == 1
    assert calls[0]["fee"] == .075
    assert row == before
    extra = logged[0]["extra"]
    if mode == "matching":
        assert extra["execution_identity_fill_status"] == "cost_policy_verified"
    elif mode == "mismatch":
        assert extra["execution_identity_fill_status"] == "invalid"
    else:
        assert "execution_identity_fill_status" not in extra
