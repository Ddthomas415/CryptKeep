"""Native v3 portfolio/funding compatibility, invented observations only."""
import asyncio
from copy import deepcopy
from fractions import Fraction

import pytest

from tests.test_coinbase_account_pages_installed_sdk import offline, bind_dispatch
from tests.test_coinbase_balance_observation import policy
from tests.test_coinbase_sync_preflight import namespace, SubmissionReached


def row(asset="USD", value="100", *, identity="usd", portfolio="p-one", **changes):
    return {"uuid": identity, "currency": asset, "retail_portfolio_id": portfolio,
            "type": "ACCOUNT_TYPE_FIAT" if asset == "USD" else "ACCOUNT_TYPE_CRYPTO",
            "active": True, "ready": True, "deleted_at": None,
            "available_balance": {"value": value, "currency": asset},
            "hold": {"value": "999", "currency": asset}} | changes


def balance(rows=None):
    return {"info": {"accounts": rows if rows is not None else [row(), row("ETH", "5", identity="eth")]},
            "free": {"USD": 100, "ETH": 5}}


def client(observation):
    class Observed:
        id = "coinbase"
        def v3PrivateGetBrokerageKeyPermissions(self): return {"portfolio_uuid": "p-one"}
        def fetch_balance(self): return observation
    return Observed()


def test_valid_v3_accounts_pass_both_guards():
    ns = namespace()
    b = balance(); ex = client(b)
    ns["enforce_coinbase_quote_account_available"](ex, "ETH/USD")
    assert ns["_extract_spendable_balance"](ex, b, "ETH") == (5, "coinbase.v3_available+free_min")
    ns["_enforce_funding_gate"](ex, symbol="ETH/USD", side="sell", amount=1, price=10, order_type="limit")


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("side", ["buy", "sell"])
def test_real_sdk_pages_reach_common_preflight(asynchronous, side):
    async def scenario():
        import ccxt
        import ccxt.async_support as sdk_async
        from tests.test_proposed_async_balance_preflight import namespace as async_ns, APPLICATION, SubmissionReached as AsyncReached
        cls = sdk_async.coinbase if asynchronous else ccxt.coinbase
        ex = cls({"apiKey": None, "secret": None, "options": {"cbp_balance_paging": policy("v3")}})
        calls, perms = [], []
        responses = [{"accounts": [row()], "has_next": True, "cursor": "next"},
                     {"accounts": [row("ETH", "5", identity="eth")], "has_next": False, "cursor": ""}]
        bind_dispatch(ex, "v3", responses, calls, asynchronous)
        def permissions(): perms.append(1); return {"portfolio_uuid": "p-one"}
        ex.v3PrivateGetBrokerageKeyPermissions = permissions
        def submit(*args): raise SubmissionReached()
        async def async_submit(*args): raise AsyncReached()
        ex.create_order = async_submit if asynchronous else submit
        try:
            with pytest.raises(AsyncReached if asynchronous else SubmissionReached):
                if asynchronous: await async_ns(APPLICATION, [], side=side)["place_order_async"](ex)
                else: namespace(side=side)["place_order"](ex)
            assert len(calls) == 2 and len(perms) == 1
        finally:
            if asynchronous: await ex.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("changes", [{"active": False}, {"active": "true"}, {"ready": False},
    {"ready": None}, {"deleted_at": "2026-01-01"}, {"type": "ACCOUNT_TYPE_STAKING"},
    {"name": "Staked USD"}, {"retail_portfolio_id": "other"}])
def test_ineligible_or_other_portfolio_cannot_fund_or_supply_quote(changes):
    ns = namespace(); b = balance([row(**changes)])
    with pytest.raises(RuntimeError, match="portfolio_account_unavailable"):
        ns["enforce_coinbase_quote_account_available"](client(b), "ETH/USD")
    value, _ = ns["_extract_spendable_balance"](client(b), b, "USD")
    assert value == 0


