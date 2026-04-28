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


def test_scan_catches_dynamic_getattr_create_order(tmp_path: Path) -> None:
    violating = tmp_path / "services" / "execution" / "rogue_getattr.py"
    violating.parent.mkdir(parents=True, exist_ok=True)
    attr_name = "create_" + "order"
    violating.write_text(
        "def run(ex):\n"
        f"    return getattr(ex, {attr_name!r})('BTC/USD', 'limit', 'buy', 0.1, 100.0, {{}})\n",
        encoding="utf-8",
    )

    hits = scan(tmp_path)

    assert len(hits) == 1
    assert hits[0]["file"] == "services/execution/rogue_getattr.py"


def test_scan_catches_dynamic_getattr_create_order_camel_case(tmp_path: Path) -> None:
    violating = tmp_path / "services" / "execution" / "rogue_getattr_camel.py"
    violating.parent.mkdir(parents=True, exist_ok=True)
    attr_name = "create" + "Order"
    violating.write_text(
        "def run(ex):\n"
        f"    return getattr(ex, {attr_name!r})('BTC/USD', 'limit', 'buy', 0.1, 100.0, {{}})\n",
        encoding="utf-8",
    )

    hits = scan(tmp_path)

    assert len(hits) == 1
    assert hits[0]["file"] == "services/execution/rogue_getattr_camel.py"


def test_scan_does_not_flag_create_order_method_definition(tmp_path: Path) -> None:
    harmless = tmp_path / "tests" / "test_exchange_double.py"
    harmless.parent.mkdir(parents=True, exist_ok=True)
    harmless.write_text(
        "class FakeExchange:\n"
        "    def create_order(self, *args, **kwargs):\n"
        "        return {'id': 'fake'}\n",
        encoding="utf-8",
    )

    assert scan(tmp_path) == []
