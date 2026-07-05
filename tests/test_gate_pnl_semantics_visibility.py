from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_promotion_gates",
    Path(__file__).resolve().parents[1] / "scripts" / "check_promotion_gates.py",
)
gates = importlib.util.module_from_spec(_SPEC)
sys.modules["check_promotion_gates"] = gates
assert _SPEC.loader is not None
_SPEC.loader.exec_module(gates)


def _fill(pnl: float, semantics: str | None) -> dict:
    fill = {"record_type": "fill", "pnl_usd": pnl}
    if semantics is not None:
        fill["pnl_usd_semantics"] = semantics
    return fill


def test_all_net_fills_not_flagged_mixed():
    fills = [_fill(1.0, "net_of_fees") for _ in range(12)]
    summary = gates._pnl_semantics_summary(fills)
    assert summary["counts"] == {"net_of_fees": 12}
    assert summary["mixed"] is False
    assert summary["warning"] == ""


def test_legacy_fills_counted_as_unknown_legacy():
    fills = [_fill(1.0, None) for _ in range(12)]
    summary = gates._pnl_semantics_summary(fills)
    assert summary["counts"] == {"unknown_legacy": 12}
    assert summary["mixed"] is False


def test_mixed_semantics_flagged_with_warning():
    fills = [_fill(1.0, None) for _ in range(6)] + [
        _fill(-0.5, "net_of_fees") for _ in range(6)
    ]
    summary = gates._pnl_semantics_summary(fills)
    assert summary["counts"] == {"unknown_legacy": 6, "net_of_fees": 6}
    assert summary["mixed"] is True
    assert "mixed" in summary["warning"]


def test_fills_without_pnl_are_ignored():
    summary = gates._pnl_semantics_summary(
        [{"record_type": "fill"}, _fill(1.0, "net_of_fees")]
    )
    assert summary["counts"] == {"net_of_fees": 1}


def test_expectancy_pass_fail_unchanged_by_semantics():
    uniform = [_fill(1.0, "net_of_fees") for _ in range(10)]
    mixed = [_fill(1.0, "net_of_fees") for _ in range(5)] + [
        _fill(1.0, None) for _ in range(5)
    ]
    assert gates._check_expectancy(uniform) == gates._check_expectancy(mixed)


def test_history_branch_surfaces_semantics_report_without_changing_expectancy():
    fills = [_fill(1.0, "net_of_fees") for _ in range(5)] + [
        _fill(1.0, None) for _ in range(5)
    ]
    out = gates._paper_gate_trade_metrics(
        fills,
        paper_history={
            "ok": True,
            "source": "trade_journal_sqlite",
            "fills": 10,
            "closed_trades": 5,
            "expectancy_per_closed_trade": 2.5,
        },
    )
    assert out["expectancy_value"] == 2.5
    assert out["expectancy_mixed_semantics"] is True
    assert out["expectancy_pnl_semantics"] == {
        "net_of_fees": 5,
        "unknown_legacy": 5,
    }
