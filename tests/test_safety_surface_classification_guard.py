from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "architecture" / "safety_surface_classification.md"

SOURCE_ROOTS = (
    ROOT / "services",
    ROOT / "scripts",
)

GOVERNED_LIVE_PATHS = (
    ROOT / "services" / "execution" / "_executor_submit.py",
    ROOT / "services" / "execution" / "_executor_reconcile.py",
    ROOT / "services" / "execution" / "exchange_client.py",
    ROOT / "services" / "execution" / "live_executor.py",
)

LEGACY_CLIENT_OID_IMPORTERS = {
    "services/execution/compat/intent_executor.py",
    "services/execution/intent_executor.py",
}

LEGACY_LIVE_TRADER_STUBS = (
    ROOT / "services" / "live_trader_multi" / "main.py",
    ROOT / "services" / "live_trader_fleet" / "main.py",
)


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _source_files() -> list[Path]:
    out: list[Path] = []
    for root in SOURCE_ROOTS:
        out.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(out)


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _files_referencing(needle: str) -> set[str]:
    hits: set[str] = set()
    for path in _source_files():
        if needle in path.read_text(encoding="utf-8"):
            hits.add(_rel(path))
    return hits


def test_safety_surface_classification_doc_names_authority_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Backlog link: `REMAINING_TASKS.md` Deferred Structure And Research Hygiene item",
        "`services/admin/kill_switch.py` | Canonical operator kill-switch state",
        "`services/risk/killswitch.py` | Live-order safety probe",
        "`services/risk/kill_conditions.py` | Strategy-runner risk-block cooldown logic",
        "`services/risk/live_risk_gates.py` | Canonical live hard-limit gate",
        "`services/execution/client_order_id.py` | Canonical live client-order-id builder",
        "`services/execution/client_oid.py` | Legacy/compat client OID builder",
        "`services/live_trader_multi/main.py` and `services/live_trader_fleet/main.py` | Duplicate dry-run legacy live runner stubs",
        "`tests/test_safety_surface_classification_guard.py` pins the visible source-tree",
    ]
    missing = [item for item in required if item not in text]
    assert not missing


def test_governed_live_paths_use_canonical_client_order_id_builder() -> None:
    for path in GOVERNED_LIVE_PATHS:
        text = path.read_text(encoding="utf-8")
        assert "services.execution.client_order_id" in text or "make_client_order_id" in text, _rel(path)
        assert "services.execution.client_oid" not in text, _rel(path)
        assert "make_client_oid32" not in text, _rel(path)


def test_legacy_client_oid_importers_stay_in_compatibility_paths() -> None:
    importers = _files_referencing("services.execution.client_oid")
    importers.discard("services/execution/client_oid.py")
    assert importers == LEGACY_CLIENT_OID_IMPORTERS

    function_users = _files_referencing("make_client_oid32")
    function_users.discard("services/execution/client_oid.py")
    assert function_users == LEGACY_CLIENT_OID_IMPORTERS


def test_legacy_live_trader_stubs_do_not_gain_real_order_routing_imports() -> None:
    forbidden_modules = {
        "ccxt",
        "services.execution._executor_submit",
        "services.execution.exchange_client",
        "services.execution.live_exchange_adapter",
        "services.execution.live_intent_consumer",
        "services.execution.order_router",
        "services.execution.place_order",
    }

    for path in LEGACY_LIVE_TRADER_STUBS:
        text = path.read_text(encoding="utf-8")
        imports = _imported_modules(path)
        assert "dry-run mode" in text
        assert 'venue = "simulated"' in text
        assert not (imports & forbidden_modules), f"{_rel(path)} imports {imports & forbidden_modules}"


def test_kill_switch_and_risk_gate_authorities_remain_separate() -> None:
    assert "services.admin.kill_switch" in (ROOT / "scripts" / "killswitch.py").read_text(encoding="utf-8")
    execution_switch = (ROOT / "services" / "execution" / "kill_switch.py").read_text(encoding="utf-8")
    assert "from services.admin.kill_switch import get_state, set_armed" in execution_switch
    assert "from services.risk import killswitch" in (ROOT / "services" / "execution" / "place_order.py").read_text(encoding="utf-8")
    assert "services.risk.kill_conditions" in (ROOT / "services" / "execution" / "strategy_runner.py").read_text(encoding="utf-8")

    executor_importers = {
        _rel(path)
        for path in _source_files()
        if "services.risk.live_risk_gates" in path.read_text(encoding="utf-8")
    }
    assert "services/execution/_executor_submit.py" in executor_importers
    assert "services/execution/_executor_reconcile.py" in executor_importers
    assert "services/execution/live_executor.py" in executor_importers
