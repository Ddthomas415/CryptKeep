# Existing async balance preflight: offline integration proposal

2026-10-28. AUDITOR diagnosis, ENGINEER source-copy proposal.
Risk HIGH; proposal separately ACCEPTED_WITH_RISK for offline source-copy scope.
Application unchanged; application authority and post-application proof pending.

## SHOWN Integration Problem

Current place_order_async calls synchronous portfolio and funding validators.
Those read ex.v3PrivateGetBrokerageKeyPermissions/ex.fetch_balance directly and
then use dict methods. Genuine async reads return coroutines, not dicts. The
existing AsyncFundingExchange fixture overrides create_order only and retains
synchronous inherited account reads; it does not exercise this mismatch.

Isolated unchanged-function probe: sync funding control passes; genuine fake
async balance and async portfolio reads each raise AttributeError before the
coroutine is awaited. Fakes are explicitly closed afterward, without emitting
unawaited coroutine warnings. No real client, private request or order used.
This is source/fixture evidence, not proof of current remote trading impact.

Evidence: `../review_artifacts/balance_preflight_integration_20261028/probe.py`
and RESULT.json. Original source hashes and direct unawaited call sites recorded.

## Exact Proposed File Change

The application file is not edited. A copied place_order_proposed.py and exact
proposal.patch live in that artifact folder. Proposed actual target is only
`services/execution/place_order.py`; no new runtime service/router/client/store.

The patch adds inspect and one internal async preflight helper, then awaits it
at the existing asynchronous entry. It reads permissions first for Coinbase,
fails closed if missing/malformed, then awaits or accepts the original client's
balance result. A tiny observation view supplies those same already-read values
to the unchanged existing synchronous validators. It does not create another
authenticated client or permit the view to route orders.

This reduces duplicate private reads to one permission/one balance observation
for the proposed async flow. It does not authenticate a new account boundary or
make account/balance observations atomic. The synchronous entry and all existing
validators are AST-identical. Existing fail-closed risk checks remain before any
account read; existing order submission stays after all preflights and its
existing semaphore. Exceptions/cancellation cannot proceed to submission.

This corrects awaiting semantics only. It deliberately does NOT wire the
synthetic pager/cap into production, manufacture trusted completeness from their
false authority flags, repair one-page SDK behavior, alter fees/limits or claim
fresh complete positions. Those remain separate requirements. No dependency
upgrade or real account activity is needed to review this patch.

## Verification

```sh
./.venv/bin/python -I -S -B docs/review_artifacts/balance_preflight_integration_20261028/probe.py
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_proposed_async_balance_preflight.py
```

Probe exit0: sync control plus two confirmed unsupported async read cases.
Proposal slice14passed0.31s: source-copy actual async entry with selected existing
validators, synchronous-compatible and genuine async reads, missing permission,
failed/malformed/insufficient balance, risk ordering, cancellation, one-read
counts and AST equality of unchanged synchronous validators/entry.

Uses AST-selected source with fake earlier risk/argument seams and fake client.
A sentinel exception at the fake submission boundary prevents the existing
post-submit risk_daily import from executing; no production module is imported.
This is not full-module, all-gates, full-suite or deployed proof. A sync callback
can still block the event loop; no new timeout/transport guarantee is introduced.
No production fix or account source authority follows from the passing slice.

## Application Boundary

Submit the exact hash-bound proposal for separate review, then obtain explicit
authority before changing the application source. Applying a patch is distinct
from deploying/restarting or invoking account/trading paths. Any actual source
application needs source-hash/diff checks and a post-application regression run;
these source-copy results must not be labelled applied/deployed results.
No account/credential, collector/scheduler/server/Docker, risk/capital/strategy,
service, package, trading, commit or push action occurred in this preparation.

## Separate Proposal Review

GATE reviewer01a11481-515d-7473-8ee3-7f6864c6d40b accepted the exact offline
source-copy proposal with risk, no material blocker. It verified all bindings,
reproduced proposal.patch exactly and confirmed the original application hash
unchanged. Its isolated14-case run passed in0.30seconds. No files, private reads,
network or runtime operations changed.

Accepted proposed source:
`a29ba48fb1f45b167c47817d91d25d7be3341ae18fa64999f7892866642072a6`.
Accepted tests:
`358c4bbe7e9a50c3149ba84e15cb2b592cf870c635d1bf36f2cdca1b3926980d`.
Accepted patch:
`9dbc9abfa312a9455441a1aa5edfc4f711325bde3f9566b2439e7d102a0895b5`.
Review request01a182f4-d810-7581-b1de-a496898a6e78.

The reviewer explicitly requires separate source-application approval, hash/diff
checks and post-application regressions. This review accepts no transport
timeout, pagination, cap reservation, actual account completeness, full-module
or deployed behavior. Source-copy results are not applied results.

Proposed next authorized scope: apply only this reviewed patch to the local
place_order.py, preserve the original snapshot and update the isolated harness
to test the actual application file while retaining the original failing-source
control. Run bounded offline regressions, including unchanged reader/pager
compatibility as relevant; no private requests, module-level client construction,
service/restart/deploy, schedule, risk/capital or trading action.

## Subsequent Local Application

The operator subsequently authorized application and offline regressions. Exact
reviewed bytes were applied locally; see `balance_preflight_applied_20261028.md`
for source hashes, preserved originals and actual-source64-case proof. Earlier
"application unchanged" text is the preserved proposal-stage state, not current
source status. No account/runtime/deployment verification is implied.
