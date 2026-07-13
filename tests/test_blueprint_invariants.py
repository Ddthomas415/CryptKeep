"""Executable invariants for cost/expectancy forks (repo-wide blueprint audit).

These tests protect FACTS established by tracing on 2026-07-12, not architectural
opinions. Each one fails if the traced relationship changes — forcing the
blueprint (docs/architecture/SYSTEM_BLUEPRINT.md) to be updated rather than
silently going stale.

A failure here is not automatically a bug. It means a traced fact is no longer
true and the blueprint claim must be re-verified.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _source_files(*roots: str) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        path = REPO / root
        if path.is_file():
            files.append(path)
        else:
            files.extend(sorted(path.rglob("*.py")))
    return files


def _source_matches(pattern: str, *roots: str) -> list[tuple[str, int, str, re.Match[str]]]:
    rx = re.compile(pattern)
    matches: list[tuple[str, int, str, re.Match[str]]] = []
    for path in _source_files(*roots):
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith("tests/"):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = rx.search(line)
            if match:
                matches.append((rel, lineno, line.strip(), match))
    return matches


# ---------------------------------------------------------------------------
# FORK 1: expectancy has two structurally different denominators.
#
# REFUTED CLAIM: "the promotion gate measures expectancy per trade."
# TRACE:
#   paper_engine.py:332      pnl = None for BUY (open) legs; only SELL legs get
#                            realized PnL.
#   evidence_logger.py:345   writes "pnl_usd": pnl unconditionally -> the KEY IS
#                            PRESENT with value None on entry fills.
#   check_promotion_gates.py:203
#                            [float(f.get("pnl_usd") or 0) for f in fills
#                             if "pnl_usd" in f]
#                            -> key present, None coerced to 0.0
#                            -> entry fills ENTER THE MEAN AS ZERO.
# CONSEQUENCE: the gate's expectancy is mean-per-FILL, diluted toward zero by
# the entry/exit ratio (~50% for 1:1 round trips). It is NOT the per-closed-trade
# expectancy that `paper_evidence_qualification.expectancy_per_closed_trade`
# computes (net_realized / closed_count).
# ---------------------------------------------------------------------------

def test_entry_fills_are_written_with_a_present_pnl_usd_key():
    """The dilution depends on the KEY being present on entry fills. If entry
    fills stopped writing pnl_usd, the gate's filter would exclude them and the
    denominator would change."""
    src = (REPO / "services/execution/paper_engine.py").read_text(encoding="utf-8")
    assert "pnl = None" in src, "entry-fill pnl initialization changed"
    assert 'if order.get("side") == "sell":' in src, "sell-only realized-pnl gating changed"

    logger = (REPO / "services/strategies/evidence_logger.py").read_text(encoding="utf-8")
    assert '"pnl_usd":' in logger, "evidence no longer writes a pnl_usd key"


def test_gate_expectancy_is_per_fill_not_per_closed_trade():
    """Executable proof of the dilution: a 1:1 round trip (entry + exit) with a
    +10 exit yields gate expectancy 5.0 (mean over 2 fills), not 10.0 (per trade).

    If this ever returns 10.0, the gate switched to a per-trade denominator and
    the blueprint's expectancy fork claim must be revised.
    """
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "cpg_invariant", REPO / "scripts" / "check_promotion_gates.py"
    )
    gates = importlib.util.module_from_spec(spec)
    sys.modules["cpg_invariant"] = gates
    spec.loader.exec_module(gates)

    # 5 round trips: each an entry (pnl_usd None, as paper_engine writes) and an
    # exit (+10). Per-trade expectancy is 10.0; per-fill is 5.0.
    fills = []
    for _ in range(5):
        fills.append({"pnl_usd": None})   # entry leg, key present
        fills.append({"pnl_usd": 10.0})   # exit leg
    ok, value = gates._check_expectancy(fills)
    assert ok is True
    assert value == pytest.approx(5.0), (
        "gate expectancy is no longer diluted by entry fills — the per-fill vs "
        "per-closed-trade fork has changed; update the blueprint."
    )


def test_qualification_expectancy_is_per_closed_trade():
    """The other side of the fork: qualification divides by CLOSED TRADES."""
    src = (REPO / "services/control/paper_evidence_qualification.py").read_text(encoding="utf-8")
    assert "net_realized / closed_count" in src, (
        "qualification's per-closed-trade expectancy denominator changed"
    )


# ---------------------------------------------------------------------------
# FORK 2: the fee/slippage surface census.
#
# Five fee surfaces were traced (2026-07-12). This test pins the census so a new
# surface (or a change to an existing default) cannot appear unnoticed.
# ---------------------------------------------------------------------------

_FEE_SURFACES = {
    # module path: (fee default, slippage default, traced role)
    "services/execution/paper_engine.py": (7.5, 5.0, "canonical paper fills (user.yaml paper_trading.*)"),
    "services/analytics/paper_strategy_evidence_service.py": (10.0, 5.0, "evidence/leaderboard scoring"),
    "services/paper_exec.py": (10.0, 5.0, "compat paper executor (services/paper_trader/main.py)"),
    "services/paper_trader/paper_execution_venue.py": (1.0, 0.0, "legacy runner venue (trading_runner/run_trader.py)"),
    "services/execution/paper_fees.py": (0.0, None, "dormant: no production callers"),
}


@pytest.mark.parametrize("path,expected", list(_FEE_SURFACES.items()))
def test_fee_surface_defaults_unchanged(path: str, expected):
    """Each traced cost surface still declares the default the blueprint records."""
    fee, slip, _role = expected
    src = (REPO / path).read_text(encoding="utf-8")
    assert f"{fee}" in src, f"{path}: fee default {fee} no longer present"
    if slip is not None:
        assert f"{slip}" in src, f"{path}: slippage default {slip} no longer present"


# The backtest family declares fee_bps as a PARAMETER default in seven modules.
# Traced (2026-07-12): all seven default to 10.0 and none reads user.yaml — they
# form ONE cost family, not seven independent surfaces. Pinned so a divergence
# inside the family becomes visible.
_BACKTEST_FEE_FAMILY = {
    "services/backtest/evidence_cycle.py",
    "services/backtest/evidence_run.py",
    "services/backtest/leaderboard.py",
    "services/backtest/parameter_sweep.py",
    "services/backtest/parity_engine.py",
    "services/backtest/signal_replay.py",
    "services/backtest/walk_forward.py",
}


def test_backtest_fee_family_is_internally_consistent():
    """All seven backtest modules must declare the SAME fee default. A divergence
    inside the family would mean backtest, sweep, leaderboard, and parity results
    are computed against different costs."""
    defaults_by_file: dict[str, set[float]] = {}
    for rel, _lineno, _line, match in _source_matches(
        r"fee_bps:\s*float\s*=\s*([0-9.]+)",
        "services/backtest",
    ):
        defaults_by_file.setdefault(rel, set()).add(float(match.group(1)))

    assert set(defaults_by_file) == _BACKTEST_FEE_FAMILY, (
        "backtest fee-family membership changed: "
        f"{sorted(set(defaults_by_file) ^ _BACKTEST_FEE_FAMILY)}"
    )
    divergent_modules = {
        rel: sorted(values)
        for rel, values in defaults_by_file.items()
        if len(values) != 1
    }
    assert not divergent_modules, (
        f"backtest fee family DIVERGED within modules: {divergent_modules}"
    )
    family_defaults = {next(iter(values)) for values in defaults_by_file.values()}
    assert len(family_defaults) == 1, (
        "backtest fee family DIVERGED — modules now use different fee defaults: "
        f"{defaults_by_file}"
    )


def test_no_new_fee_surface_appeared():
    """A `fee_bps: float = <n>` declaration outside the traced census or the
    backtest family means a new cost surface exists and the blueprint is stale."""
    found = {
        rel
        for rel, _lineno, _line, _match in _source_matches(
            r"fee_bps:\s*float\s*=",
            "services",
        )
    }
    known = set(_FEE_SURFACES) | _BACKTEST_FEE_FAMILY | {"services/execution/fill_model.py"}
    unexpected = found - known
    assert not unexpected, (
        f"new fee surface(s) not in the blueprint census: {sorted(unexpected)}"
    )


def test_legacy_runner_models_near_free_execution():
    """Traced fact worth protecting: the legacy trading_runner hardcodes
    fee=1.0 bps and slippage=0.0 — near-free execution. Any evidence produced by
    that path is NOT comparable to canonical paper evidence. If this changes,
    the blueprint's 'non-canonical, optimistic costs' note must be revised."""
    src = (REPO / "services/trading_runner/run_trader.py").read_text(encoding="utf-8")
    assert "fee_bps=1.0" in src and "slippage_bps=0.0" in src


