# ED-002: proposed 25-symbol dual-exit comparison

Bot relation: BOT_RULES; runtime configuration not checked. Prepared2026-11-14; role DIRECTOR; risk HIGH.
Status: READY_FOR_INDEPENDENT_REVIEW. **Proposal only: NOT ADOPTED, NOT FROZEN, NOT ACTIVATED.**

## Owner decision and practical purpose

SHOWN: the owner selected "Resume offline design; propose both exit models (Recommended)" after the recorded
October31 pause was identified. This authorizes this proposal and review only. Collection, market evaluation,
deployment and trading stay stopped. R10 stays STOPPED. No dates, new data request, service or schedule is set.

Question: on genuinely future data, what do the three frozen default families and their exact SELL-unblocked
variants earn or lose after stated costs when all25 assets share each alternative's cash, and how does adding
a declared runner-style exit stack change that result? Research intelligence and deterministic execution remain
separate; this is not a replacement product direction or live-trading permission.

The November14 five-coin historical contrast remains negative after costs for all60 unblocked cases. It is
not rerun, reclassified as holdout, or evidence that a larger basket rescues the strategies. The reason to compare
these alternatives is the owner's existing25-symbol mandate, not a newly discovered positive backtest.

## Preserved inputs and proposed arm structure

SHOWN adopted in prior decisions:25-symbol scope, one shared-cash account per alternative, carry cash/positions
forward, fixed1hour execution delay, event-triggered allocation with at most4% signal-close NAV per new entry,
USD1000 initial model capital/no deposits,182days, fees50/90bps and adverse25bps per side,0.01USD per-order cash
rounding, and a separate20USD/month overhead scenario. These are model settings, not actual balances, account
fees, live risk limits or measured fills. Existing contract/review records remain historical and unchanged.

Retain all25 identities: BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK, DOT, LTC, MATIC, UNI, ATOM, FIL, APT,
OP, ARB, INJ, SUI, PEPE, WIF, JTO, BONK, PYTH. Coinbase USD spot identity/status/precision must be established
from dated public evidence before any future freeze. No MATIC-to-POL substitution, ticker-only identification,
survivor deletion, outcome-based exclusions or reallocation of known excluded allocation. Unknown is not excluded.
Public product eligibility is not private account/geographic entitlement. No current eligibility is certified here.

PROPOSED, not yet adopted:

- Six signal configurations: breakout_default, ema_cross_default, mean_reversion_default, and each corresponding
  `*_exit_unblocked` preset. Base parameters come from the unchanged snapshot709149a9...cfc; variants are separate
  sidecar overlays adding only literal Boolean `filters_apply_to_sell=False`. Do not mutate the snapshot or expand
  its accepted three-family identity gate in place. Bind each overlay/config/source hash in a new versioned recipe.
- Each configuration runs under **S** and **R-H1D** below:12 strategy alternatives. Add four common controls:
  cash, BTC buy-and-hold, fixed-unit25%BTC/25%ETH/50%cash, and the unchanged28-day BTC/ETH incumbent.
  Therefore16 accounts per cost case,32 alternative trajectories total—not32funded accounts added together.
- Controls are shared comparisons, not duplicated under S/R. Retain actual first-execution benchmark-entry proof,
  no post-fill NAV rebasing, no benchmark retry and no silently relabeled cash fallback. The mix and status
  conventions remain proposals until the final revised contract is adopted.
- Within each configuration, keep identical entry/sizing rules between S and R-H1D so the contrast isolates the
  added exits rather than simultaneously changing the entry latch. This deliberately differs from the historical
  C_path/R transition-entry experiment. No claim of historical or live runner trade-path parity follows.

## The two proposed exit models

**Common event/entry policy:** reuse `event_targets` semantics: BUY only while flat, SELL only while held,
all-HOLD/no event emits no batch, and new entries share residual budget up to1/25 each. Existing retained
holdings use signal-close weights, so any emitted batch can resize them at execution. Record that incidental
turnover separately. The4% rule is an entry target, not a permanent position cap. Keep sells-before-buys,
fee/precision-aware joint affordability, deterministic ordering, unused allocation as cash and existing dust rules.

