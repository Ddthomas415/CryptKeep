"""Selected existing preflights with fake clients, not a production module import."""

import ast
from decimal import Decimal
import hashlib
import json
import logging
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def functions(path, names, namespace):
    source = path.read_bytes()
    tree = ast.parse(source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(selected) == len(names)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *selected], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)
    return hashlib.sha256(source).hexdigest()


class Fake:
    def __init__(self, venue, async_balance=False, async_permissions=False):
        self.id, self.async_balance, self.async_permissions = venue, async_balance, async_permissions
        self.awaited_balance = self.awaited_permissions = False
        self.coroutines = []

    def fetch_balance(self):
        value = {"free": {"ETH": 5}, "total": {"ETH": 5}, "info": {"data": []}}
        if not self.async_balance:
            return value
        async def observation():
            self.awaited_balance = True
            return value
        coroutine = observation(); self.coroutines.append(coroutine)
        return coroutine

    def v3PrivateGetBrokerageKeyPermissions(self):
        value = {"portfolio_uuid": "invented-portfolio"}
        if not self.async_permissions:
            return value
        async def observation():
            self.awaited_permissions = True
            return value
        coroutine = observation(); self.coroutines.append(coroutine)
        return coroutine

    def close_test_coroutines(self):
        for coroutine in self.coroutines:
            coroutine.close()


def main():
    path = ROOT / "services/execution/place_order.py"
    names = {"_float_or_none", "_split_symbol", "_coinbase_portfolio_uuid",
             "_coinbase_row_currency_code", "_coinbase_row_amount", "_coinbase_row_trade_spendable",
             "_coinbase_spendable_from_info_rows", "_extract_spendable_balance", "_enforce_funding_gate"}
    namespace = {"math": math, "_LOG": logging.getLogger("synthetic-preflight"),
                 "_parse_order_amount": lambda value: value,
                 "_parse_order_price": lambda value, **kwargs: value,
                 "decimal_value": lambda value, **kwargs: Decimal(str(value))}
    digest = functions(path, names, namespace)
    guard_path = ROOT / "services/execution/coinbase_portfolio_guard.py"
    guard = {}
    guard_digest = functions(guard_path, {"_get_portfolio_uuid", "_get_portfolio_currencies",
                                        "_split_symbol", "enforce_coinbase_quote_account_available"}, guard)
    results = []
    for mode in ["sync_funding_control", "async_balance", "async_permissions"]:
        fake = Fake("coinbase" if mode == "async_permissions" else "invented-other-venue",
                    async_balance=mode == "async_balance", async_permissions=mode == "async_permissions")
        try:
            if mode == "async_permissions":
                guard["enforce_coinbase_quote_account_available"](fake, "ETH/USD")
            else:
                namespace["_enforce_funding_gate"](fake, symbol="ETH/USD", side="sell",
                    amount=1, price=10, order_type="limit")
            error = None
        except AttributeError:
            error = "AttributeError_on_unawaited_result"
        finally:
            fake.close_test_coroutines()
        assert (error is None) == (mode == "sync_funding_control")
        assert not fake.awaited_balance and not fake.awaited_permissions
        results.append({"case": mode, "result": error or "funding_control_passed",
                        "async_balance_awaited": fake.awaited_balance,
                        "async_permissions_awaited": fake.awaited_permissions})
    tree = ast.parse(path.read_bytes())
    entry = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "place_order_async")
    bare_preflights = [n.value.func.id for n in entry.body if isinstance(n, ast.Expr)
                      and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
                      and n.value.func.id in {"_enforce_funding_gate", "enforce_coinbase_quote_account_available"}]
    assert set(bare_preflights) == {"_enforce_funding_gate", "enforce_coinbase_quote_account_available"}
    print(json.dumps({"qualification": "SHOWN selected source and fake client, not current runtime impact",
        "cases": results, "unawaited_preflight_calls_in_async_entry": bare_preflights,
        "source_sha256": {str(path.relative_to(ROOT)): digest, str(guard_path.relative_to(ROOT)): guard_digest},
        "orders_or_private_requests": False}, indent=2))


if __name__ == "__main__":
    main()
