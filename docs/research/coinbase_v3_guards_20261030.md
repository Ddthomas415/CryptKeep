# Coinbase native-v3 guard compatibility

2026-10-30. ENGINEER. HIGH risk, financial admission.
State: READY_FOR_INDEPENDENT_REVIEW; not deployment or trading acceptance.

## Outcome and scope

The accepted balance pager preserves native v3 `info.accounts`, while the
quote-account and funding guards previously consumed only v2 `info.data`.
Eligible v3 observations therefore could not pass the common order preflight.
This repair connects that existing path without rewriting v3 rows as v2 rows.
It does not establish all-account exposure, reserve funds, or enable paging.

Production changes are limited to a pure `coinbase_v3_accounts.py` helper and
one explicit branch in each of `_get_portfolio_currencies` and
`_coinbase_spendable_from_info_rows`. The rest of both existing files, including
the v2 bodies, preflight orchestration, fees, market and risk checks, is retained.
Native v3 input that formerly failed can now pass these two checks when the
required evidence is present. That is an intentional admission change, not
merely formatting. No process was reloaded or order submitted to test it.

## Native evidence contract

- Require the row's native `retail_portfolio_id` to match the permission result.
  No inference from aggregate `free`, configuration scope labels, or the one
  portfolio seen in yesterday's authorized check.
- Validate native account identity, currency and both available/hold amounts.
  Deduplicate identical account IDs; reject conflicting rows. Other portfolios'
  funds and held amounts never count as available for this portfolio.
- Count only explicitly active, ready, non-deleted fiat/crypto rows. Missing
  eligibility fields withhold the row, including absent `deleted_at`; a null or
  empty deletion value is required. Staked-name rows are also excluded. These
  are conservative eligibility checks, not independent proof of tradability.
- Reject malformed/mixed schemas, provider errors, missing native ownership,
  currency disagreement, negative or non-finite amounts. Native values are
  limited to string/integer representations of at most 128 characters and an
  absolute Decimal exponent of at most 100 before rational conversion. Extreme
  values are refused, not interpreted as zero.
- Sum native amounts exactly as rationals, then ensure the float's decimal
  representation cannot exceed that evidence. Keep the existing parsed-free
  minimum. No aggregate fallback after a malformed v3 observation.
- Ordinary v2 observations use their unchanged original code. Native-v3 support
  also applies if an existing caller supplies that schema without paging;
  no current client options, API version or paging policy were changed.

Field/schema reference inspected for this implementation:
[Coinbase List Accounts](https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/accounts/list-accounts).
The reference documents the fields and notes that CDP keys use their permissioned
portfolio. It does not establish that a returned available amount will fill an
order or that this particular key sees all user portfolios. Installed-parser
type/amount disagreement still causes the existing pager bridge to refuse.

## Verification

VERIFIED_ENV: repository Python 3.12 venv; invented observations/None-key SDK
clients, request dispatch stubbed before signing, credentials or real HTTP.

New cases against the before source: 19 failed, 11 passed in 2.21s. Five failures
directly demonstrate valid-v3 rejection (both guards and four sync/async
buy/sell cells); other failures cover new typed refusal and amount handling.
The old source already withheld funds on malformed v3 inputs; those failures
are not claims of prior unsafe submission. Initial repaired slice: 30 passed.

Existing eight-file regression run: 209 passed, 2 structural-expectation failures.
Those tests expected the old exact source. Their expected ASTs now include only
the explicit four-line v3 branch; no behavior assertion or full-AST comparison
was removed. Both older harnesses are preserved in the artifact `before/` folder.
New structural checks additionally reproduce the current before source exactly
after removal of only the declared branch in each production function.

Final command, one consolidated guarded run:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B docs/review_artifacts/coinbase_v3_guards_20261030/verify_offline.py
```

Result: **245 passed in 14.30s, exit 0**: prior 211 plus 32 new cases and the
2 existing portfolio-guard cases. Reused the accepted offline runner, adding
these two test files only. Network/process launches are blocked; SQLite is
limited to disposable temporary state. This includes the existing full-module
order unit slice, not the repository's full suite or a live execution test.

## Limits and next boundary

Two assumptions: caller observations originate from the intended client, and
the supplied snapshot is not concurrently mutated during validation. Neither
assumption is independent authentication or atomicity proof.

No private request, credentials, account balance, server, collector, scheduler,
trading setting, capital or live-order operation occurred in this repair.
Yesterday's two-GET authorization remains consumed. Source imports in future
processes can use these local changes; no deployment/reload was performed.

All-account coverage remains UNVERIFIED. The operator's all-holdings-per-asset
cap mandate is unchanged; a dedicated portfolio is not silently substituted
for it. Production transport bounds, concurrent pending orders/reservations,
cap enforcement and live qualification remain INCOMPLETE. No profitability or
trading-readiness claim follows from these tests.

Artifacts: `docs/review_artifacts/coinbase_v3_guards_20261030/` preserves before
sources/harnesses, exact diff, source/dependency hashes and verification results.
Separate GATE review is required; implementing thread does not self-approve.
