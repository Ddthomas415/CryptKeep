"""Position-truth hysteresis + halt binding (operator decision 2026-10-09). Isolated temp stores, stub exchange."""
import asyncio

import pytest

from services.reconciliation.exchange_reconciler import ReconcileConfig
from services.reconciliation.position_truth import (DriftConfirmationStore, PositionTruthPolicy, critical_keys,
                                                    run_position_truth_once)
from storage.portfolio_store_sqlite import SQLitePortfolioStore

MIN = 60_000
TRADING = {"portfolio": {"quote_ccy": "USD"}, "symbols": ["BTC/USD"], "symbol_maps": {"coinbase": {"BTC/USD": "BTC/USD"}}}


class Stub:
    def __init__(self, total=None, fail=False, ts=None):
        self.total, self.fail, self.ts = total, fail, ts

    async def fetch_balance(self):
        if self.fail:
            raise TimeoutError("venue lookup failed")
        out = {"total": dict(self.total)}
        if self.ts is not None:
            out["timestamp"] = self.ts
        return out


@pytest.fixture
def env(tmp_path):
    port = SQLitePortfolioStore(path=tmp_path / "portfolio.sqlite")
    port.upsert_cash(exchange="coinbase", cash=1000.0, quote_ccy="USD")
    port.upsert_position(exchange="coinbase", symbol="BTC/USD", qty=1.0)
    cfg = ReconcileConfig(recon_db_path=str(tmp_path / "recon.sqlite"), portfolio_db_path=str(tmp_path / "portfolio.sqlite"),
                          runbook_db_path=str(tmp_path / "runbooks.sqlite"), auto_draft_runbook_on_critical=False)
    return cfg, DriftConfirmationStore(tmp_path / "position_truth.sqlite")


def step(env, total, t_ms, halts, fail=False):
    cfg, store = env
    return asyncio.run(run_position_truth_once(exchange_id="coinbase", ex_obj=Stub(total, fail), cfg=cfg,
                                               trading_cfg=TRADING, store=store, policy=PositionTruthPolicy(3, 15 * MIN),
                                               halt=halts.append, now_ms=lambda: t_ms))


GOOD = {"USD": 1000.0, "BTC": 1.0}
BAD = {"USD": 1000.0, "BTC": 0.5}  # venue holds half the BTC we think we hold


def test_single_critical_snapshot_does_not_halt(env):
    halts = []
    out = step(env, BAD, 0, halts)
    assert out["critical_keys"] == {"coinbase:position:BTC": -0.5} and halts == []


def test_three_observations_but_under_15_minutes_do_not_halt(env):
    halts = []
    for t in (0, 5 * MIN, 10 * MIN):
        step(env, BAD, t, halts)
    assert halts == []


def test_persistent_drift_halts_once_confirmed(env):
    halts = []
    for t in (0, 5 * MIN, 10 * MIN):
        step(env, BAD, t, halts)
    out = step(env, BAD, 15 * MIN, halts)
    assert out["halted"] is True and halts == ["position_truth_drift_confirmed:coinbase:position:BTC"]


def test_clean_observation_clears_and_restarts_the_clock(env):
    halts = []
    for t in (0, 5 * MIN, 10 * MIN):
        step(env, BAD, t, halts)
    step(env, GOOD, 12 * MIN, halts)
    for t in (14 * MIN, 20 * MIN, 26 * MIN):
        step(env, BAD, t, halts)
    assert halts == []  # 3 obs again but only 12 minutes since the new first observation
    step(env, BAD, 30 * MIN, halts)
    assert len(halts) == 1


def test_lookup_errors_neither_count_nor_clear(env):
    halts = []
    step(env, BAD, 0, halts)
    for t in (5 * MIN, 6 * MIN, 7 * MIN, 8 * MIN):
        assert step(env, None, t, halts, fail=True)["observation"] == "error_not_counted"
    assert env[1].rows("coinbase")[0]["count"] == 1 and halts == []
    step(env, BAD, 10 * MIN, halts)
    step(env, BAD, 16 * MIN, halts)
    assert len(halts) == 1


