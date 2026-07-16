from __future__ import annotations

import logging
from typing import Any

from services.audit.operator_event_journal import append_operator_event

_LOG = logging.getLogger(__name__)


def strategy_state(cfg: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(cfg, dict):
        return {}
    strategy = cfg.get("strategy")
    return dict(strategy) if isinstance(strategy, dict) else {}


def record_strategy_config_change(
    *,
    pre_cfg: dict[str, Any],
    post_cfg: dict[str, Any],
    change_source: str,
    source: str,
    actor: str = "operator",
) -> dict[str, Any]:
    pre_strategy = strategy_state(pre_cfg)
    post_strategy = strategy_state(post_cfg)
    if pre_strategy == post_strategy:
        return {"ok": True, "skipped": True, "reason": "strategy_config_unchanged"}
    try:
        event = append_operator_event(
            actor=actor,
            action="strategy_config_change",
            target="user.yaml:strategy",
            result="success",
            reason=str(change_source or "strategy_config_update"),
            pre_state={"strategy": pre_strategy},
            post_state={"strategy": post_strategy},
            source=source,
            extra={"surface": "dashboard_operations", "change_source": str(change_source or "")},
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        _LOG.warning(
            "strategy_config_change operator event journal failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}
