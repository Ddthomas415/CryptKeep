# Coinbase balance paging: installed-source verification

2026-10-28. Active role AUDITOR. Finding SHOWN; production repair INCOMPLETE.
This is the existing queued fix1 dependency, not a new market experiment.

## Result

The installed sync and async Coinbase `fetch_balance` methods each make only
one balance endpoint call in the inspected spot branch, then pass that response
to the parser. Continuation cursors are not followed. Passing `paginate=True`
does not add paging in the tested default path. This prevents using a missing
holding as proof of zero account exposure for the adopted per-asset cap.

SHOWN installed version: `ccxt/__init__.py:25` declares4.5.48, matching
`requirements-pinned.txt:35` and `requirements-dev-pinned.txt:35`.
This is the local installation, not proof of the server's version or live state.

## Sources And Narrow Proof

- `.venv/lib/python3.12/site-packages/ccxt/coinbase.py:426` sets the described
  fetchBalance option to v2PrivateGetAccounts; fetch_balance at2344 selects v2
  by default or v3 by parameter/option, requests limit250 once and parses once.
- `.venv/lib/python3.12/site-packages/ccxt/async_support/coinbase.py:427` and
  fetch_balance at2345 have the corresponding awaited behavior.
- The installed fetch_accounts_v2 helper has a separate optional cursor pager
  (sync569/async570). Its existence does not make fetch_balance call it, and
  account-list output is not automatically the existing balance consumer schema.
- `services/security/exchange_factory.py:24` creates the preferred client and
  does not override Coinbase's fetchBalance option. The inspected preferred
  `LiveExchangeAdapter.fetch_balance` at61 and funding gate at
  `services/execution/place_order.py:195` call fetch_balance without parameters.
  Legacy ExchangeClient allows caller options; actual runtime options were not
  read, so do not generalize the default to every configured instance.
- `place_order.py:102` reads raw info.data rows and filters spendability/portfolio;
  its aggregate free/total fallback is a different path. A repair must preserve
  coherent raw rows and aggregates, not replace one while leaving the other
  truncated. V3's native accounts field must not be silently represented as
  already compatible with this v2-row consumer.

Ran the saved probe:

```sh
./.venv/bin/python -I -S -B docs/review_artifacts/coinbase_balance_paging_review_20261028/probe.py
```

Exit0, six selected-method assertions passed: sync/async x default-v2,
explicit-v3 and default-v2-with-paginate. The unchanged selected method body
was AST-loaded with deferred annotations; fake helpers and transport supplied
one response carrying a nonempty continuation. Every case made exactly one
fake endpoint call. The repeat solely to save machine-readable output also
passed; RESULT.json includes both installed source hashes.

No ccxt module, production client, credential loader or exchange factory was
imported. load_markets and parse_custom_balance were stubs, not tested CCXT
internals. This demonstrates the selected method's control flow under those
fakes, not real server paging, a complete balance result or an actual missing
holding. The installed parser was separately read: it already adds same-code
rows; this review does not invent an overwrite defect there.

## Repair Requirements, Not Implementation

Reuse one existing-client balance boundary covering sync and async callers.
Explicitly handle supported v2/v3 continuation semantics with bounded pages,
deadline and repeated-cursor detection. Merge and validate all raw accounts
before deriving the corresponding aggregate view. Deduplicate by verified
account identity; conflicting duplicate rows are unknown, not additive money.
Incomplete/failed pages must not become a complete snapshot or zero holding.

Retain total/locked holdings for cap exposure separately from spendable funds
for buys/sells. Reuse the account-wide scope and existing independent gates;
missing funding evidence can refuse a sell, which is a separate constraint from
the position cap's promise not to add an over-cap reducing-sell prohibition.
Do not claim a pager supplies pending external orders or an atomic exchange
snapshot; those remain separate cap-contract evidence requirements.

Required future tests: two-page sync/async merging with a page-two held asset,
raw-row funding selection, second-page failure, repeated/invalid cursor,
duplicate/conflicting account IDs, bounds and account isolation. These tests
were not run here. No production patch, upgrade, new endpoint or private account
read is authorized by this source audit. A newer release's reported v3 fix is
CLAIMED in the handoff; no downloaded release or changelog was verified here.

## Pilot Check At 08:53 New York

The reloaded job showed runs0, never exited and new log paths. No slot artifacts
exist; new log files do not yet exist. The next opportunity is09:05, so this is
not another failed post-repair run. No forced capture, job/source modification,
window extension or passive wait occurred. Unattended proof remains INCOMPLETE.
