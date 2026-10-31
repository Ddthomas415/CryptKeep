"""Audit selected installed methods with fake transport; no ccxt/client imports."""

import ast
import asyncio
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / ".venv/lib/python3.12/site-packages/ccxt"


def selected_method(path):
    source = path.read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "coinbase")
    method = next(n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "fetch_balance")
    describe = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "describe")
    defaults = [
        value.value
        for node in ast.walk(describe)
        if isinstance(node, ast.Dict)
        for key, value in zip(node.keys, node.values)
        if isinstance(key, ast.Constant) and key.value == "fetchBalance"
        and isinstance(value, ast.Constant) and isinstance(value.value, str)
    ]
    assert defaults == ["v2PrivateGetAccounts"]
    # Future annotations avoid importing CCXT's type aliases; the body is unchanged.
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["fetch_balance"], defaults[0], hashlib.sha256(source.encode()).hexdigest()


class FakeTransport:
    def __init__(self, default):
        self.options = {"fetchBalance": default}
        self.calls = []

    def safe_bool(self, obj, key, default):
        return obj.get(key, default)

    def safe_string(self, obj, key, default):
        return obj.get(key, default)

    def omit(self, obj, keys):
        return {k: v for k, v in obj.items() if k not in keys}

    def handle_market_type_and_params(self, name, market, params):
        return "spot", dict(params)

    def extend(self, request, params):
        return dict(request, **params)

    def parse_custom_balance(self, response, params):
        return response

    def load_markets(self):
        return None

    def response(self, route, params):
        self.calls.append({"route": route, "params": dict(params)})
        assert "starting_after" not in params and "cursor" not in params
        if route == "v2":
            return {"data": [{"id": "first-wallet", "currency": {"code": "BTC"}}], "pagination": {"next_starting_after": "page-two"}}
        return {"accounts": [{"uuid": "first-wallet", "currency": "BTC"}], "has_next": True, "cursor": "page-two"}

    def v2PrivateGetAccounts(self, params):
        return self.response("v2", params)

    def v3PrivateGetBrokerageAccounts(self, params):
        return self.response("v3", params)


class AsyncFakeTransport(FakeTransport):
    async def load_markets(self):
        return None

    async def v2PrivateGetAccounts(self, params):
        return self.response("v2", params)

    async def v3PrivateGetBrokerageAccounts(self, params):
        return self.response("v3", params)


def main():
    results = []
    inputs = {}
    for asynchronous, relative in [(False, "coinbase.py"), (True, "async_support/coinbase.py")]:
        path = PACKAGE / relative
        method, default, digest = selected_method(path)
        inputs[str(path.relative_to(ROOT))] = digest
        for params in [{}, {"v3": True}, {"paginate": True}]:
            fake = (AsyncFakeTransport if asynchronous else FakeTransport)(default)
            response = asyncio.run(method(fake, dict(params))) if asynchronous else method(fake, dict(params))
            assert len(fake.calls) == 1
            rows = response.get("data", response.get("accounts"))
            assert len(rows) == 1
            assert (response.get("pagination") or {}).get("next_starting_after") == "page-two" or response.get("cursor") == "page-two"
            results.append({"async": asynchronous, "params": params, "calls": fake.calls, "continuation_retained_but_not_followed": True})
    print(json.dumps({"evidence": "SHOWN selected installed method with fake helpers/transport, not authenticated behavior or full CCXT parser", "cases_passed": len(results), "inputs_sha256": inputs, "results": results}, indent=2))


if __name__ == "__main__":
    main()