**S: signal-only.** A raw filtered/default or unblocked strategy SELL proposes target0. No stop, TP, trailing
or hold limit is added. Failed/expired targets do not become hidden orders; the next hourly decision re-evaluates
the fresh signal with actual model holdings. A stale target is not silently carried until a favorable price.

**R-H1D: hourly-observed runner-style exit stack, delayed execution.** Use the SAME entries/allocation as S.
For held positions evaluate the repository's stop3%, trailing2%, take-profit6%, hold60hours priority stack
at completed, available hourly close T. A triggered stack exit overrides the strategy action to SELL/target0,
including a filtered HOLD, but never overrides actual venue execution permission. Otherwise use S's action.
No intra-hour price path, tick sampling, high/low-trigger fill, extra EMA invalidation or new tuned threshold.

All decisions, including stack exits, use only bars ending by T received by cutoff E=T+1hour, and execute at
the model open E under the same declared costs. No current bar ending E enters that decision. A3% trigger is
**not a3% loss cap**: the price can gap or move during the delay, and the full delayed price governs the fill.
The old historical R/C_path had an assumed intrabar path and transition entries; its numbers cannot be used
to forecast or certify this different, causal hourly comparison. Real runner evaluation remains forming-candle/
loop-driven and has independent risk/order behavior; R-H1D is an exit-policy model, not bot execution proof.

Proposed persistent model state per position, separate from financial cost basis:

- On first actual fill from flat, set age anchor to fill timestamp, gross entry reference to adjusted fill price,
  and trailing peak to that reference. Subsequent eligible completed closes must end strictly AFTER that fill
  before updating the peak. Never borrow a pre-entry bar's high, close or maximum.
- Incidental additional buys change gross entry reference to quantity-weighted adjusted fill price; entry fees
  and cash rounding are not included in that trigger reference. Age/peak do not reset. Partial sells leave the
  remaining reference/age/peak intact; full flat clears them. The financial ledger retains its original exact
  fee-inclusive basis. Entry reference and market peak are explicitly different concepts.
- Here partial sells/additions mean modeled quantity changes from the allocator, not measured exchange partial
  fills or an empirical maker-fill model. No new market-microstructure claim follows from the position state.
- When quantity is reduced to0 by an incidental sell, clear state; do not certify a residual position from dust
  that was not actually sold. Preserve genuinely held dust, its marks and state. Lot refusals do not create fills.
- Triggering a stack exit is re-evaluated each new close from retained state if no fill occurred; this is a fresh
  decision, not a stale-price retry. All source inputs, costs, last clock, pending target and exit state are bound
  across restart/midpoint. Missing/inconsistent state is INCOMPLETE, never a reset or guessed first entry.

These position-state rules are NEW proposals, not statements about the current runner or implemented bridge.
They need explicit adoption and synthetic proof. No risk/live rule is changed by specifying them here.

## Clocks, marks, costs and held-coin events

Retain proposed prospective structure: freeze F only after reviewed source/input readiness and owner adoption;
A is the first Monday00:00UTC at least7days after F, E=A+1hour, B=A+182days. These are formulas, not chosen dates
or authority to activate. Structural readiness precedes A; the final required warmup receipt is checked by E.
Defaults need300 contiguous hours; incumbent needs61 complete preceding UTC days. Unknown/gapped required
history is not a recent listing. No trades in warmup, no backdating, no automatic shifted start.

Use50bps primary/90bps stress fees on adjusted executed notional,25bps adverse adjustment per side and0.01USD
buy-debit-up/sell-credit-down rounding. No extra spread deduction. All alternatives start1000USD flat at A,
first execute E and stop trading before B. Primary endpoint is marked NAV, preserving open holdings/dust;
no invented terminal sale. MidpointA+91days retains cash/units/basis/pending/exit state and cost anchors. No
reset or interim economic selection. Separate20USD/month overhead is20*12*elapsed_days/365, not paid out
of the model wallet and not multiplied across32alternatives as if they were one real deployment.