# ---------------------------------------------------------------------------
# FORK 3: backtest costs are sourced independently of user.yaml.
# ---------------------------------------------------------------------------

def test_backtest_costs_not_sourced_from_user_yaml():
    hits = _source_matches(
        r"load_user_yaml|load_user_config|paper_trading",
        "services/backtest",
    )
    rendered = "\n".join(f"{rel}:{lineno}:{line}" for rel, lineno, line, _match in hits)
    assert not hits, (
        "services/backtest now reads user config — backtest costs are no longer "
        "independently sourced; update the blueprint.\n" + rendered
    )


def test_backtest_cost_defaults_are_derivable():
    from services.backtest.walk_forward import run_anchored_walk_forward

    sig = inspect.signature(run_anchored_walk_forward)
    assert sig.parameters["fee_bps"].default == 10.0
    assert sig.parameters["slippage_bps"].default == 5.0


# ---------------------------------------------------------------------------
# FORK 4: realized_pnl_usd has TWO different mathematical meanings.
#
# PAPER  storage/paper_trading_sqlite.py:354  proceeds(net of sell fee)
#                                             - (avg incl. buy fee) * qty
#                                             -> pnl_usd_semantics="net_of_fees"
# LIVE   storage/live_position_store_sqlite.py:220
#                                             realized = (price - old_avg) * qty
#                                             -> apply_fill takes NO fee param
#                                             -> GROSS of fees
#
# Same field name, different mathematics. The live fee is carried separately to
# RiskDailyDB (fees_usd column) rather than folded into realized.
# ---------------------------------------------------------------------------

