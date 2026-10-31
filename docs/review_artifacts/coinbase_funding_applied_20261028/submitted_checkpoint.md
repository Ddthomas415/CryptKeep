# Coinbase funding-provenance patch applied locally

2026-10-28. ENGINEER stage, HIGH risk financial admission.
Status READY_FOR_INDEPENDENT_REVIEW for post-application proof.

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