def test_warn_level_drift_never_counts(env):
    halts = []
    for t in range(0, 60 * MIN, 5 * MIN):
        step(env, {"USD": 1007.0, "BTC": 1.0}, t, halts)  # 7 USD: above 5 tolerance, below 15 critical
    assert halts == [] and env[1].rows("coinbase") == []


def test_cash_key_and_other_quote_keys():
    drift = {"exchange": "x", "cash": {"primary": {"quote_ccy": "USD", "abs_drift": -20.0},
                                       "others": [{"quote_ccy": "USDT", "abs_drift": 16.0}]}, "positions": []}
    assert critical_keys(drift, 5.0, 1e-4) == {"x:cash:USD": -20.0, "x:cash:USDT": 16.0}


def test_default_halt_arms_kill_switch_and_never_disarms(monkeypatch, env):
    calls = []
    import services.execution.kill_switch as ks
    monkeypatch.setattr(ks, "set_kill_switch", lambda armed, reason="manual": calls.append((armed, reason)) or {})
    cfg, store = env
    for t in (0, 5 * MIN, 10 * MIN, 15 * MIN):
        asyncio.run(run_position_truth_once(exchange_id="coinbase", ex_obj=Stub(BAD), cfg=cfg, trading_cfg=TRADING,
                                            store=store, policy=PositionTruthPolicy(3, 15 * MIN), now_ms=lambda: t))
    asyncio.run(run_position_truth_once(exchange_id="coinbase", ex_obj=Stub(GOOD), cfg=cfg, trading_cfg=TRADING,
                                        store=store, policy=PositionTruthPolicy(3, 15 * MIN), now_ms=lambda: 20 * MIN))
    assert calls and all(armed is True for armed, _ in calls)


def test_bad_env_values_cannot_loosen_policy(monkeypatch):
    monkeypatch.setenv("CBP_POSITION_DRIFT_MIN_OBS", "0")
    monkeypatch.setenv("CBP_POSITION_DRIFT_MIN_PERSIST_MS", "-5")
    p = PositionTruthPolicy.from_env()
    assert (p.min_obs, p.min_persist_ms) == (3, 900_000)


def test_positive_env_values_cannot_shorten_accepted_confirmation(monkeypatch):
    monkeypatch.setenv("CBP_POSITION_DRIFT_MIN_OBS", "1")
    monkeypatch.setenv("CBP_POSITION_DRIFT_MIN_PERSIST_MS", "0")
    p = PositionTruthPolicy.from_env()
    assert (p.min_obs, p.min_persist_ms) == (3, 900_000)


@pytest.mark.parametrize("obs,persist", [(1, 900_000), (3, 0), (True, 900_000), (3, True)])
def test_direct_policy_cannot_bypass_accepted_minima(obs, persist):
    with pytest.raises(ValueError):
        PositionTruthPolicy(obs, persist)


def test_stale_venue_snapshot_is_not_an_observation(env):
    cfg, store = env
    halts = []
    for t in (20 * MIN, 25 * MIN, 30 * MIN, 40 * MIN):
        out = asyncio.run(run_position_truth_once(exchange_id="coinbase", ex_obj=Stub(BAD, ts=t - 5 * MIN), cfg=cfg,
                                                  trading_cfg=TRADING, store=store, policy=PositionTruthPolicy(3, 15 * MIN),
                                                  halt=halts.append, now_ms=lambda: t))
        assert out["observation"] == "stale_snapshot_not_counted"
    assert halts == [] and store.rows("coinbase") == []
    fresh = asyncio.run(run_position_truth_once(exchange_id="coinbase", ex_obj=Stub(BAD, ts=50 * MIN - 1000), cfg=cfg,
                                                trading_cfg=TRADING, store=store, policy=PositionTruthPolicy(3, 15 * MIN),
                                                halt=halts.append, now_ms=lambda: 50 * MIN))
    assert fresh["observation"] == "counted"