@pytest.mark.parametrize("field", ["active", "ready", "deleted_at"])
def test_missing_eligibility_refuses_quote(field):
    r = row(); r.pop(field); b = balance([r])
    with pytest.raises(RuntimeError):
        namespace()["enforce_coinbase_quote_account_available"](client(b), "ETH/USD")


@pytest.mark.parametrize("changes", [{"retail_portfolio_id": None}, {"uuid": None}, {"currency": None},
    {"available_balance": {"value": "NaN", "currency": "USD"}},
    {"available_balance": {"value": "-1", "currency": "USD"}},
    {"available_balance": {"value": "1e999999999", "currency": "USD"}},
    {"available_balance": {"value": "1" * 129, "currency": "USD"}},
    {"available_balance": {"value": True, "currency": "USD"}},
    {"available_balance": {"value": "5", "currency": "EUR"}}, {"hold": {"value": "1", "currency": "EUR"}}])
def test_invalid_native_evidence_refuses_without_aggregate_fallback(changes):
    ns = namespace(); b = balance([row(**changes)])
    with pytest.raises(RuntimeError): ns["_extract_spendable_balance"](client(b), b, "USD")


def test_duplicate_identity_is_not_double_counted_and_conflict_refused():
    ns = namespace(); r = row(value="3"); b = balance([r, deepcopy(r)])
    assert ns["_extract_spendable_balance"](client(b), b, "USD")[0] == 3
    b["info"]["accounts"][1]["available_balance"]["value"] = "4"
    with pytest.raises(RuntimeError): ns["_extract_spendable_balance"](client(b), b, "USD")


def test_held_and_other_portfolio_funds_not_counted_and_free_min_preserved():
    ns = namespace(); b = balance([row(value="3"), row(value="900", identity="other", portfolio="other")])
    b["free"]["USD"] = 2
    assert ns["_extract_spendable_balance"](client(b), b, "USD")[0] == 2


def test_native_decimal_sum_does_not_round_up():
    ns = namespace(); b = balance([row(value="0.123456789123456789"), row(value="0.2", identity="two")])
    value, _ = ns["_extract_spendable_balance"](client(b), b, "USD")
    assert 0 < Fraction(str(value)) <= Fraction("0.123456789123456789") + Fraction("0.2")


def test_mixed_native_versions_refuse():
    ns = namespace(); b = balance(); b["info"]["data"] = []
    with pytest.raises(RuntimeError): ns["_extract_spendable_balance"](client(b), b, "USD")


def test_provider_error_and_missing_declared_accounts_refuse():
    ns = namespace(); b = balance(); b["info"]["error"] = "invented rejection"
    with pytest.raises(RuntimeError): ns["_extract_spendable_balance"](client(b), b, "USD")
    b = {"info": {}, "cbp_balance_paging": {"version": "v3"}, "free": {"USD": 999}}
    with pytest.raises(RuntimeError): ns["_extract_spendable_balance"](client(b), b, "USD")


def test_exact_v2_function_body_preserved_outside_explicit_v3_branch():
    import ast
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    base = root / "docs/review_artifacts/coinbase_v3_guards_20261030/before"
    for filename, name in [("place_order.py", "_coinbase_spendable_from_info_rows"),
                           ("coinbase_portfolio_guard.py", "_get_portfolio_currencies")]:
        current = ast.parse((root / "services/execution" / filename).read_bytes())
        before = ast.parse((base / filename).read_bytes())
        def definitions(tree):
            return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        old, new = definitions(before), definitions(current)
        assert old.keys() == new.keys()
        assert {k for k in old if ast.dump(old[k]) != ast.dump(new[k])} == {name}
        at = 1
        assert isinstance(new[name].body[at], ast.ImportFrom)
        assert new[name].body[at].module == "services.execution.coinbase_v3_accounts"
        assert isinstance(new[name].body[at+1], ast.Assign) and isinstance(new[name].body[at+2], ast.If)
        del new[name].body[at:at+3]
        assert ast.dump(old[name]) == ast.dump(new[name])
