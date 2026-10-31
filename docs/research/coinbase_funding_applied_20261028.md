# Coinbase funding-provenance patch applied locally

2026-10-28. ENGINEER stage, HIGH risk financial admission.
Status ACCEPTED_WITH_RISK after separate post-application GATE review for the
exact local change and offline regressions. Deployed proof INCOMPLETE.

## Authorized Change

Operator answered "carry out the next steps" to the explicit request to apply
the reviewed two-helper patch locally and run offline regressions. That request
disclosed newly refused Coinbase orders with unproven funding, including sells,
and excluded account calls, restart, deployment and trading operations.

Verified the accepted proposal's closure, source/test dependencies and unchanged
target before applying exactly proposal.patch with apply_patch. Application
`services/execution/place_order.py` now matches the separately reviewed proposal:
SHA256 `8d04313c13b8e9ab8683a4c77d7dd5c63a49049ff9cbf44e862e5aec4849242a`.
Only _coinbase_spendable_from_info_rows and _extract_spendable_balance change
relative to the pre-application source. Existing async correction is retained.

Coinbase funding now requires explicit matching asset-row portfolio evidence;
unknown provenance cannot fall back to aggregate free or total. Known scoped
funds retain the existing free minimum. Other venues are unchanged. Zero eligible
funding is a refusal value, not proof of zero account holdings. The patch adds
no cap, liquidation, exit strategy, routing, fee or capital-setting change.

## Verification

VERIFIED_ENV, repository venv, invented inputs and selected-source methods only:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_coinbase_paged_preflight_compatibility.py tests/test_proposed_async_balance_preflight.py tests/test_coinbase_account_pages.py
```

Author result:72passed2.69s, exit0 (28 parser/funding,23 async preflight,21 page
reader cases). Updated tests to target the applied source and latest exact
reviewed bytes, preserving prior harnesses in the application artifact folder.
Six paired cases retain archived original acceptance as a negative control and
require actual-source refusal. Four new async-path cases cover missing/wrong
asset portfolio with sync and async fake reads, without reaching submission.
An AST check limits synchronous-definition changes to the two approved helpers.

No full-module, full-suite, live client/account, real fee, deployed or end-to-end
order proof. Reader/prototype source remains unchanged and unwired. Installed
SDK parsing is selected-source with invented currency identity/options; V2
spendability and authenticated account coverage remain UNVERIFIED. V3 still
does not satisfy the legacy portfolio guard. Pagination/cap wiring is INCOMPLETE.

## Evidence And Review

Artifacts: `docs/review_artifacts/coinbase_funding_applied_20261028/` preserves
prior test harnesses, the exact applied patch and new hash bindings. Earlier
proposal/reader bindings remain historical: application/test hash evolution
here is intentional, not a reason to rewrite their accepted records.
Separate GATE reviews the applied bytes, changed harnesses and exact targeted
command. No same-thread high-risk acceptance. No private/account/credential
access, service/scheduler/pilot, deployment, trading operation, package,
migration, commit or push occurred.

## Actual Separate Acceptance

Reviewer 01a11481-515d-7473-8ee3-7f6864c6d40b, request
01a18415-f310-7420-883c-13d2bafa34bf, returned ACCEPTED_WITH_RISK for exact local
application/offline regressions. No material mismatch or unauthorized test
weakening found. All fourteen bindings matched; reviewer also verified unchanged
pager/cap prototype hashes. The documented command ran independently once:
72passed2.50s. No edits or private/network/runtime operations.

Accepted application SHA256 remains
`8d04313c13b8e9ab8683a4c77d7dd5c63a49049ff9cbf44e862e5aec4849242a`.
No code/test changed after review. Original submission checkpoint/BINDINGS are
preserved; CLOSURE.json records the subsequent disposition. Reverse patch check
passed without reverting the application; source AST and scoped whitespace
checks passed. The local defect is closed within this evidence lane, not proof
of real-client, full-module, full-suite or deployed correctness. No deployment
or account-access authority follows from acceptance.