def test_paper_realized_pnl_is_net_of_fees():
    src = (REPO / "storage/paper_trading_sqlite.py").read_text(encoding="utf-8")
    assert '"pnl_usd_semantics": "net_of_fees"' in src


def test_live_position_store_realized_pnl_is_gross_of_fees():
    """The live store's apply_fill takes NO fee parameter and computes
    (price - avg) * qty. If a fee param appears, live realized may have become
    net — the blueprint's PnL-semantics fork must then be re-verified."""
    src = (REPO / "storage/live_position_store_sqlite.py").read_text(encoding="utf-8")
    sig_start = src.index("def apply_fill(")
    sig = src[sig_start:src.index(")", sig_start)]
    assert "fee" not in sig, "live apply_fill now takes a fee param — PnL semantics may have changed"
    assert "realized = (price_f - old_avg) * qty_f" in src


# ---------------------------------------------------------------------------
# FORK 5 (capital-relevant): the live daily-loss gate reads NET realized PnL
# including fees.
#
#   risk_daily.snapshot():  "realized_pnl": realized      <- GROSS
#                           "fees":         fees
#                           "pnl": (realized - fees)      <- NET, computed here
#   risk_daily.realized_today_usd():  returns snap["pnl"]            <- NET
#   _executor_submit.py:382:          rpnl = realized_today_usd()    -> live gates
#
# Consequence: the daily-loss limit is fee-inclusive, so fees cannot cause actual
# loss to exceed the configured cap unnoticed.
# ---------------------------------------------------------------------------

def test_risk_daily_snapshot_exposes_both_gross_and_net():
    src = (REPO / "services/risk/risk_daily.py").read_text(encoding="utf-8")
    assert '"realized_pnl": realized' in src, "gross field renamed"
    assert '"pnl": (realized - fees)' in src, "net field no longer computed"


def test_realized_today_usd_returns_net_including_fees(tmp_path):
    """POLICY: realized_today_usd() returns NET PnL including fees.

    The live risk gate at _executor_submit.py consumes this value, so changing
    this function back to gross PnL changes daily-loss cap semantics and must be
    reviewed before capped-live use.
    """
    src = (REPO / "services/risk/risk_daily.py").read_text(encoding="utf-8")
    fn = src[src.index("def realized_today_usd("):]
    fn = fn[: fn.index("\n    def ")] if "\n    def " in fn else fn
    assert 'snap.get("pnl"' in fn, (
        "realized_today_usd no longer returns the net pnl field — the "
        "daily-loss cap's fee treatment changed; re-verify the blueprint risk entry."
    )
    assert 'snap.get("realized_pnl"' not in fn

    from services.risk.risk_daily import RiskDailyDB, snapshot

    db_path = tmp_path / "risk_daily.sqlite"
    rdb = RiskDailyDB(str(db_path))
    rdb.add_pnl(realized_pnl_usd=-100.0, fee_usd=5.0)
    snap = snapshot(str(db_path))
    assert snap["realized_pnl"] == pytest.approx(-100.0)
    assert snap["pnl"] == pytest.approx(-105.0)
    assert rdb.realized_today_usd() == pytest.approx(-105.0)


def test_live_risk_gate_consumes_realized_today_usd():
    src = (REPO / "services/execution/_executor_submit.py").read_text(encoding="utf-8")
    assert "realized_today_usd()" in src
