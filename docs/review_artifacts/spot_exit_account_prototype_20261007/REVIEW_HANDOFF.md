# Spot-exit account prototype: consolidated handoff

Active role: ENGINEER (packaging only). Objective: preserve the unwired prototype
and distinguish completed local proof from remaining integration requirements.
Risk: HIGH for any future wiring. No further trading logic added in this stage.

## Exact artifact and base

- Base commit: 381bd4776c871af8305fb38ae880a101cb0f8fef (accepted PR606 head).
- Archive: prototype_sources.tar.gz, 13 new source/test files, no live state.
- SHA256: b192c3f6f062311fe24031bf5d30d7843e92953eb1d5cd87875cf2aee51a402f.
- SHA256SUMS records each source/test file. Archive contains no credentials,
  database, config, historical account records or existing runner modifications.
- Package is an overlay for an isolated copy of the base, NOT a deployment
  series. It does not include earlier cooldown patches and does not require
  them for its targeted tests. Do not extract into a dirty production checkout.

## What is implemented

1. Reconciled holdings evidence and transactional conservative exit reservations.
2. Terminal receipts bound to durable intent/order/symbol/venue identity.
3. Settlement requires delivered canonical fill accounting and is replay-safe.
4. Dedicated empty-database binding: venue/environment/account/portfolio.
5. Prototype operation checks binding within write transactions and before fetch.
6. Coinbase portfolio-scope observer and same-session receipt coordinator.

The Coinbase account namespace is `coinbase-portfolio:<UUID>`, a trading scope,
not legal/global user identity. Existing history is never automatically adopted.
No production caller imports these new modules. Legacy writers remain unguarded.

## Reproduction and proof

VERIFIED_ENV: existing Python 3.12 venv, fresh isolated base extraction at
/private/tmp/cryptkeep-prototype-package-check-YPzPxw. All 13 manifest entries
verified OK. Eight-file slice: 81 passed in 2.17s, exit 0:

```sh
/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_coinbase_bound_receipt.py tests/test_coinbase_portfolio_scope.py \
  tests/test_spot_exit_account_enforcement.py tests/test_execution_account_binding.py \
  tests/test_spot_exit_owned_boundary.py tests/test_spot_exit_receipt_probe.py \
  tests/test_spot_exit_real_schema.py tests/test_spot_exit_reservations.py
```

Full suite NOT run for this prototype. Most transport tests use doubles; real
stores are used for accounting/identity tests. Trigger ABORT rollback is not
power-loss proof. One actual laptop Keychain-authenticated permissions observation
succeeded (DEFAULT, view/trade true); it did not verify this coordinator end to
end, bind a database or establish historical ownership. UUID was not retained.

## Review status

Hume independently inspected each bounded stage and its corrections; stages
ended ACCEPTED_WITH_RISK. Reviewer did not independently rerun tests. Findings
fixed included receipt replay after settlement, replacement-insert rebinding,
and cross-venue fetching before refusal. This is not whole-system acceptance.
Consolidated handoff: READY_FOR_INDEPENDENT_REVIEW.

Review outcome: Hume ACCEPTED_WITH_RISK for handoff/package consistency. Reviewer
verified archive hash, exactly13 regular source/test files and all manifest
hashes against extracted package and reviewed candidate. Tests were not rerun.
Acceptance covers preservation/handoff only, never integration or deployment.

## Material work still required before any live integration

- Trusted factory fixes authenticated account/session/endpoint context and
  prevents concurrent credential/config changes; endpoint string checks alone
  do not prove transport authenticity.
- Reconcile remote holdings/open orders before establishing any new database;
  never import historical evidence without account provenance.
- Establish durable position revision and explicit spot-instrument proof.
- Coordinate ALL submission/accounting writers with reservations; prototype
  reservations cannot prevent uncoordinated legacy submissions.
- Integrate receipt/settlement lifecycle and recovery without disabling existing
  protective exits, including unsupported fill-accounting paths.
- Independently verify auth/arming/global halt/reconciliation/order-validity
  remain mandatory; bypass only the previously agreed entry veto/symbol cooldown
  for a verified reducing exit. No bypass exists in this package.
- Run targeted production integration and reviewed failure/restart/concurrency
  proof, then separately decide publication/deployment. No scope expansion into
  strategy alpha or financial performance claims is authorized here.

## Next recommended action

Independent consolidated review, then select ONE integration requirement with
explicit proof. Prefer trusted session/ownership lifecycle before modifying live
gates. Stop adding simulated proof as a substitute for that missing contract.
Nothing merged, published, deployed, armed or started by this packaging stage.
