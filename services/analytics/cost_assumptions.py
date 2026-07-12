from __future__ import annotations

import inspect
import math
import os
from dataclasses import fields
from typing import Any

ENGINE_DEFAULT_FEE_BPS = 7.5
ENGINE_DEFAULT_SLIPPAGE_BPS = 5.0
PAPER_FEES_DEFAULT_BPS = 0.0
DEFAULT_MIN_PLAUSIBLE_ROUND_TRIP_BPS = 5.0

OK = "ok"
WARN = "warning"
FAIL = "fail"
CONFIG_UNREADABLE = "config_unreadable"
_RANK = {OK: 0, WARN: 1, FAIL: 2}


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _configured_float(mapping: dict[str, Any], key: str, *, default: float) -> dict[str, Any]:
    if key not in mapping:
        return {"status": "missing", "value": float(default), "raw": None}
    value = _num(mapping.get(key))
    if value is None:
        return {"status": "invalid", "value": None, "raw": mapping.get(key)}
    return {"status": "configured", "value": float(value), "raw": mapping.get(key)}


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def min_plausible_round_trip_bps() -> float:
    raw = str(os.environ.get("CBP_MIN_PLAUSIBLE_ROUND_TRIP_BPS") or "").strip()
    value = _num(raw) if raw else None
    if value is None or value < 0:
        return DEFAULT_MIN_PLAUSIBLE_ROUND_TRIP_BPS
    return value


def evidence_service_cost_defaults() -> dict[str, Any]:
    try:
        from services.analytics.paper_strategy_evidence_service import PaperStrategyEvidenceServiceCfg

        defaults: dict[str, Any] = {}
        for item in fields(PaperStrategyEvidenceServiceCfg):
            if item.name in {"fee_bps", "slippage_bps"}:
                defaults[item.name] = _num(item.default)
        if defaults.get("fee_bps") is None or defaults.get("slippage_bps") is None:
            return {"fee_bps": None, "slippage_bps": None, "derivable": False}
        return {
            "fee_bps": float(defaults["fee_bps"]),
            "slippage_bps": float(defaults["slippage_bps"]),
            "derivable": True,
        }
    except Exception:
        return {"fee_bps": None, "slippage_bps": None, "derivable": False}


def backtest_cost_defaults() -> dict[str, Any]:
    try:
        from services.backtest.walk_forward import run_anchored_walk_forward

        sig = inspect.signature(run_anchored_walk_forward)
        fee_bps = _num(sig.parameters["fee_bps"].default)
        slippage_bps = _num(sig.parameters["slippage_bps"].default)
        if fee_bps is None or slippage_bps is None:
            return {"fee_bps": None, "slippage_bps": None, "derivable": False}
        return {"fee_bps": float(fee_bps), "slippage_bps": float(slippage_bps), "derivable": True}
    except Exception:
        return {"fee_bps": None, "slippage_bps": None, "derivable": False}


def _interpretation(overall: str) -> str:
    if overall == FAIL:
        return (
            "The live paper cost surface is invalid or models an implausibly low "
            "round-trip cost against the declared policy floor. Correct the config, "
            "then segment historical evidence by the cost assumptions in force when "
            "each result was produced."
        )
    if overall == WARN:
        return (
            "The live paper cost surface is not failing, but at least one assumption "
            "needs operator confirmation. Historical expectancy may require "
            "interpretation against the cost assumptions actually in force."
        )
    return "The live paper cost surface is explicitly configured and plausible."


