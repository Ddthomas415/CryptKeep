# Coinbase balance paging: synthetic-only implementation

2026-10-28. Active role ENGINEER. Risk HIGH (financial evidence/cancellation).
Current acceptance ACCEPTED_WITH_RISK after separate GATE review of the exact
synthetic callback-only scope. Production paging/cap integration INCOMPLETE.

Operator continued the stated synthetic-only paging repair after the accepted
cap prototype. No private account request or production wiring authorized.

## Implementation

Added `scripts/research/synthetic_coinbase_balance_paging.py` and
`tests/test_synthetic_coinbase_balance_paging.py`. No existing client/CCXT,
requirements, funding gate, state database or collector source changed.

One shared Pager validates pages for sync/async wrappers. A callback supplies
an invented {scope:[venue,account],body:native_response} envelope. Version,
page size, page/unique-account/retained-JSON budgets, absolute deadline and clock
are explicit caller inputs. The callback receives only limit and the appropriate
cursor parameter, never a server-supplied next_uri as a request destination.

V2 follows pagination.next_starting_after using starting_after; V3 follows
has_next/cursor using cursor. Missing/inconsistent control fields, cursor cycles,
empty nonterminal pages, scope changes, provider errors, conflicting account
identities, malformed amounts/currencies and exhausted budgets withhold the
entire complete view. Identical account rows deduplicate; distinct IDs with the
same currency sum exactly. No partial balance is returned as complete.

All in-budget supplied pages are copied into diagnostic raw_pages. Oversized or
non-JSON-serializable pages are not retained. This budget measures serialized
decoded fixture envelopes, not actual HTTP bytes or a hard peak-memory bound.
Callback data already exists in caller memory; no transport is implemented.

On completion, the research view retains merged rows under native info.data
(V2) or info.accounts (V3), with original pages separately available. Totals are
exact rational pairs. V3 additionally retains available and hold-derived used
amounts. V2 available/used stay null: reported balance.amount is not independently
certified as free/spendable or complete account-wide holdings. Native IDs/currency
tags and the declared page scope are not authenticated by this prototype.

The envelope explicitly says SYNTHETIC_PAGES_NOT_CCXT_BALANCE_OR_ACCOUNT_PROOF,
scope_authenticated=false, spendable_verified=false, execution_authority=false.
It is not a drop-in SDK balance or permission to feed its output to live gates.
V3 rows are not silently rewritten into V2 info.data. No provider rounding,
fees, canonical asset mapping, product eligibility or pending-order truth added.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_synthetic_coinbase_balance_paging.py
```

Final author result45passed0.22s, exit0. Covers both versions and both wrappers
for two-page success/second-page failure; duplicates/conflicts, same-asset
aggregation, scope/schema/currency/amount errors, immediate/long cursor loops,
budgets, regressed/nonfinite/expired clocks, callback overrun and cancellation.
Callback/clock exception details are not copied into reasons, even when a fake
callback raises the library's own Incomplete type.

The page-two V2 ETH row reaches the unchanged selected funding reader and
returns coinbase.info_rows_spendable. Five existing reader helpers execute in an
isolated AST namespace with deferred annotations; no production module/client,
credential loader or order/funding submission gate is imported. This proves row
shape reuse, not actual sell authorization or truthful account availability.

Initial run29passed/2failed: test AST omitted deferred annotations, and a test
passed duplicate version arguments. Corrected test harness only;31then39then42
cases passed as explicit edge coverage was added. Final45includes callback/clock
error sanitation. No existing cap53-test/full-suite/backtest was repeated.

Code/test/source diff and hashes are preserved under
`../review_artifacts/synthetic_coinbase_paging_20261028_01/`.
No unreviewed dependencies or changes to the separately accepted cap prototype.

## Remaining Integration Risk

The supplied clock must represent the intended monotonic clock. Deadlines are
checked before/after callbacks; a blocking sync callback or hung async await is
not forcibly interrupted here. A future authorized transport must enforce its
own per-call/request/total bounds, recipient policy and sanitized persistence.
Async cancellation propagates without retries or a complete result; this pure
helper does not durably journal unfinished observations.

Complete pagination is not authenticated account scope, an atomic balance/order
snapshot, full manual/pending exposure or trusted canonical asset identity.
Empty terminal data only proves the supplied page sequence ended, not that an
actual private account is empty. Real integration must validate native provider
semantics and preserve account/portfolio ownership and all independent gates.
No upgrade, private read, account/credential change, service/schedule, strategy,
cap/capital/risk/trading, migration, deployment, commit or push occurred.

## Actual Separate Review

Reviewer01a11481-515d-7473-8ee3-7f6864c6d40b returned ACCEPTED_WITH_RISK,
no material blocker in the exact synthetic callback-only scope. The documented
isolated command independently passed45cases in0.22s; all submitted bindings
matched. No files, private access, network/runtime operations or extra probes.

Accepted source SHA256:
`6d5bb2cbb7d833cb7188432ebd62859db74371d36cb4b71372a0288383944bed`.
Accepted tests SHA256:
`b9b3d29ba33e24ea612bf4eadf95cbc69e2f0f675cbc7bf64ba387905123dd16`.
Review request01a182e5-2440-7243-adad-fdc83bb36f82.

The reviewer explicitly retained asserted scope, callback-boundary deadlines,
decoded-JSON rather than peak-memory bounds, and no actual account/pending
coherence proof. V2 spendability and V3 legacy compatibility remain unproven.
Completion proves the supplied page sequence ended only. Original submission
bindings are preserved; CLOSURE.json records this subsequent disposition.
This does not accept a future transport, production adapter or live guard change.
