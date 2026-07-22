from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.strategies import config_tools
from services.strategies.presets import get_preset
from services.strategies.strategy_registry import SUPPORTED as REGISTRY_SUPPORTED
from services.strategies.validation import validate_strategy_config


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CryptoEdgeStrategySpec:
    name: str
    context_kind: str
    module_relpath: str
    preset_name: str | None
    known_blockers: tuple[str, ...]
    next_action: str


CRYPTO_EDGE_STRATEGIES: tuple[CryptoEdgeStrategySpec, ...] = (
    CryptoEdgeStrategySpec(
        name="funding_extreme",
        context_kind="funding",
        module_relpath="services/strategies/funding_extreme.py",
        preset_name="funding_extreme_default",
        known_blockers=(
            "persistent campaign blocked pending archive-backed research review",
            "crypto-edge promotion qualification remains high-risk gate work",
        ),
        next_action="review price-joined funding research before any persistent campaign decision",
    ),
    CryptoEdgeStrategySpec(
        name="open_interest_shift",
        context_kind="open_interest",
        module_relpath="services/strategies/open_interest_shift.py",
        preset_name="open_interest_shift_default",
        known_blockers=(
            "config-only until previous OI state is derived from snapshot history",
            "not executable through strategy_registry.compute_signal",
        ),
        next_action="build a reviewed OI history/context contract before enabling execution",
    ),
    CryptoEdgeStrategySpec(
        name="order_book_imbalance",
        context_kind="order_book",
        module_relpath="services/strategies/order_book_imbalance.py",
        preset_name=None,
        known_blockers=(
            "depth REST snapshots are not proof-quality evidence for this signal",
            "requires tighter-cadence or streaming depth evidence path",
        ),
        next_action="design a proof-quality depth collection path before registration",
    ),
)


def _strategy_status(*, registry_executable: bool, config_supported: bool, config_only: bool, preset_exists: bool) -> str:
    if registry_executable and config_supported and preset_exists and not config_only:
        return "stage0_wired_research_only"
    if config_only:
        return "config_only_research_placeholder"
    if config_supported and not registry_executable:
        return "config_supported_not_executable"
    return "signal_module_unregistered"


def _preset_state(preset_name: str | None) -> dict[str, Any]:
    if not preset_name:
        return {
            "preset_name": None,
            "preset_exists": False,
            "preset_trade_enabled": None,
            "preset_validation_ok": None,
            "preset_validation_errors": [],
        }
    preset = get_preset(preset_name)
    if preset is None:
        return {
            "preset_name": preset_name,
            "preset_exists": False,
            "preset_trade_enabled": None,
            "preset_validation_ok": None,
            "preset_validation_errors": [],
        }
    strategy = preset.get("strategy") if isinstance(preset.get("strategy"), dict) else {}
    validation = validate_strategy_config(preset)
    return {
        "preset_name": preset_name,
        "preset_exists": True,
        "preset_trade_enabled": bool(strategy.get("trade_enabled", True)),
        "preset_validation_ok": bool(validation.get("ok")),
        "preset_validation_errors": list(validation.get("errors") or []),
    }


def build_crypto_edge_strategy_readiness(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or REPO_ROOT)
    executable = set(REGISTRY_SUPPORTED)
    supported = set(config_tools.supported_strategies())
    config_only = config_tools.config_only_strategies()

    rows: list[dict[str, Any]] = []
    for spec in CRYPTO_EDGE_STRATEGIES:
        registry_executable = spec.name in executable
        config_supported = spec.name in supported
        config_only_reason = config_only.get(spec.name)
        preset = _preset_state(spec.preset_name)
        module_exists = (root / spec.module_relpath).is_file()
        status = _strategy_status(
            registry_executable=registry_executable,
            config_supported=config_supported,
            config_only=bool(config_only_reason),
            preset_exists=bool(preset["preset_exists"]),
        )
        rows.append(
            {
                "strategy": spec.name,
                "context_kind": spec.context_kind,
                "module_path": spec.module_relpath,
                "module_exists": module_exists,
                "registry_executable": registry_executable,
                "config_supported": config_supported,
                "config_only": bool(config_only_reason),
                "config_only_reason": config_only_reason,
                **preset,
                "status": status,
                "known_blockers": list(spec.known_blockers),
                "next_action": spec.next_action,
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1

    return {
        "artifact_type": "crypto_edge_strategy_readiness_v1",
        "ok": True,
        "read_only": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "row_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "strategies": rows,
        "limitations": [
            "does_not_start_or_modify_campaigns",
            "does_not_fetch_market_or_crypto_edge_data",
            "does_not_change_promotion_gate_qualification",
            "known_blockers_are_documented_research_status_not_profitability_evidence",
        ],
    }
