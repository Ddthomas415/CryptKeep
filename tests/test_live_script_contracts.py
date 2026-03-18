from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APPROVED_SANDBOX_FALSE_SCRIPTS = {
    "scripts/cancel_intent.py",
    "scripts/reconcile_order_dedupe.py",
}


def _sandbox_false_scripts() -> set[str]:
    hits: set[str] = set()
    for path in (ROOT / "scripts").rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if "sandbox=False" in text:
            hits.add(rel)
    return hits


def test_only_approved_scripts_use_sandbox_false_exchange_clients() -> None:
    assert _sandbox_false_scripts() == APPROVED_SANDBOX_FALSE_SCRIPTS


def test_cancel_intent_script_is_cancel_only() -> None:
    text = (ROOT / "scripts" / "cancel_intent.py").read_text(encoding="utf-8", errors="replace")
    assert "client.cancel_intent(" in text
    assert "submit_order(" not in text
    assert "place_order(" not in text
    assert ".create_" + "order(" not in text


def test_reconcile_order_dedupe_script_is_read_only_reconcile() -> None:
    text = (ROOT / "scripts" / "reconcile_order_dedupe.py").read_text(encoding="utf-8", errors="replace")
    assert "client.fetch_open_orders(" in text
    assert "client.fetch_order(" in text
    assert "submit_order(" not in text
    assert "place_order(" not in text
    assert ".create_" + "order(" not in text
