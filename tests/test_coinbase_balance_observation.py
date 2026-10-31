"""Reachable paging integration with invented SDK responses and no private I/O."""

import asyncio
from copy import deepcopy

import pytest

from services.execution import coinbase_balance_observation as bridge
from tests.test_coinbase_account_pages_installed_sdk import offline, pages, bind_dispatch


def policy(version="v2"):
    return {"version": version, "scope": ["coinbase", "invented-boundary"], "page_size": 100,
            "max_pages": 3, "max_rows": 20, "max_json_bytes": 20000, "timeout_seconds": 10}


def supplied_pages(version):
    out = pages(version)
    for page in out:
        for row in page["data" if version == "v2" else "accounts"]:
            row["portfolio_id" if version == "v2" else "retail_portfolio_id"] = "p-one"
    return out


def run(version, asynchronous, inspect_result, responses=None, mutate=None):
    async def scenario():
        import ccxt
        import ccxt.async_support as async_sdk
        cls = async_sdk.coinbase if asynchronous else ccxt.coinbase
        client = cls({"apiKey": None, "secret": None, "enableRateLimit": False,
                      "options": {bridge.POLICY_KEY: policy(version)}})
        calls = []
        bind_dispatch(client, version, supplied_pages(version) if responses is None else responses, calls, asynchronous)
        if mutate is not None:
            mutate(client)
        try:
            value = await bridge.read_balance_async(client) if asynchronous else bridge.read_balance_sync(client)
            inspect_result(value, client, calls)
        finally:
            if asynchronous:
                await client.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_paging_reaches_real_parser_without_creating_authority(version, asynchronous):
    def check(balance, client, calls):
        assert len(calls) == 2 and balance["total"]["SOL"] == 7
        evidence = balance[bridge.POLICY_KEY]
        assert evidence["all_supplied_pages_returned"] and evidence["native_total_fractions"]["ETH"] == [5, 1]
        assert all(evidence[key] is False for key in ["scope_authenticated", "spendable_verified", "transport_limits_verified", "execution_authority"])
        assert ("accounts" in balance["info"]) == (version == "v3")
    run(version, asynchronous, check)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_missing_policy_retains_exact_legacy_balance(asynchronous):
    sentinel = {"legacy": "unchanged"}
    def setup(client):
        client.options.pop(bridge.POLICY_KEY)
        client.fetch_balance = lambda: sentinel
    def check(value, client, calls):
        assert value is sentinel and calls == []
    run("v2", asynchronous, check, mutate=setup)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("failure", ["page_two", "cursor", "parser", "raw_info", "precision", "metadata_collision"])
def test_configured_failure_never_uses_legacy_fallback(version, asynchronous, failure):
    responses = supplied_pages(version)
    def setup(client):
        if failure == "parser":
            client.parse_custom_balance = lambda *args: {"secret": "invalid parser"}
        if failure == "raw_info":
            original = client.parse_custom_balance
            def changed(*args):
                result = original(*args); result["info"] = {}; return result
            client.parse_custom_balance = changed
        if failure == "metadata_collision":
            original = client.parse_custom_balance
            def collided(*args):
                result = original(*args); result[bridge.POLICY_KEY] = {}; return result
            client.parse_custom_balance = collided
    if failure == "page_two":
        responses[1] = RuntimeError("private detail must not leak")
    elif failure == "cursor":
        responses[1] = responses[0]
    elif failure == "precision":
        row = responses[1]["data" if version == "v2" else "accounts"][-1]
        if version == "v2": row["balance"]["amount"] = "9007199254740993"
        else:
            row["available_balance"]["value"] = "9007199254740993"; row["hold"]["value"] = "0"
    with pytest.raises(bridge.BalanceObservationError) as error:
        run(version, asynchronous, lambda *args: pytest.fail("must withhold balance"), responses, setup)
    assert "private detail" not in str(error.value)


@pytest.mark.parametrize("bad", [None, {}, {"extra": 1}, {**policy(), "timeout_seconds": 0},
                                {**policy(), "timeout_seconds": float("inf")}, {**policy(), "max_pages": True},
                                {**policy(), "version": "guess"}, {**policy(), "scope": ["other", "x"]}])
