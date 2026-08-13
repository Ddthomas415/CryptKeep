from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_intent_table_mutations_stay_behind_queue_store() -> None:
    """Live intent rows/events must be mutated through LiveIntentQueueSQLite."""

    scanned_roots = [ROOT / "dashboard", ROOT / "scripts", ROOT / "services", ROOT / "storage"]
    allowed = {
        Path("storage/live_intent_queue_sqlite.py"),
    }
    table_tokens = {
        "live_trade_intents",
        "live_trade_intent_events",
        "live_consumer_state",
    }
    mutation_tokens = {
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "ALTER TABLE ",
        "DROP TABLE ",
        "CREATE TABLE ",
        "INSERT OR ",
    }

    violations: list[str] = []
    for scan_root in scanned_roots:
        for path in sorted(scan_root.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if not any(token in text for token in table_tokens):
                continue
            if any(token in text for token in mutation_tokens):
                violations.append(str(rel))

    assert violations == []
