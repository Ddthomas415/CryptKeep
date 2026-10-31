# Paged balances: parser compatibility and funding-provenance proposal

2026-10-28. ENGINEER stage; HIGH risk financial admission.
Status ACCEPTED_WITH_RISK for the exact offline source-copy proposal after
separate GATE review. Application unchanged; live repair INCOMPLETE.

## Answer

SHOWN in an offline selected-source chain: page-two holdings survive the
installed SDK parser for both V2 and V3. V2 output reaches existing portfolio
and funding checks. V3 output does not: the portfolio check reads info.data,
not native info.accounts. Do not switch the existing caller to V3 silently.

SHOWN in the same invented fixture: the existing Coinbase funding reader can
discard another portfolio's ETH row, then use aggregate free ETH anyway. With
USD in the selected portfolio, the quote-account and sell-funding checks both
pass although the only ETH row belongs to another portfolio. This is a concrete
reproduction of queued fix3 (funding provenance), not proof of an actual order,
current holdings, a private-account incident or an exchange vulnerability.

## Minimal Proposal, Not Applied

Preserved current place_order.py and a source-copy proposal under
`docs/review_artifacts/coinbase_paged_preflight_20261028_01/`.
Only two helper definitions change:

- Require an available portfolio identifier and explicit matching row scope
  for the requested asset. A missing row portfolio makes funding unknown.
- When scoped Coinbase rows cannot establish funds, return zero eligible
  funding instead of trusting aggregate free/total. Existing positive-quantity
  funding checks then refuse the order. This zero is a gate refusal, not a
  factual claim that the account holds zero assets.

Known, scoped, spendable V2 rows retain existing behavior, including the free
minimum. Other venues, routing, kills, async awaiting, pricing, fees and
submission are unchanged. No pager, cap or new policy is wired into execution.
The proposal can newly refuse buys/sells with missing or ambiguous Coinbase
portfolio evidence; operator approval is required before application.
It does not add an over-cap sell prohibition or narrow the adopted account-wide
position-cap boundary. Funding and total exposure are different constraints.

## Verification

VERIFIED_ENV, existing repository venv, no SDK/client construction or network:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_coinbase_paged_preflight_compatibility.py
```

The test AST-loads unchanged installed parse_custom_balance, safe_balance and
required base helpers, plus installed Precise and existing application guards.
It does not import the SDK, application entry module or credentials. A parsing
context supplies invented currency identity and matching fixture account-type
options; number parsing uses float, as configured in this fixture. Funding fee
arithmetic is an explicit test seam, not verification of actual fee settings.
Socket/DNS entry points are patched to refuse access.

Initial compatibility result:17passed1.61s. Final author result:28passed2.18s,
exit0. The expanded run adds six paired
base/proposal refusal cases, four known-funds/non-Coinbase preservation cases,
and AST scope/application-byte checks. The paired cases show current acceptance
and proposed refusal for other/missing row portfolio, unknown permissions,
aggregate-only evidence, missing asset rows and malformed row container.
These are positive regression assertions, not 28 newly repaired behaviors.
No old backtests, full suite, private request, order or service operation run.

## Limits And Next Boundary

Source/fixture compatibility is not actual SDK client lifecycle or a full order
request. Complete pagination is not authenticated account coverage or an atomic
balance/order snapshot. V2 spendability semantics and current private data remain
UNVERIFIED. The proposal does not certify all row schemas, canonical identities,
fees, pending orders or cap reservations. SDK retry/recipient/time bounds remain
separate requirements. The reader's false authority flags remain unchanged.

No material market/account assumption supports a live claim. Two fixture inputs
are explicit: invented USD/ETH identity and installed account-type options.
Application remains byte-identical to the previously accepted local async fix.
No credentials, account call, deployment/service, scheduler/pilot, trading/risk/
capital setting, dependency, commit or push action. Separate GATE review is for
this offline evidence and exact proposal only; it cannot authorize application.

## Actual Separate Review

Reviewer 01a11481-515d-7473-8ee3-7f6864c6d40b, submission
01a1840e-b597-7a80-833b-410e77e22bf1, returned ACCEPTED_WITH_RISK for the exact
offline proposal only. No material blocker found. Verified all eleven input
bindings and reproduced the patch. Independently ran the documented command
once:28passed2.04s. No edits or private/network/runtime operations.

Accepted proposal SHA256:
`8d04313c13b8e9ab8683a4c77d7dd5c63a49049ff9cbf44e862e5aec4849242a`.
Tests SHA256:
`746aed28ab82752718f7de1efae4e7b41e1cd3157de6956f0f122d6ce2212e78`.
Patch SHA256:
`39d7f3e5dcf6dbecc7dae8e670d93206ab624af9a920715ead4f7b986440c5bc`.

No code/test changed after review. The submitted checkpoint and original
BINDINGS remain preserved; CLOSURE.json records this later disposition.
git apply --check passed without application. Explicit operator authorization
is needed to apply the two-helper patch locally and run offline regressions.
That would not authorize account requests, deployment, restart or trading.
