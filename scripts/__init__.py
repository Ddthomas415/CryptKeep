"""Compatibility imports for relocated script modules."""
from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import sys
from types import ModuleType

_ALIASES = {
    "cancel_intent": "scripts.live.cancel_intent",
    "find_strategy_signal_candidates": "scripts.dev.find_strategy_signal_candidates",
    "inject_test_fill": "scripts.dev.inject_test_fill",
    "live_submit_intent": "scripts.live.live_submit_intent",
    "recommend_model_switch": "scripts.dev.recommend_model_switch",
    "reconcile_order_dedupe": "scripts.dev.reconcile_order_dedupe",
    "record_dummy_fill": "scripts.dev.record_dummy_fill",
    "replay_paper_losses": "scripts.dev.replay_paper_losses",
    "run_bot_runner": "scripts.compat.run_bot_runner",
    "run_crypto_edge_collector_loop": "scripts.data.run_crypto_edge_collector_loop",
    "run_intent_executor": "scripts.compat.run_intent_executor",
    "run_intent_executor_safe": "scripts.live.run_intent_executor_safe",
    "run_intent_reconciler_safe": "scripts.live.run_intent_reconciler_safe",
    "run_pipeline_loop": "scripts.compat.run_pipeline_loop",
    "run_pipeline_once": "scripts.compat.run_pipeline_once",
    "run_strategy_evidence_cycle": "scripts.data.run_strategy_evidence_cycle",
    "run_ws_ticker_feed": "scripts.data.run_ws_ticker_feed",
    "show_live_gate_inputs": "scripts.live.show_live_gate_inputs",
    "start_supervisor": "scripts.compat.start_supervisor",
    "supervisor": "scripts.compat.supervisor",
    "supervisor_ctl": "scripts.compat.supervisor_ctl",
    "sync_briefcase_requires": "scripts.release.sync_briefcase_requires",
}


def _load_alias(name: str) -> ModuleType:
    target = _ALIASES[name]
    module = importlib.import_module(target)
    globals()[name] = module
    sys.modules[f"{__name__}.{name}"] = module
    return module


def __getattr__(name: str) -> ModuleType:
    if name in _ALIASES:
        return _load_alias(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_ALIASES))


class _ScriptAliasLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, alias: str) -> None:
        self.fullname = fullname
        self.alias = alias

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType:
        module = importlib.import_module(self.alias)
        sys.modules[self.fullname] = module
        return module

    def exec_module(self, module: ModuleType) -> None:
        return None


class _ScriptAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: object | None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        prefix = f"{__name__}."
        if not fullname.startswith(prefix):
            return None
        name = fullname.removeprefix(prefix)
        alias = _ALIASES.get(name)
        if not alias:
            return None
        return importlib.machinery.ModuleSpec(
            fullname,
            _ScriptAliasLoader(fullname, alias),
            origin=f"alias:{alias}",
        )


if not any(isinstance(finder, _ScriptAliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _ScriptAliasFinder())