Proposed public metadata validity remains the existing one-hour receipt-based model, with exact identity,
required raw flags/field presence, source hash and separate T/E checks. No current metadata extended backward
or indefinitely. Missing held valuation or unknown mandatory eligibility makes the affected arm INCOMPLETE;
retain diagnostic wallet/last valid NAV. Future evidence cannot repair the primary historical cutoff.

PROPOSED common venue-event policy, also requiring adoption and a feasible dated input source before freeze:

- An official, asset-identified delisting/market-restriction announcement received by T blocks new entries from T.
  If it announces a future cutoff D, stage a held-position reduction at E only if E<D and market sells remain
  explicitly permitted with a valid execution open and precision. Label it `venue_event_exit`, not a successful
  signal/stack forecast. No use of an announcement that was first received after T.
- Already limit-only, cancel-only, disabled, closed or delisted markets cannot be filled by this market-order
  model. Do not invent a limit fill, stale-price sale or zero recovery. Keep real model holdings/marks as
  diagnostics and mark the affected account INCOMPLETE when the prescribed exit cannot execute; no valid
  final-economic headline can be recovered by silently excluding that arm.
- Event-driven liquidation of a fixed buy-and-hold control invalidates its original benchmark contract. Keep
  diagnostic settlement/valuation, but mark that benchmark comparison INCOMPLETE rather than relabel cash as
  successful hold. Unknown event identity/time/coverage is not an observed absence of announcements.
- Existing candle/products capture supplies price/status evidence, NOT a proved complete announcement archive.
  Exact public event-source coverage/receipts are an unresolved feasibility prerequisite. Reuse the existing
  research/evidence path or a separately authorized bounded official capture; no new collector/job is assumed.

This is not a decision to add a free-form news model. The event schema would contain exact asset/product IDs,
official source/hash, received timestamp, announcement timestamp when given, effective cutoff when given,
and the declared restriction. Unresolvable mandatory inputs prevent freeze rather than trigger more infrastructure.

## Reuse and exact implementation gaps

SHOWN by current code inspection; no tests or market runs were repeated for this proposal:

| Requirement | Existing evidence/capability | Remaining scoped work before use |
|---|---|---|
| Shared cash, carry, fees/rounding/lots | `shared_cash_research.py`; accepted adapter/carry evidence | Reuse unchanged unless a demonstrated interface defect requires a reviewed change |
| Delayed inputs and incumbent | `frozen_signal_bridge.py`, `delayed_signal_bridge.py` | Preserve cutoff/window/default behavior; add versioned overlay/exit-policy adapter rather than mutate old snapshot |
| Arm orchestration | `delayed_research_comparison.py` hardcodes7 arms | Explicit16-arm opt-in recipe and bound resume identities; old7-arm API/result behavior retained |
| Stack decisions and carry | `exit_controls.py` supplies pure priority evaluator | Proposed reference/peak/age and delayed-target adapter; no existing end-to-end R-H1D support claimed |
| Held restrictions/events | Mapper/rules/ledger exclude ineligible market fills | Side-aware policy, event receipts and mandatory benchmark/arm incompleteness; no pretend sell permission |
| Reporting | `descriptive_report.py` checks7arms/14trajectories and exact costs/contributions | Versioned arm/report recipe; new policy/event/state traces and gap-correct attribution |
| Future inputs/operation | Accepted public receipt/candle/metadata/readiness/pilot components | Current25identity/warmup/status/event continuity, chosen-host/cost/monitoring proof remain unverified; no deployment authorized |

Do not claim that the existing code is a turnkey32trajectory experiment, that historical hashes certify today's
environment, or that ledger tests establish execution or profitable signals. Current binding hashes accompany
this proposal; no compatibility issue is repaired merely by documenting it.

## Reporting, hypotheses and proof before implementation acceptance

