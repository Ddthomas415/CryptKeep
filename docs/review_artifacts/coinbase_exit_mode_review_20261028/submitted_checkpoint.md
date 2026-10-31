# Coinbase exit-mode gap: bounded source review

2026-10-28. AUDITOR stage. Financial behavior remains HIGH risk; no production
repair or exit-policy change. Evidence READY_FOR_INDEPENDENT_REVIEW;
original handoff Fix2 remains INCOMPLETE.

## Correction To My Recent Task Labels

The original 99-line CODEX_HANDOFF_FIXES.md and 139-line October24 checkpoint
were read in full in this review, including all four addenda. Original Fix3 is
funding-rate intervals, source fields, timestamps, predicted/settled status and
formula version. It is NOT the Coinbase order-funding portfolio repair.

My recent references to that local repair as "fix3" were wrong. Its correct
local identifier is CBA-FUNDING-SCOPE-20261028. The independently accepted patch
and72offline tests remain valid for that disclosed two-helper scope. They do
not complete or verify the original funding-rate item, which remains open.
Historical reviewed artifacts are preserved unchanged; this note and the
current task index correct their task identity, not their source/test results.

## Shown Findings

1. services/markets/fetch_coinbase_ccxt.py retains normalized active, quantity/
   price limits and ccxt_symbol, but discards raw product status and mode flags.
   services/markets/rules.py validates active and numeric limits only. Its
   default cache TTL is6hours; actual runtime TTL and current status UNVERIFIED.
2. Six invented active-market cases (normal control, cancel_only, limit_only,
   post_only, auction_mode, status offline) lose mode information and pass that
   selected validator. An inactive control is refused. This checks the supplied
   normalized-market path, not a live response or complete SDK market parser.
3. services/execution/_executor_submit.py returns a failed submit to pending
   with submit_error. The selected function plus actual _list_intents_any picks
   it again on each of three mocked ticks. No outer retry deadline/backoff is
   consulted in this path. The fake client rejects all three boundary calls.
4. The real ExchangeClient.submit_order has deduplication, blocks submitted/
   unknown resubmits and reconciles ambiguous failures. The three fake boundary
   calls do NOT establish three HTTP requests, duplicate exchange orders/fills,
   or bypass of that inner machinery. No real client was constructed.
5. The old handoff's literal "nothing under services reads flags" is no longer
   current: services/backtest/descriptive_metadata.py retains these flags for
   ED-002 model eligibility. That is research metadata, not execution gating;
   do not wire its one-hour research rule in as a live freshness policy.

Partial fills, cancel/stop recovery, currently held positions and current venue
status remain UNVERIFIED. This review did not exercise those paths, claim that
they are broken, or close the rest of original Fix2.

## Reproduction

VERIFIED_ENV: repository venv, selected source and invented SDK/client/store,
clock, risk/preflight and market-cache seams. No real state database, config
values, credentials, network, SDK client or application-entry module imported.
Pure market models/math helpers are imported. Socket/DNS entry points refuse
access. Passing diagnostics mean the gap was reproduced, not repaired.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_coinbase_exit_mode_gap.py
```

Author final result:8passed0.19s,exit0. Initial7failed/1passed because the AST
harness omitted DEFAULT_TTL_S used in a function default; loaded that unchanged
source assignment and reran. No application fix was made to produce a pass.
Two inspection commands included nonexistent guessed helper paths; exact
existing store/shared/client files were then read. No absent file claimed read.

## Recommended Decision Before Implementation

Preserve the original exit intent/remaining quantity and explicitly defer it
with a reason while the product cannot accept its order type. Do not silently
convert a market exit into a limit order, reprice it, mark it filled, abandon it
or cancel a possibly live order. Record an alert event separately from proof of
external delivery. No new alert channel or scheduler is authorized here.

This is a proposed contract, not adopted policy. A bounded implementation still
needs explicit metadata freshness/recipient and retry ceilings and must preserve
the existing uncertain-submit/deduplication authority. Partial fills require
confirmed remaining quantity before any resubmission. Do not choose numerical
live settings, expiry/liquidation rules or a new retry job from this note.

No account/credential access, public capture, service/scheduler/pilot, trading/
risk/capital setting, source deployment, package, migration, commit or push.
Only diagnostic tests, current task labels and this evidence record changed.