def evaluate_cost_assumptions(user_cfg: dict[str, Any]) -> dict[str, Any]:
    cfg = user_cfg if isinstance(user_cfg, dict) else {}
    paper = cfg.get("paper_trading") if isinstance(cfg.get("paper_trading"), dict) else {}
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}

    engine_fee_field = _configured_float(paper, "fee_bps", default=ENGINE_DEFAULT_FEE_BPS)
    engine_slippage_field = _configured_float(
        paper,
        "slippage_bps",
        default=ENGINE_DEFAULT_SLIPPAGE_BPS,
    )
    paper_fee_lookup_field = _configured_float(
        execution,
        "paper_fee_bps",
        default=PAPER_FEES_DEFAULT_BPS,
    )

    engine_fee = engine_fee_field["value"]
    engine_slippage = engine_slippage_field["value"]
    paper_fee_lookup = paper_fee_lookup_field["value"]
    evidence_defaults = evidence_service_cost_defaults()
    backtest_defaults = backtest_cost_defaults()

    surfaces = {
        "paper_engine": {
            "role": (
                "authoritative for paper-fill execution costs and the expectancy "
                "calculations derived from those fills; not authoritative for "
                "backtest/walk-forward expectancy"
            ),
            "fee_bps": engine_fee,
            "slippage_bps": engine_slippage,
            "fee_status": engine_fee_field["status"],
            "slippage_status": engine_slippage_field["status"],
            "source": "user.yaml paper_trading.*",
        },
        "evidence_service": {
            "role": "leaderboard/evidence scoring assumption; separate from paper fills",
            "fee_bps": evidence_defaults.get("fee_bps"),
            "slippage_bps": evidence_defaults.get("slippage_bps"),
            "derivable": evidence_defaults.get("derivable"),
            "source": "PaperStrategyEvidenceServiceCfg dataclass defaults",
        },
        "paper_fees_lookup": {
            "role": "dormant lookup unless production callers are added",
            "fee_bps": paper_fee_lookup,
            "fee_status": paper_fee_lookup_field["status"],
            "source": "user.yaml execution.paper_fee_bps",
        },
        "backtest_walk_forward": {
            "role": "archive/backtest expectancy surface; validate separately from paper fills",
            "fee_bps": backtest_defaults.get("fee_bps"),
            "slippage_bps": backtest_defaults.get("slippage_bps"),
            "derivable": backtest_defaults.get("derivable"),
            "source": "run_anchored_walk_forward signature defaults",
        },
    }

    checks: list[dict[str, str]] = []

    invalid_engine_fields = [
        name
        for name, field in (
            ("paper_trading.fee_bps", engine_fee_field),
            ("paper_trading.slippage_bps", engine_slippage_field),
        )
        if field["status"] == "invalid"
    ]
    if invalid_engine_fields:
        checks.append(
            _check(
                "engine_costs_valid",
                FAIL,
                "invalid/non-finite values: " + ", ".join(invalid_engine_fields),
            )
        )
    elif float(engine_fee) < 0 or float(engine_slippage) < 0:
        checks.append(_check("engine_costs_valid", FAIL, "fee/slippage must not be negative"))
    else:
        checks.append(_check("engine_costs_valid", OK, "paper fee/slippage values are finite and non-negative"))

    missing_engine_fields = [
        name
        for name, field in (
            ("fee_bps", engine_fee_field),
            ("slippage_bps", engine_slippage_field),
        )
        if field["status"] == "missing"
    ]
    if missing_engine_fields:
        checks.append(
            _check(
                "engine_costs_configured",
                WARN,
                "falling back to code defaults for: "
                + ", ".join(missing_engine_fields)
                + f" (fee={engine_fee}, slippage={engine_slippage})",
            )
        )
    else:
        checks.append(
            _check(
                "engine_costs_configured",
                OK,
                f"paper_trading.fee_bps={engine_fee}, slippage_bps={engine_slippage}",
            )
        )

    round_trip_bps: float | None = None
    if engine_fee is not None and engine_slippage is not None:
        round_trip_bps = (float(engine_fee) + float(engine_slippage)) * 2.0
        floor = min_plausible_round_trip_bps()
        if round_trip_bps < floor:
            checks.append(
                _check(
                    "round_trip_plausible",
                    FAIL,
                    f"modeled round-trip {round_trip_bps:.1f} bps < policy floor {floor:.1f} bps",
                )
            )
        else:
            checks.append(
                _check(
                    "round_trip_plausible",
                    OK,
                    f"modeled round-trip {round_trip_bps:.1f} bps >= policy floor {floor:.1f} bps",
                )
            )
        if float(engine_fee) <= 0:
            checks.append(_check("fee_modeled", WARN, "paper_trading.fee_bps is zero; confirm this is intentional"))
        else:
            checks.append(_check("fee_modeled", OK, f"fee_bps={engine_fee}"))
        if float(engine_slippage) <= 0:
            checks.append(
                _check(
                    "slippage_modeled",
                    WARN,
                    "slippage_bps is zero; treat expectancy as provisional until shadow costs calibrate it",
                )
            )
        else:
            checks.append(_check("slippage_modeled", OK, f"slippage_bps={engine_slippage}"))
    else:
        checks.append(_check("round_trip_plausible", FAIL, "round-trip cost could not be computed"))

    if paper_fee_lookup_field["status"] == "invalid":
        checks.append(_check("dormant_lookup_valid", WARN, "execution.paper_fee_bps is invalid, but lookup is dormant today"))
    elif paper_fee_lookup_field["status"] == "missing":
        checks.append(
            _check(
                "dormant_lookup_unset",
                WARN,
                "execution.paper_fee_bps is unset; harmless while paper_fees has no production callers",
            )
        )
    else:
        checks.append(_check("dormant_lookup_unset", OK, f"execution.paper_fee_bps={paper_fee_lookup}"))

    if evidence_defaults.get("derivable"):
        evidence_fee = float(evidence_defaults["fee_bps"])
        if engine_fee is not None and abs(evidence_fee - float(engine_fee)) > 0.01:
            checks.append(
                _check(
                    "evidence_scoring_cost_surface",
                    WARN,
                    f"evidence scoring fee default {evidence_fee} differs from paper engine fee {engine_fee}; roles differ",
                )
            )
        else:
            checks.append(_check("evidence_scoring_cost_surface", OK, "evidence scoring fee matches paper engine fee"))
    else:
        checks.append(_check("evidence_scoring_cost_surface", WARN, "could not derive evidence-service cost defaults"))

    if backtest_defaults.get("derivable"):
        backtest_fee = float(backtest_defaults["fee_bps"])
        backtest_slippage = float(backtest_defaults["slippage_bps"])
        if engine_fee is not None and abs(backtest_fee - float(engine_fee)) > 0.01:
            status = WARN
            lead = "differs"
        else:
            status = OK
            lead = "matches"
        checks.append(
            _check(
                "backtest_cost_surface",
                status,
                f"walk_forward defaults fee={backtest_fee}, slippage={backtest_slippage}; "
                f"paper engine fee={engine_fee}. Backtest fee {lead}; this validator does "
                "not verify archive-sweep cost policy.",
            )
        )
    else:
        checks.append(_check("backtest_cost_surface", WARN, "could not derive walk-forward cost defaults"))

    overall = max((item["status"] for item in checks), key=lambda status: _RANK[status])
    return {
        "overall": overall,
        "round_trip_bps": round_trip_bps,
        "policy_floor_bps": min_plausible_round_trip_bps(),
        "surfaces": surfaces,
        "checks": checks,
        "interpretation": _interpretation(overall),
    }


def check_cost_assumptions() -> dict[str, Any]:
    try:
        from services.admin.config_editor import load_user_yaml

        cfg = load_user_yaml(strict=True)
    except Exception as exc:
        return {
            "overall": CONFIG_UNREADABLE,
            "round_trip_bps": None,
            "policy_floor_bps": min_plausible_round_trip_bps(),
            "surfaces": {},
            "checks": [_check("config_readable", FAIL, f"{type(exc).__name__}: {exc}")],
            "interpretation": (
                "Config could not be read, so cost assumptions are not verified. "
                "No claim is made about the fee values themselves."
            ),
        }
    return evaluate_cost_assumptions(cfg)