def test_present_invalid_policy_does_not_fall_back(bad):
    def setup(client): client.options[bridge.POLICY_KEY] = bad
    with pytest.raises(ValueError):
        run("v2", False, lambda *args: pytest.fail("bad policy accepted"), mutate=setup)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_parser_time_is_inside_result_acceptance_window(monkeypatch, asynchronous):
    now = [1.0]; monkeypatch.setattr(bridge, "monotonic", lambda: now[0])
    def setup(client):
        original = client.parse_custom_balance
        def slow(*args):
            value = original(*args); now[0] = 20; return value
        client.parse_custom_balance = slow
    with pytest.raises(bridge.BalanceObservationError, match="paging_window_expired"):
        run("v2", asynchronous, lambda *args: pytest.fail("late result"), mutate=setup)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_regressing_clock_refuses_before_balance_endpoint(monkeypatch, asynchronous):
    values = iter([1.0, 0.0]); monkeypatch.setattr(bridge, "monotonic", lambda: next(values))
    with pytest.raises(bridge.BalanceObservationError):
        run("v2", asynchronous, lambda *args: pytest.fail("regressed clock"))


def test_async_cancel_is_not_transformed_to_balance_or_retried():
    responses = supplied_pages("v3"); responses[1] = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        run("v3", True, lambda *args: pytest.fail("cancelled balance"), responses)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_common_order_preflight_uses_paged_observation_and_keeps_existing_guards(version, asynchronous):
    async def scenario():
        import ccxt
        import ccxt.async_support as async_sdk
        from tests.test_coinbase_sync_preflight import namespace, SubmissionReached
        from tests.test_proposed_async_balance_preflight import namespace as async_namespace, APPLICATION, SubmissionReached as AsyncReached
        client = (async_sdk.coinbase if asynchronous else ccxt.coinbase)(
            {"apiKey": None, "secret": None, "options": {bridge.POLICY_KEY: policy(version)}})
        calls, permissions = [], []
        bind_dispatch(client, version, supplied_pages(version), calls, asynchronous)
        def key_permissions():
            permissions.append("read"); return {"portfolio_uuid": "p-one"}
        client.v3PrivateGetBrokerageKeyPermissions = key_permissions
        def submit(*args): raise SubmissionReached()
        async def async_submit(*args): raise AsyncReached()
        client.create_order = async_submit if asynchronous else submit
        try:
            error = RuntimeError if version == "v3" else (AsyncReached if asynchronous else SubmissionReached)
            with pytest.raises(error) as caught:
                if asynchronous:
                    await async_namespace(APPLICATION, [], side="sell")["place_order_async"](client)
                else:
                    namespace()["place_order"](client)
            if version == "v3": assert "portfolio_account_unavailable" in str(caught.value)
            assert len(calls) == 2 and len(permissions) == 1
        finally:
            if asynchronous: await client.close()
    asyncio.run(scenario())


def test_preferred_factory_copies_policy_and_default_is_unchanged(monkeypatch):
    from services.security.exchange_factory import make_exchange
    monkeypatch.delenv("CBP_VENUE", raising=False)
    chosen = policy(); client = make_exchange("coinbase", {}, balance_paging_policy=chosen)
    chosen["scope"][1] = "mutated"
    assert client.options[bridge.POLICY_KEY]["scope"][1] == "invented-boundary"
    default = make_exchange("coinbase", {})
    assert bridge.POLICY_KEY not in default.options
    with pytest.raises(ValueError): make_exchange("kraken", {}, balance_paging_policy=policy())


def test_preferred_adapter_forwards_explicit_policy_and_fetches_complete_view(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import ccxt
    import services.execution.live_exchange_adapter as module
    client = ccxt.coinbase({"apiKey": None, "secret": None})
    calls = []
    bind_dispatch(client, "v2", supplied_pages("v2"), calls, False)
    def factory(venue, creds, **kwargs):
        client.options[bridge.POLICY_KEY] = deepcopy(kwargs["balance_paging_policy"])
        return client
    monkeypatch.setattr(module, "load_exchange_credentials", lambda venue: {"apiKey": "invented", "secret": "invented"})
    monkeypatch.setattr(module, "make_exchange", factory)
    adapter = module.LiveExchangeAdapter("coinbase", balance_paging_policy=policy())
    assert adapter.fetch_balance()["total"]["SOL"] == 7 and len(calls) == 2
    monkeypatch.setattr(module, "load_exchange_credentials", lambda *args: pytest.fail("invalid policy must precede credentials"))
    with pytest.raises(ValueError): module.LiveExchangeAdapter("coinbase", balance_paging_policy={})
