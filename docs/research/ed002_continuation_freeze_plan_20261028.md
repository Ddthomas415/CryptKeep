# ED-002: continuation and prospective freeze

2026-10-28. Active role DIRECTOR. Risk HIGH (financial research timing).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Study/statistics: INCOMPLETE.
Supplement proposed for DESCRIPTIVE-1; not adopted, frozen or activated here.

## Outcome And Evidence

Continue the existing 25-symbol comparison toward a genuine prospective economic
answer, without another simulator or repeated historical strategy runs. Preserve
the original contract, captures, source snapshots and failed statistical evidence.

SHOWN in the two pinned capture namespaces only:
- The warm-up seed has 9,528 rows ending October 28 00:00 UTC. A separate
  capture adds 48 rows covering 06:00-08:00 UTC: 9,576 rows combined.
- Each of the 24 required assets lacks six tail hours, 00:00-06:00 UTC, in these
  two namespaces. This is not an exhaustive search of all repository data.
- MATIC remains the 25th scope row, with dated delisted/disabled evidence;
  it is not replaced by POL or silently removed.
- All 194 hash comparisons in the two verification records match. All 11
  selected source files in the frozen strategy snapshot match their hashes.
- A deterministic panel fixture rejects a last candle received A+5 minutes
  when availability is required by A, but accepts it by E=A+1 hour. It calls
  no strategy or return calculation. See the inventory and source bindings.

UNVERIFIED: future continuity, an appropriate collection host/schedule, current
permissions outside saved receipts, and end-to-end readiness through future A.
No new public request, operation or performance result follows from this plan.

## Proposed Timing Clarification

The original contract requires preflight before A while allowing the candle
closing at A to arrive by E=A+1 hour. A complete final-candle check before its
close cannot be assumed. Preserve the clocks; split readiness explicitly:

1. Before A, freeze the structural contract, exact sources, identity references,
   collection policy and future A/E/B. F is the signed future freeze; A remains
   the first Monday 00:00 UTC at least seven days after F. B=A+182 days.
2. Before A, establish the collection path and warm-up available so far. Record
   which final candle is necessarily still outstanding; do not call it complete.
3. By the fixed E, validate the first signal windows using actual receipts no
   later than E, including the candle closing at A. Metadata permission at A
   must come from a record received by A; metadata at E is checked separately.
4. All arms remain cash-only in [A,E). No entry or rebasing moves to a later
   hour. If the required first-batch input check fails, the planned start is
   INCOMPLETE; retain the record and register new future dates before a new start.
5. Execution-open and later outcome checks remain ex-post model-input checks,
   not evidence that future prices were known at E. Missing opens follow the
   existing expiry/benchmark-failure rules, not a repaired or retried entry.

This is a proposed clarification, not a claim that the current contract already
contains it. Keeping literal all-data preflight before A is the alternative;
it cannot be satisfied by inventing an early receipt or using an unfinished bar.
No dates are selected in this document.

## Proposed Continuation And Collection

Reuse the existing public capture CLI, pure adapters and accepted ledger. Do
not introduce a service, database or live strategy executor.

- Before freeze, add one explicit continuation profile for a pinned interval of
  at most 24 completed hours per product, at most 27 public GETs. This is a
  proposed profile, not currently implemented. Refresh metadata, retain all 25
  rows, and request candles only for required products under that observation.
- Fill the six known warm-up hours only in a separately authorized append-only
  capture. New receipts remain new knowledge; they cannot repair old signal-time
  availability or historical venue permission. Reassess any later tail separately.
- For forward observation, propose fixed slots at :05 and :35 each UTC hour,
  each requesting the last two completed hours. These are planned observations,
  not automatic retries after failures. Use distinct output namespaces; never
  reset an attempt, overwrite evidence or catch up a missed receipt retroactively.
- Retain the existing per-run caps: 120-second supervised worker wait, five-second
  owned cleanup, 110-second cooperative budget, five-second socket timeout,
  2 MiB per body and 16 MiB stored payload plus overflow detection. These are not
  a hard 125-second bound on every filesystem/startup/finalization operation.
  Preserve verified TLS and no auth, proxies, redirects or automatic retries.
- Fixed slots offer two chances for a recently closed candle before E. Neither
  success nor continuous host uptime is guaranteed. A failed call does not
  erase a valid earlier candle; a later unknown metadata observation does shadow
  older permission under the existing mapper.
- Preserve partial/error records. Only individually valid hash-bound receipts
  may feed inputs; orphan payloads or a COMPLETE invocation label are not enough.
  Retain conflicting completed values and withhold affected readiness rather
  than choosing a convenient price. No interpolation, stale marks or substitute
  source. A later conflict must not rewrite prior decisions as if known earlier.

Capacity scenario, not a quota or operating commitment: 48 slots/day gives
8,736 slots and at most 235,872 GETs over 182 days. Extrapolating just the one
923,231-byte feasibility payload gives about 8.07 GB of raw bodies, excluding
manifests, normalization, warm-up and changes in response size. No paid data,
new infrastructure bill or return projection is assumed. Host availability,
rate-limit behavior and actual storage must be checked before operations.

## Freeze Record And Remaining Implementation

Add only a receipt-aware merger/readiness path and the bounded continuation
profile; do not alter frozen signal rules or financial libraries. Synthetic
proof should cover interval limits, overlap equivalence/conflict, receipt
deadlines, all-25 consideration, metadata expiry/unknown/exclusion, first-batch
failure and immutable attempt outputs. A readiness report must not call signals,
score returns, generate random trials, or certify statistical qualification.

The future freeze record must bind the adopted contract plus this supplement,
all strategy/ledger/adapter/report/capture source hashes, all 25 identities,
model settings, source/receipt-selection policy, signed F and reserved A/E/B.
Append the final first-batch check without changing the prior registration.
Warm-up prefixes may be frozen then; future evidence is appended with actual
receipt times, not predeclared or backdated. No primary economic ranking until B.

The intended operating host and schedule remain undecided, not assumed absent.
Inventory existing scheduling before proposing any operational change; do not
duplicate a collector. Schedule/host changes, public acquisition and a market
evaluation each retain their separate authorization boundary. This plan does
not pause other accepted research or abandon unresolved inference work.

Unchanged: 25-symbol scope, three frozen families, seven alternative accounts,
carry-forward, one-hour delay, adopted sizing/costs, 182 days, marked final NAV,
missing-data/benchmark rules, and no profitability or trading-readiness claim.
SB-1 remains unqualified. No full-suite or historical backtest rerun is needed
for this design-only supplement.

## Decision And Handoff

Recommended next decision: adopt the two-stage preflight and fixed-slot proposal
for offline continuation/readiness implementation, or retain the current timing
wording pending independent review. Adoption of the design is not approval to
fetch data, create a job, activate dates, evaluate market returns or trade.

Two modelling premises remain: Coinbase USD spot only; hypothetical full fills
under adopted costs/status validity. Neither supplies missing evidence.
Plan READY_FOR_INDEPENDENT_REVIEW; current study/statistics INCOMPLETE.
