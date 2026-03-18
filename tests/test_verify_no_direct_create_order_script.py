from __future__ import annotations

from pathlib import Path

from scripts.verify_no_direct_create_order import scan


def test_scan_catches_direct_create_order_with_whitespace(tmp_path: Path) -> None:
    violating = tmp_path / "services" / "execution" / "rogue.py"
    violating.parent.mkdir(parents=True, exist_ok=True)
    create_order_call = ".create_" + "order ("
    violating.write_text(
        "def run(ex):\n"
        f"    return ex{create_order_call}\n"
        "        'BTC/USD', 'limit', 'buy', 0.1, 100.0, {}\n"
        "    )\n",
        encoding="utf-8",
    )

    hits = scan(tmp_path)

    assert len(hits) == 1
    assert hits[0]["file"] == "services/execution/rogue.py"