Report all16 alternatives at both costs, all25 consideration rows per strategy policy, actual exclusions and
unknowns, each account's net/gross same-fill-path arithmetic, fees/adverse adjustment/rounding, overhead,
realized/unrealized contributions, turnover/incidental resizes, closed cycles/open dust, exposure, drawdown,
worst trade/day, venue-event exits and incomplete paths. Per-symbol contributions must sum to their shared
account result; do not sum alternative accounts into invested capital/income. Benchmarks retain actual entry proof.

For in/out-of-market attribution, partition every price interval at the execution open: opening-gap price P&L
uses units held BEFORE the batch; open-to-close price P&L uses units AFTER it. Add exact execution costs to
reconcile account P&L. Never credit an entry's prior opening gap to newly acquired units. Separately partition
per-symbol log price returns into held/flat segments using the matching pre/post-batch state. Flat-segment
positive/negative moves describe rises missed/falls avoided; they are not cash profit or causal trading advantage.
Exit-to-next-entry price gaps use actual model episodes, retain never-reentered episodes as censored, and never
choose a hindsight local minimum. This reporting extension is not already implemented by the existing reporter.

Fixed descriptive questions: within each model, unblocked minus default net result; within each configuration,
R-H1D minus S net result; each alternative minus the same controls. Report every sign and cost case. No economic
winner is selected or promoted from these comparisons. Positive difference is not positive net profit. Primary
reported endpoint and both halves are produced only after B; health checks never tune or rank interim results.

No new inferential pass/fail is invented: SB-1 remains unqualified, original confirmation/POP/DSR requirements
remain intact and no p-value, confidence claim, expected income or edge verdict follows. Count12 strategy
policies,300symbol-policy considerations/600cost views and32alternative trajectories if eventually run. These
are not independent trials, evaluated observations or approved research coverage today. Preserve and eventually
reconcile trial history; no new registry/trial outcome is recorded from design alone.

Smallest proposed next implementation AFTER owner adoption: explicit versioned six-config signal/policy recipe
and shared-state exit adapter with synthetic fixtures, reusing accepted ledger/math; then only demonstrated
orchestration/report gaps. Required failure matrix: old API/default parity; raw SELL-only overlay; one-hour cutoff/
future-bar invariance; simultaneous entries/exits/lot dust; gaps beyond trigger; no pre-entry peak; partial resize/
weighted reference/age/peak; state corruption/restart/midpoint equality; venue-event receipt/effective clocks/
failed exits; failed benchmark; all25rows and per-symbol/account/gap-cost reconciliation; correct16/32 counts.
One independent pre-code plan review and focused source review, not a new backtesting framework or broad test loop.

## Acceptance boundary and open facts

Retain the queue's **server collector** requirement. Reuse the existing documented server only after separately
approved compatibility/provisioning and deployment; do not restart the expired Mac pilot or silently use the Mac
as a substitute. Actual incremental versus allocated monthly cost needs dated billing evidence, not the20USD
overhead scenario. Before collection approval, propose expected slot/output counts and missing-run/freshness
checks using existing monitoring; prove delivered observations rather than job labels, with separately approved
alert destination/delivery. No new monitoring framework, job, power setting or server call is authorized here.

Only this offline proposal was authorized. Its new arm/model/event/report rules must be adopted before code is
changed. Then implementation needs synthetic proof and separate review. Current data/source/host feasibility,
actual provider cost/monitoring, future freeze/dates and a bounded collection/evaluation operation are separate
authorizations. Neither generic continuation nor a design GATE resumes R10 or removes commissioning criteria.
The original experiments, rejected outcomes, defaults, unit profiles and paused collection are preserved.

Two model premises: one Coinbase USD spot venue/no FX, yield or leverage; hypothetical full fills at declared
delayed opens/costs with explicit eligibility. Neither supplies missing data, actual liquidity, account permission
or live stop protection. Open facts: future dated identities/status/events/candles, complete provider/host/cost
coverage, operational continuity and current full-path compatibility. Current profitability remains unproved.

What do I know that could change the owner's decision that I have not yet said? R-H1D is a new, deliberately
hourly-observed/delayed exit-policy comparison, not the earlier intrabar replay or actual runner. It may lose more,
and it requires additional reviewed state/report plumbing before any future data can produce a usable result.
