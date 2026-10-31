# Coinbase execution product-mode guard: local repair

2026-10-28. ENGINEER stage; HIGH risk financial execution gating.
Status ACCEPTED_WITH_RISK after separate review of the exact local repair and
offline proof. No deployment or account access.

## Change Applied

Operator requested "fix it" after the checkpoint prototype. Chose the concrete
existing execution-path gap rather than activating an unwired state prototype.
Preserved pre-change sources/tests under review_artifacts/coinbase_mode_gate_20261028/.

- fetch_coinbase_ccxt retains native product ID, status and whitelisted mode
  flags in MarketRules.meta. Missing or malformed fields remain unknown, not
  default-false permission. Existing numeric/active parsing is unchanged.
- rules.validate accepts optional order_type. In Coinbase order context it
  validates product identity/schema, blocks offline/disabled/view-only/cancel-only,
  blocks market orders under limit-only and conservatively blocks unsupported
  auction/post-only behavior. Already specified limit orders remain unchanged
  under limit-only. Other venues and quantity-only validation stay unchanged.
- The common place_order fail-closed guard passes its actual order type to
  validation, covering both existing sync/async entries before funding/submit.
  No raw order type, price, quantity, params or strategy rule is rewritten.

A legacy active cache entry lacking the new product snapshot is refreshed once
through the existing public fetch path. Refreshed inactive/unavailable or unknown
mode evidence blocks; old active is not substituted. Malformed populated snapshots
are refused rather than repeatedly refreshed. No new private endpoint or client
constructor is added beyond the existing public market-rules fetcher.

The existing cache TTL is retained, not shortened or certified as suitable for
exits. Order-context TTL must be positive/finite. The source default remains
six hours; effective runtime value and current exchange status are UNVERIFIED.
Flags may change inside that cache window. This repairs mode loss/enforcement,
not receipt-time authentication, per-exit live refresh or full Fix2 readiness.

## Verification

VERIFIED_ENV: isolated venv, fake public provider and patched socket/DNS; real
market modules/cache and disposable SQLite in numeric/cache tests. No actual
execution entry module/SDK client/account requests were run by this selection.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_coinbase_market_mode_gate.py tests/test_coinbase_exit_mode_gap.py tests/test_market_rules_validation.py tests/test_market_rules_decimal_validation.py tests/test_coinbase_paged_preflight_compatibility.py tests/test_proposed_async_balance_preflight.py tests/test_coinbase_account_pages.py

Author126passed3.42s,exit0. Includes34 new actual-validator/public-fetcher/cache
and structural-chokepoint cases,12 existing cache/decimal tests,8 historical gap
controls,28 parser/funding,23 async preflight and21 reader cases. Both order
entries' use of the common guard is source/AST proof, not a full runtime order.
The existing async harness still uses fake risk/argument/submission seams.

Historical gap tests now load archived pre-repair fetcher/validator functions;
they do not assert current mode loss is still present. Updated preflight/source
evolution checks retain the reviewed funding helpers and permit exactly the
new order_type keyword in the common market-validation call. The entire module
AST must otherwise match the accepted pre-change proposal. Original test bytes
are preserved. No assertions were removed merely to obtain a green result.

## Remaining Boundary

Actual order submission, live exchange flags/cache age and alert delivery remain
UNVERIFIED. Durable checkpoint/reconciliation/initialization is not wired; outer
tick retry scheduling is not repaired here. Known restricted orders fail at
validation, but this is not proof of zero repeated client/public refresh calls
or actual partial-fill safety. Existing lifecycle/dedupe authority is unchanged.

No existing database, migration/schema, SDK/dependency, credentials/accounts,
service/restart/deploy, scheduler/pilot, capital/risk setting, trading operation,
commit or push action. This local code changes refusal behavior when modes are
restricted/unknown, not live configuration. Accepted planner/checkpoint/cap
prototypes remain unchanged; original funding-rate Fix3 remains open. Freeze
the exact source/test diff and hashes for one independent GATE review.

## Actual Independent Acceptance

Reviewer01a11481-515d-7473-8ee3-7f6864c6d40b, submission
01a18446-79ba-7100-a541-c249808d23ad, returned ACCEPTED_WITH_RISK for the exact
local mode-gate repair/offline proof. No material blocker or unauthorized test
weakening found. Verified nineteen bindings, three unchanged prototypes and
both diffs; independent bound command126passed3.66s. No edits/private/network/
real-client/operational actions.

Accepted source SHA256:
- fetcher:8fb7b9d0edf6d1c265d671183b51169746ab7ba303c02630b6f9f3b5e844d15f
- validator:250321c190f327750e7170fa7ff2be5126979bf208b6b5ffa1c2a34e77ba4c0f
- order boundary:137a3e7260381eec79982c63a716928446f6acc6909df37db92e91a0ce80664b

No reviewed source/test changed afterward. Original BINDINGS and submitted
checkpoint are preserved; CLOSURE records this subsequent outcome. Reviewer
retains six-hour source-default TTL/freshness, partial-fill, retry, checkpoint
and runtime limitations. Original Fix2 not fully closed; original funding-rate
Fix3 remains open. Acceptance grants no deployment or trading authority.
