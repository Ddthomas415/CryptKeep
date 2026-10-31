# CryptKeep research brief: read before any strategy or edge work

Last updated 2026-10-28: recorded descriptive reporting and receipt-aware input preparation alongside adopted ED-002 settings, unresolved statistical qualification and bounded restoration results. The October16 research corrections remain preserved. This brief is a map. The linked files are the evidence, and they win if the two disagree. Original experiments and registered verdicts are unchanged.

**Correction 2026-10-30 (Claude Cowork, operator-approved; Codex to verify):** section 4 gains rows for VOLFC-1, ATTN-1 and ENTR-CB-1, and the tracker v2 row gains a dated status update. No existing text was removed or reworded.

### Latest Model Decision And Statistical Warning

Live-cap contract disposition: the separate GATE accepted the exact reviewed
contract with risk for synthetic implementation only, no material design blocker.
See `live_position_cap_contract_review_20261028.md`. Required next proof covers
real temporary transaction races, cross-pair reservations, partial fills, restart
and reducing sells. No production repair, account completeness, cap change or
trading acceptance follows from this separate design review.

The subsequent synthetic implementation was separately REJECTED for lost
known-fill coverage on disappearing orders, then corrected in two source lines.
Four pre-fix regressions failed as expected; the corrected53-case file passed
independently in0.62s. Separate GATE ACCEPTED_WITH_RISK the exact corrected
synthetic code and closed SYNTHETIC-CAP-01. See
`synthetic_live_cap_review_20261028.md`. Original rejected sources/results are
archived, not hidden. This establishes synthetic transaction proof only: the
production cap, trusted account evidence and live lifecycle integration remain
INCOMPLETE. No trading or operational readiness follows from this acceptance.

The separately scoped Coinbase paging prototype also received independent
ACCEPTED_WITH_RISK:45tests passed0.22s for synthetic V2/V3 sync/async pages,
cursor/failure/budget handling, raw/aggregate consistency and selected V2 reader
shape reuse. See `synthetic_coinbase_paging_20261028.md`. It supplies no actual
private data, authenticated account completeness, V2 spendability or live wiring.
Production balance/cap integration remains INCOMPLETE; no trading readiness.

Offline existing-boundary inspection also reproduced unawaited genuine async
account reads in the order preflights. A source-copy-only correction has separate
ACCEPTED_WITH_RISK and14independent tests passed0.30s; see
`balance_preflight_integration_20261028.md`. Application remains unchanged pending
explicit source-application scope. Await correctness is not a paging/cap repair,
account-proof gate, runtime validation or authority to deploy or trade.

Operator subsequently authorized exact local application/offline regressions.
The actual file now matches the reviewed patch; separate GATE ACCEPTED_WITH_RISK
the application and64independent tests passed0.48s. See
`balance_preflight_applied_20261028.md`. This supersedes the earlier unchanged/
pending-source status. Original control sources are preserved. No account call,
service restart/deploy or trading occurred; complete pagination/cap and actual
client/operational proof remain INCOMPLETE.

October28 native collection result: the09:05NewYork run completed without a
forced invocation,26publicGETs/48completed required rows. All26raw/receipt/intent
triplets and all25symbol rows verified; MATIC remains explicitly excluded.
See `ed002_first_unattended_capture_20261028.md` and87artifactbindings. One run
does not establish sustained cadence. The named saved inputs still miss three
hours08:00-11:00UTC; a separately bounded history-capture plan is prepared only,
not acquired, backdated, fresh holdout or study activation. No returns calculated.

The operator subsequently approved that separate one-shot history capture. It
completed with26publicGETs/72newrequired rows at09:12NewYork, no retry. Existing
raw-receipt merger now verifies9840required rows with complete300/1464hour
required tails. A cutoff before the new receipts still shows the original gap:
no historical availability was repaired. See `ed002_startup_gap_capture_20261028.md`
and444artifactbindings. This closes history-content feasibility, not sustained
pilot cadence, freeze, prospective dates, inference, trading or profitability.

Current E1 reconciliation: `e1_readiness_reconciliation_20261028.md` supersedes
the older budget's "v2/waiting on fees" short status. The288-line v3 draft and
109-line budget were read in full: fees, arrival alignment, source coverage and
inference gates remain before freeze. Existing two-book/shadow/market-context
tools supply parts, not a complete E1 collector or realized execution proof.
Nov3/Nov7 are reporting-window targets, not permission to backdate or shorten
the sample. No experiment, new data, account lookup or schedule was started.

ED002-MODEL-SETTINGS-20261027: operator chose "Adopt draft settings; prepare
synthetic statistical validation (Recommended)". Adopted modelling inputs are
1000USD per alternative/no deposits/182days, fee50bps primary90bps stress and
adverse25bps each side,0.01USD per-order cash rounding, separate20USD/month
overhead. Earlier proposal-state notes below remain historical for these named
inputs, not reasons to request their adoption again. They are not actual account
balances, certified venue costs, live limits or a market-run authorization.

`ed002_stat_validation_20261027/README.md` separates implementation from inference:
213focused tests passed (28new+185existing); the fixed67-call synthetic pilot
completed in5.894880s. Under the original7-day/20000-resample screen, iid null
positives1/32, persistent AR1(0.8) null positives8/32. The latter is25% with
synthetic-trial Wilson range13.25%-42.11%, not a market false-positive estimate.
This is evidence against treating the proposed bounds as nominal5% familywise
confidence control under that persistent null. No settings, seeds, blocks or
market outcomes were tuned to improve it. Statistical validation INCOMPLETE;
code/pilot READY_FOR_INDEPENDENT_REVIEW pending separate disposition. A positive
computed bound is not a profitability PASS. Source/attempt/results preserved.
The existing reviewer subsequently returned a usage-limit error, with no saved
review artifact. No independent acceptance, retry, replacement reviewer or
additional calibration is claimed; implementation remains awaiting review.

Status/effective-interval model, exact market-rule mapping, control mix, validated
inference and actual activation dates remain outside the settings adoption.
No new market dataset, backtest, collector, operations or trading action. Next is
method review and prospectively fixed further validation, not another simulator.

Subsequent continuation prepared `ed002_stat_revision_plan_20261027.md`: one
stationary-bootstrap/automatic-length candidate, not silent selection of14or28.
References opened include official arch documentation and the2004paper/2009
correction; they do not certify our wealth bounds. Six fixed nulls, fresh audit,
exact-binomial qualification, abstention reporting and power diagnostics have
proposed budgets90sdevelopment/600saudit and no post-result rescue. All choices
remain a HIGH-risk design READY_FOR_INDEPENDENT_REVIEW; no new method, package,
random path, market study or review acceptance was created. Existing failed
pilot and adopted economic settings remain intact. Next review may be human or
independent; the prior reviewer usage-limit error is not represented as approval.

Operator subsequently selected "Adopt plan; build NumPy-only prototype
(Recommended)" (ED002-SB1-PROTOTYPE-20261027). Implemented
`ed002_sb1_prototype_20261027.md`: isolated NumPy selector/supplied-draw sampler
and wealth prototype,32deterministic/reference tests passed1.23s. Tagged
arch7.2source/license bytes captured and bound; only two reviewed mathematical
functions execute in AST test namespaces, not package imports. No installation,
RNG paths, development/audit, old213test rerun or market study. Code
READY_FOR_INDEPENDENT_REVIEW; statistical validation INCOMPLETE. The original
8/32pilot failure remains unchanged, not solved by reference parity. Proposed
randomized budgets need later authorization after separate code review.

Subsequent operator choice "Accept prototype; run development only (Recommended)"
provided the human acceptance/one-run route (ED002-SB1-DEVELOPMENT-20261027).
`ed002_sb1_development_20261027/README.md`: actual96trials completed16.908430s
within90scompute,71computed/25abstained. Per-case computed/positive: iid16/0,
AR0.5 16/1, AR0.8 12/2, AR0.95 0/0, AR-0.5 13/0, volatility14/2. The strongly
persistent case never computed a bound; zero positives is not error control.
Development cannot certify coverage, power or improvement over different old
pilot paths. No parameter/seed/guard change or larger audit. Source/attempt/raw
synthetic returns/draw hashes/results preserved;8runner-helper tests passed.
Authorized development objective complete; statistical validation INCOMPLETE.
Method/availability review is recommended before any further run, not automatic
execution of the proposed audit. No market data or trading activity occurred.

Saved-output review: `ed002_sb1_development_20261027/METHOD_REVIEW.md` and its
hash-bound JSON reconcile all 96 selector/guard decisions. AR 0.95 selected
19-21-day lengths, correctly abstaining under the frozen ten-effective-block
guard. No defect in that boundary is demonstrated; this is the implementing
thread's factual review, not independent numerical certification. Statistical
validation remains INCOMPLETE. No method rerun, tests or market requests occurred.
Do not automatically enlarge the audit or lower the guard. The operator then
selected "Prepare descriptive comparison contract (Recommended)": preparation
can proceed alongside unresolved inference. This does not adopt detailed new
rules or authorize market evaluation. See
`ed002_defaults25_descriptive_contract_20261027.md` and its hash bindings.
The new contract preserves all 25 assets, frozen families, adopted settings and
carry/delay; it proposes explicit remaining mix/metadata/mapping rules and reports
modelled economics without confidence or promotion claims. Contract
READY_FOR_INDEPENDENT_REVIEW; experiment readiness INCOMPLETE. The original
confirmatory design and statistical work remain intact. No study was run.

The operator subsequently replied "approve. carry out the next steps" to the
submitted descriptive contract: human acceptance for the design and synthetic
implementation, not independent certification or a market run. Added the pure
public-product converter documented in `ed002_descriptive_metadata_20261027.md`.
Its receipt/expiry, typed flags, exact mapping and unknown-shadow rules feed the
unchanged ledger; 76 targeted tests passed in 4.98s, including synthetic 25-label
seven-arm carry. The operator then human-approved this exact synthetic converter;
actual mapping and collection remain unverified. No account facts, statistical
qualification or trading permission follows.

Implemented pure reporting, completed October 28:
`ed002_descriptive_report_20261028.md`. Existing journals reconcile hourly wallets,
per-symbol contributions, costs, separate overhead, carried halves and all-control
differences. It retains losses/open risk and withholds the headline on incomplete
or inconsistent inputs. 101 targeted tests passed in 22.24s with invented 25-label
data and scripted signals, not actual strategy performance or a 182-day study.
The operator then human-approved this reporter's exact synthetic scope. Future
source/receipt feasibility and freeze/activation remain INCOMPLETE; statistical
qualification is unchanged.

`ed002_input_feasibility_20261028.md` checks existing collection fit: the prior
runner is five-market-bound, and its mutable OHLCV store has no first receipts.
Preserve those sources/studies; reuse raw-response capture patterns rather than
silently widening their registration or replacing history. Added a pure candle
receipt/column adapter with 82 targeted tests passed in 2.54s, using invented
bytes only. The operator then human-approved the adapter's exact synthetic scope.
Current warm-up/continuity remains UNVERIFIED, not inferred from old archives or
current collector PIDs. No acquisition or study dates have been authorized.

`ed002_capture_transport_20261028.md` records the completed one-shot transport
preparation: up to 27 public calls, raw receipts, explicit payload limits and
owned-worker supervision; default CLI is offline. 116 targeted fake tests passed
in 2.93s. A candidate plan covers all 25 dated vendor IDs; its actual read-only
preview passed with no worker or request. The operator then approved this exact
transport and instructed its described single next public feasibility capture.

SHOWN October28 at04:16NewYork: the reviewed command ran once and returned
COMPLETE, 26 public calls / 923231 bytes, no retry or cleanup failure reported.
24 metadata-model-eligible products supplied both requested 06:00-08:00UTC bars;
MATIC was delisted/disabled and retained as a known exclusion in the 25-row scope.
Latest bar receipts were within the one-hour allowance; this is observation age,
not publisher latency or execution proof. All-25 raw physical coverage remains
INCOMPLETE because MATIC has no requested candles. See
`ed002_capture_attempt_20261028.md` and its 85-artifact verification record.
All 26 payloads/receipts and 15 submitted source bindings verified unchanged.
No strategy/return/scoring, warm-up proof, collector/scheduler or study activation.
Next is separately bounded warm-up preparation; the one-shot authority is consumed.

Warm-up preparation is now implemented in the same capture path, with a distinct
validated profile: 300 hourly bars for eligible defaults, 1464 for BTC/ETH,
at most 35 public calls. Legacy two-hour mode remains capped at 27; prior source
was preserved byte-exact before extension. See `ed002_warmup_preparation_20261028.md`.
129 targeted fake tests passed in 3.64s; actual read-only plan preview passed.
The operator then instructed the stated next warm-up capture under the submitted
scope; recorded as operator acceptance, not independent review. The existing
review agent still returned a usage-limit error; no acceptance or reset is
invented from that limitation.

SHOWN October28 at04:41NewYork: one warm-up execution exited0, COMPLETE,
34publiccalls/1446556bytes/no retry or reported cleanup failure. Required9528
normalized rows cover1464hours eachBTC/ETH and300each other22 eligible products,
ending W=October28 00:00UTC. MATIC stays excluded/visible in the25-row scope.
All34payload/receipt and14submitted source bindings verified; the actual panel
loaded all required windows and rejected a historical cutoff with late receipts.
No signals, returns or study scoring. See `ed002_warmup_attempt_20261028.md`
and its109-artifact verification record. W is not activation A/E/B; no dates set.
Next is continuation/freeze and collection specification, not another simulator
or implicit scheduler. Up-to-A and ongoing coverage remain UNVERIFIED;
study/statistical readiness INCOMPLETE. The one capture instruction is consumed.

`ed002_continuation_freeze_plan_20261028.md` now proposes receipt-aware
continuation and a two-stage preflight: structural registration before A,
first-candle validation by E=A+1 hour. This corrects a timing ambiguity without
backdating or moving the adopted execution clock; the supplement is NOT adopted.
Fixed :05/:35 hourly collection slots are also proposals, not a running job.
Inventory of the two captures shows 9,576 rows and six missing tail hours per
required asset in those captures only; 194 evidence bindings and all 11 frozen
selected-source hashes match. No market request or strategy run was repeated.
Next is the design disposition before offline continuation/readiness work;
plan READY_FOR_INDEPENDENT_REVIEW, study/statistics INCOMPLETE.

Subsequently the operator explicitly selected "Adopt proposed design
(Recommended)". `ed002_continuation_implementation_20261028.md` records the
offline implementation: pinned 1-24-hour continuation profile and pure raw-
receipt merger/first-batch check. 164 synthetic targeted tests passed in5.35s;
the six-hour candidate plan passed the default offline CLI preview, without
worker or requests. Original capture source/tests archived before extension;
original plan/receipts/frozen strategies preserved. Design adoption does not
approve new acquisition, a schedule or study dates. Implementation
READY_FOR_INDEPENDENT_REVIEW; no independent code review claimed, and
study/statistical readiness INCOMPLETE. Earlier proposal labels are historical.

Operator then approved the submitted implementation (human ACCEPTED_WITH_RISK,
not independent review). One separately command-approved six-hour continuation
ran at05:22NewYork: COMPLETE,26GETs,927159bytes,144new required rows. Combined
saved input now has9720contiguous required rows through October28 08:00UTC,
exclusive, with no required conflict; all25scope rows retained. All22submission
hashes unchanged. A historical09:00availability cutoff rejects the gap received
at09:22, as required. No signal/return or statistical run. See
`ed002_continuation_attempt_20261028.md` and299-artifact verification.
No further capture, running collector, schedule or study dates. Next is approved
collection-host/schedule feasibility and a bounded operating plan; collection
continuity and study/statistical readiness remain INCOMPLETE.

`ed002_collection_operating_plan_20261028.md` now recommends this Mac for a
direct native-CLI pilot, not an AI collection task or new server. Scoped local
read-only checks: no user crontab, no matchingED-002/CryptKeep label among557
loaded user jobs, AC idle sleep0 and substantial free disk. No claim about
uninspected system/remote/Claude schedules, Downloads background permissions or
future uptime. Initial denied reads were resolved through bounded read-only
command approval, not mistaken for missing jobs. No schedule or power change.
The adopted twice-hourly cadence remains design only; proposed24-hour/48-slot
pilot and120-second lateness cap await design disposition. Next is offline
wrapper/job-artifact proof, not installation or another market run. Plan
READY_FOR_INDEPENDENT_REVIEW; collection/study/statistics INCOMPLETE.

Operator explicitly adopted the localMac pilot design (24hours/48slots/120s
dispatch-lateness) for offline preparation. `ed002_local_pilot_wrapper_20261028.md`
records the standalone pinned wrapper and disabled, undated policy/uninstalled
job template. 200 targeted synthetic tests passed in6.45s; isolated CLI preview
and plist lint passed without collection or pilot directory. Pending/uncertain
prior runs hold later slots; no automatic retry/reset. Capture/financial sources
unchanged. The existing reviewer still returned a usage-limit error; no independent
acceptance inferred. Implementation READY_FOR_INDEPENDENT_REVIEW; dated pilot,
installation, actual cadence proof and study/statistical readiness INCOMPLETE.

Operator then approved the submitted wrapper package; recorded human
ACCEPTED_WITH_RISK, not independent review. All17bindings match. Prepared
`ed002_pilot_installation_scope_20261028.md` for one24-hour/48-slot/1296GET
maximum native pilot. The first-slot rule (at least15minutes after installation
preflight) and installation/collection scope still need explicit authority.
No fixed pilot or study dates, new data, job installation or test repetition.
Claude's full direction/handoff/addenda were read and their four reported safety
fixes/research deadlines queued as pending reviews, not silently implemented or
allowed to override adopted Mac design/frozen criteria. Study/statistics INCOMPLETE.

Operator then instructed the explicitly requested bounded installation. One
command-approved native operation exited0 and registered the exact owned job;
source/policy/file identity and0600mode verified,10policy pins and17submitted
bindings unchanged. No immediate data request or kickstart. Fixed collection
pilot: October28 06:35NewYork to October29 06:35NewYork, max48slots/1296publicGETs.
See `ed002_pilot_runtime_20261028.md`. At postflight0slots had started; actual
unattended permission/cadence/receipt proof remains UNVERIFIED. Next is read-only
slot verification after first opportunity, not another forced capture. Wrapper
refuses acquisition at expiry; the native job may remain loaded with refusal
logs until separately removed. No study A/E/B, return calculation, strategy or
trading change; study/statistics INCOMPLETE.

October28 06:14NewYork check: first native pilot slot at06:35 is not yet due;
no slot directory, scheduler logs empty, no capture forced. In the interval,
the already-queued live cap fix4 received read-only current-source review:
`live_position_cap_review_20261028.md`. The selected gate omission is SHOWN with
invented limits/positions; no live/account/fill consequence is established.
Production repair remains INCOMPLETE and requires an authoritative position/
reservation contract. All10pilot source pins unchanged; no strategy or runtime
change. Next pilot proof remains actual receipts after the scheduled opportunity.

`live_position_cap_treatment_scope_20261028.md` traces the preferred adapter to
common place_order/async authority; the legacy check_live method alone is not
enough. Daily atomic counters, free balance and filled-local cache are different
from a fresh per-asset exposure reservation. Existing October9 halt/adjudicate
decision is preserved, not reopened as absent. One operator cap-scope decision
remains (all account holdings/manual/pending versus bot-owned only). No live
repair, account/DB/client use or scheduled reconciliation was performed. Source/
AST checks passed,15bindings saved,10pilot pins unchanged; no strategy results.

### October27 restoration result and next decision

October28 update: the operator directly adopted all account holdings per asset
for the live position-cap repair, including manual holdings and pending buys
across quote pairs. `live_position_cap_contract_20261028.md` records the HIGH-risk
design, READY_FOR_INDEPENDENT_REVIEW; production repair remains INCOMPLETE. No
account, cap value, arming or trading change; a dedicated portfolio is a separate
proposal, not an adopted operational action. Earlier undecided text is historical.

The 08:40NewYork pilot check contradicts any inference of unattended success:
five launch attempts, exit78/EX_CONFIG, spawn failed, no slot receipts or log
output. A targeted debug entry identifies denied access to the stdout file
inside Downloads before collector startup. `ed002_pilot_failure_check_20261028.md`
records the diagnosis and offline log-path-only proposal. Subsequent repo and
interpreter access remain UNVERIFIED. No installed repair, forced capture,
missed-slot repair, new job or pilot extension. Installation proof stands;
collection readiness INCOMPLETE.

Operator then explicitly approved the submitted log-path repair and one reload.
At08:50NewYork the exact existing job was reloaded successfully, with only the
two log destinations moved to a pilot-specific Library/Logs/CryptKeep directory.
All10pins,48-slot/1296GET ceilings and original October29 06:35expiry remain.
See `ed002_pilot_log_repair_actual_20261028.md`. No kickstart/catch-up/extension.
Registration with runs0 is not unattended collection proof; the next calendar
opportunity is09:05NewYork. Subsequent interpreter/repo/network access remains
UNVERIFIED until actual receipts. No strategy, cap, account or trading change.

### October27 Restoration Evidence (Preserved)

October28 queued balance dependency check: installed CCXT4.5.48 sync/async
fetch_balance stops after one balance response; six isolated selected-method
fake-transport cases confirm this for default-v2, explicit-v3 and paginate=True
on the default path. See `coinbase_balance_paging_review_20261028.md`. Not a
private-account or server audit, dependency upgrade or implemented repair.
Complete account evidence remains required before the cap can trust missing
holdings. At08:53 the native pilot had not reached its09:05 opportunity; no
forced capture or new failure was inferred. No strategy results produced.

### Preserved October27 Runtime Result

SHOWN: the single separately authorized V6i update and archival cited-query
attempt succeeded, and its saved committed result was independently
ACCEPTED_WITH_RISK. Four reviewed replacements were left running; companion
HTTP200, five citations, execution disabled, nine compatibility checks and five
evidence checks passed. See
`../checkpoints/companion_runtime_attempt_v6i_20261027.md` and its linked receipt.
This is a deterministic retrieved-evidence companion result under the frozen
archival probe, not an external-model or browser/UI test. Live market data was
excluded intentionally. Broader UI/live-market/model readiness and sustained
health remain unverified. Earlier dated restoration failures below are historical,
not a reason to rerun the consumed successful attempt. No further operational
authorization follows from this result.

The portfolio reuse assessment is already complete:
`portfolio_reuse_assessment_20261018.md`. Do not repeat it. The independently
reviewed recommendations in `ed002_portfolio_contract_candidate_20261018.md`
were subsequently adopted by the operator on October27 for synthetic-only
implementation. The shared-account adapter and 93 focused synthetic/compatibility
tests are documented in `ed002_shared_cash_adapter_20261027.md`, currently
independently ACCEPTED_WITH_RISK after two reproduced defects were corrected.
The synthetic implementation scope is complete. Existing APIs, carry-forward and frozen artifacts
are preserved. No new market-data run, strategy tuning, live sizing or capital/risk
change is authorized; this is accounting evidence, not an approved experiment.

Subsequent operator choice: prepare the existing frozen defaults across the
declared25, design only, rather than widen the first comparison to CTREND.
See `ed002_defaults25_comparison_design_20261027.md` and its source bindings.
The proposed shared sizing, cost scenarios, prospective dates and inferential
screen remain unadopted. Separate saved GATE review
`ed002_defaults25_design_review_20261027.json` is ACCEPTED_WITH_RISK for design
coherence, not statistical certification, implementation or a freeze. All19
review bindings matched at closeout. No parameter or economic result is frozen
by this design choice. No market data has been evaluated for that proposal.

Later October27 decision adopted the allocation rule and synthetic-only bridge,
not the cost/horizon/inference/activation proposals. See
`ed002_signal_bridge_20261027.md`: independent review rejected an incumbent
frame-validation bypass; its narrow correction has129targeted passes and was
independently ACCEPTED_WITH_RISK with that finding closed. Frozen signal sources and accepted ledger remain
unchanged; there is no new economic or operational result.

Saved-input inventory now separates availability from readiness:
`ed002_defaults25_saved_input_inventory_20261027.md`. The October19 snapshot
has25same-base USD candidates (24online/MATICdelisted);24names appear in each
old hourly archive index. No raw candle completeness/current status is claimed.
Official docs distinguish removed quantity-minimum fields, price ticks and
currency precision; no metadata-to-ledger mapping was silently adopted.
Inventory does not authorize a refresh, simulation or protocol activation.

The operator separately approved one public metadata refresh, now complete:
`ed002_defaults25_metadata_refresh_20261027.md`. Two GETs succeeded; the
October27 17:17:32NewYork snapshot again shows24online/MATICdelisted among25
same-base USD candidates. Compared fields are unchanged from October19.
This consumed metadata-only authorization; no candles, economic results,
model-rule mapping, account permission or activation follow from it.

Subsequent saved-file audit (not a strategy run):
`ed002_defaults25_archive_audit_20261027/README.md`. SHOWN:2compressed archives
and48selected members match existing hashes; zero schema-shape/timestamp defects
other than missing hours. Recent60-day window has21/24complete panels and
24/24complete final300hours (OP/PYTH/WIF lack4/1/18earlier hours). Older window
has0/24complete panels and22/24complete final300hours, including two shared
five-hour gaps already recorded in prior research. MATIC has no indexed hourly
file and remains in scope. No values/returns analyzed or repaired. Local audit
ACCEPTED; experiment readiness INCOMPLETE. Previously used history ending
October9 is not a fresh holdout or current warm-up; no per-candle availability
timestamps or historical eligibility are established by this audit.

Proposed input-contract supplement:
`ed002_defaults25_input_contract_20261027.md`. Source-only synthetic check shows
the current bridge accepts boundary-known bars but rejects the final bar known
1ms after that boundary. This is correct guard behavior, not measured feed
latency or a reopened implementation defect. A fixed one-hour execution delay
is recommended for receipt-aware research; retaining immediate next-open is an
idealized alternative with narrower claims. Timing choice remains with the
operator. Separate review subsequently ACCEPTED_WITH_RISK the bounded proposal
and reproduced the timing constraint, without certifying venue minima or code.
The operator then chose a fixed one-hour execution delay (ED002-TIMING-20261027);
this timing decision is complete and supersedes immediate-next-open timing for
the proposed comparison only. No bridge, original design or result changed;
synthetic extension/clock alignment and independent review remain next, with no
implementation or market-run authorization inferred from that choice. Proposed
costs, rounding, horizon, freshness and inference are still unadopted. No study ran.

Subsequent continuation implemented the synthetic-only delay extension:
`ed002_delayed_bridge_20261027.md`. New explicit delayed profile retains the
300-hour signal window endingT, actual receipts throughT+1h, actual pre-fill
wallet withTclose marks, execution atT+1h, and separate signal/execution
permission checks. Immediate interface defaults remain unchanged; ledger and
frozen strategy sources unchanged.157focused synthetic tests passed, including
28new cases. Separate GATE subsequently ACCEPTED_WITH_RISK exact implementation,
independently157passed4.58s/no blockers;14review bindings verified. This is
synthetic implementation acceptance, not market-run or protocol acceptance. The
original design/review and all old economic results remain historical artifacts.

Next bounded synthetic continuation added `ed002_comparison_harness_20261027.md`:
seven-arm wrapper using unchanged dependencies, explicit caller economics,
common A/E/B with initial cash-only hour, fixed-unit controls and shared carry.
An intended benchmark component must actually enter atE; otherwise its economic
result is INCOMPLETE/unknown rather than cash relabelled as successful hold.
Incomplete or partial periods suppress the top-level profit summary.180targeted
tests passed (23new+157existing); separate implementation review requested,
READY_FOR_INDEPENDENT_REVIEW. No market/inference run or activation follows.

Subsequent operator approval was recorded without waiving a newly read blocker:
independent wrapper review REJECTED ED002-COMPARISON-01 (unbound carried entry
marker). `ed002_comparison_carry_fix_20261027.md` preserves the rejected inputs
and documents the narrow actual-trade reconciliation.5regressions failed before;
185targeted tests pass after correction. Existing dependency code is unchanged.
Separate re-review `ed002_comparison_carry_rereview_20261027.json` subsequently
ACCEPTED_WITH_RISK the correction, closed ED002-COMPARISON-01, independently
185passed6.98s;20current input hashes verified. Bounded synthetic comparison
objective complete; no market or statistical authority. Original rejection and
180-pass checkpoint remain historical evidence, not a reopened implementation.

2026-10-18 supplement: the user explicitly requested separate low-unit-price and
lower-cap top-100 tests, rather than another BTC/ETH test. See
`low_value_top100_20261018/RESULTS_V2.md`: three exploratory CMC-reference
screens, no BTC/ETH purchases, 383 historical asset IDs across 100 four-week
cycles after explicit instrument classification repair. V1 was incomplete
because truncated tags admitted stable/wrapped instruments; all v1 artifacts
and review remain preserved. Under-USD1 and ranks51..100 mean net lower bounds
+USD28.43/+USD16.11 per independent USD1,000 cycle; new entrants +USD129.35 point estimate, heavily
concentrated, median -USD1.25 and worst -USD528.27. All paired advantage
intervals cross zero; no executable edge established. Missing exits stay unknown,
not fabricated fills. Basket evidence does not change individual-symbol status,
the 25-symbol mandate, old FAILs, or operational authorization. This direct user
request authorizes the bounded screen separately from backend restoration;
restoration remains incomplete and no services were touched.

Labels follow AGENTS.md: SHOWN (evidence in repo), CLAIMED, UNVERIFIED.

### October20 correction and continuation checkpoint

The full externally shared audit is preserved, not rewritten, in
`../review_artifacts/claude_cowork_20261020/research_audit_review_cache/`.
Its seven reviewed corrections control over contradictory claims in that
external document; frozen registrations and results stay unchanged.

- Earlier Binance funding is not certified untouched history: E7 includes
  pre-December2020 prints in its expanding thresholds (`crash_brake_20261013/crash_brake.py`,
  lines18-41). A new funding question must disclose reuse, not claim a fresh holdout.
- Failed promotion or benchmark criteria do not mean every altcoin rule lost
  money. Corrected top-10 trend returned +20.5% in its 2024-26 model while
  trailing BTC (`altcoins_corrected_rerun_20261009.md`). No new edge follows.
- E1 measures all-in cost, including fees. Do not substitute that number for
  slippage while retaining a separate fee charge. Its $23-32 annual fee-saving
  illustration at constant $1,000 is conditional, not expected income or an
  upper bound on total execution improvement. Turnover already counts both sides.
- Static configured live limits are not verified effective runtime limits.
  The inspected `services/risk/live_risk_gates.py:check_live` does not check its
  parsed position-notional field. Whole-system enforcement remains UNVERIFIED;
  this observation does not authorize a risk or execution change.
- UNLOCK-1 is a proposal, not registered or run. The bounded public-document
  feasibility check is in `unlock_data_feasibility_20261020.md`: historical
  schedule versions, coverage and licensing are not demonstrated. No purchase,
  automatic FUND-1 replacement or new collector follows from that result.
- Independent $1,000 research cycles are not a funded continuous portfolio;
  selection counts alone do not bound a filter's economic contribution.
- Tracker v2's TLS repair has a separate ACCEPTED_WITH_RISK review. The operator
  supplied Mac Python3.12.10 proof: default CA count0, certifi CA count137,
  30 targeted tests passed (October20 work log). Unattended delivery remains
  UNVERIFIED here; this is not another instruction to rebuild or rerun the repair.
- CMC primary inference remains blocked by statistical-method certification,
  not merely by the February2027 date (`cmc_trending_log/confirmation_result_v2_20261009.md`,
  `cmc_trending_log/statistical_v3_confirmation_result_20261010.md`). Collection
  is separate from inference and trading eligibility.

Continue from the dated queue in `../../REMAINING_TASKS.md` and the saved review
checkpoint. Reopen only changed or contradicted evidence. Preserve the user's
lower-value/top-100 focus and the 25-symbol mandate; BTC/ETH execution research
does not silently replace that objective. No live fees, budgets, operational
startup permissions or financial-model parameters are inferred from takeover.

## 0. Scope (read first)
- **CryptKeep is multi-symbol.** See `MULTI_SYMBOL_MANDATE.md`. Project scope remains the 25 symbols in `config/candidate_universe.yaml`; this is not a current or historical trading-eligibility list. The mandate's October15 check records 24 Coinbase USD products, MATIC-USD delisted with POL-USD as successor, and XRP's historical suspension. No automatic substitution or scope change follows.
- **The findings below are research evidence for specific symbols and conditions. They are not the project's scope.**
- **Coverage (2026-10-15, after E10; `research/symbol_coverage.csv`):**
  - The 10 Coinbase core pairs have each had a standalone slow-trend test. Results:
    - CANDIDATE vs hold: ETH, AVAX, DOT;
    - INCONCLUSIVE: BTC, SOL, DOGE, ADA;
    - REJECTED under tested conditions: LTC, LINK, XRP.
  - The equal-weight 10-symbol trend portfolio was rejected vs BTC+ETH.
  - 15 symbols (BNB and the tier-2 and watchlist symbols) remain UNTESTED.

## 1. Bottom line
- **No demonstrated dependable trading income or validated profitability** in the reviewed evidence. This does not reject all possible edges or the untested universe.
  - **Candidate:** the BTC+ETH 28-day volatility-scaled trend rule has scoped historical risk-reduction evidence at the tested costs. Its registered 1.2% stress rejection stands; lower-cost results remain exploratory, not confirmation.
  - **Return:** it has no proven return advantage over BTC, and it depends on costs.
- **Literature context:** `crypto_trading_edges_survey_20261013.md` is a research survey, not proof that only one family can survive costs. Existing negative findings apply to their tested rules, assets, periods and assumptions.
- **Further work:**
  - cost reduction and risk engineering around the candidate;
  - restore the existing research/explanation path and reproducible delivery before new experiments; E10 is completed, not queued to run again;
  - prospective, pre-registered comparisons across justified subsets of the wider universe, after data, sizing, cost and evaluation contracts are frozen;
  - no unregistered signal hunting.

## 2. Costs: confirm before trusting any backtest
- **Account fee tier:** 0.25% maker / 0.50% taker per side. SHOWN for the account-level SPOT tier via an authenticated read on 2026-10-08 (`research/coinbase_fee_observation_20261008.json`). Product-specific fees are UNVERIFIED.
- **Conflicting secondary sources:**
  - entry tier 0.40% / 0.60%;
  - a reported Sep 2026 US change to 0.50% / 0.90%.
  - Both are UNVERIFIED. They do not override the dated account-level observation. BTC-USD/ETH-USD product-specific all-in rates and historical applicability remain UNVERIFIED; no new credential or account action is authorized by this brief. See `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md` for the preserved observation and remaining evidence requirements.
- **Round trip at 0.25/0.50:** 0.50% (maker/maker) to 1.00% (taker/taker), plus spread.
  - Weekly full turnover costs about 26-52%/yr.
  - Monthly full turnover costs about 6-12%/yr.
- **Never use the simple Coinbase buy/sell flow** (0.5-2% spread built in). Use Advanced only.
- **Limit fills are adversely selected:** easy fills tend to be followed by adverse moves. A backtest must model unfilled orders and post-fill drift.
- **Server:** about $20/month. This is an operator estimate (CLAIMED); the invoice is not seen. Workloads: `server_workload_inventory_20261011.md`.
- **Tax:** short-term gains are taxed as ordinary income. Brokers have issued Form 1099-DA since 2025.

## 3. What the evidence says (details and sources: `crypto_trading_edges_survey_20261013.md`)
| Scoped historical candidates / hypotheses | Access or execution feasibility unresolved | Rejected or inconclusive under tested conditions |
|---|---|---|
| BTC/ETH slow trend and volatility scaling; E10 also tested 10 core symbols, with scoped results in the registry | Futures carry / basis; existing modeled feasibility is not verified access, fees or liquidation safety | Cross-sectional momentum, size, reversal as tested (E6 basket, leader pullback; scoped in the registry) |
| Volatility scaling and rebalance bands have scoped historical results; E9's registered FAIL stands | Selling options (variance premium) | Calendar/overnight/intraday rejections apply only to the tested rules, assets, periods and costs |
| Avoidance filters are research hypotheses, not established profitable rules | Arbitrage, order flow, MEV, liquidity-pool provision | Listing/event results are limited to the reviewed models and data |
| Funding/basis crash brake: tested 2026-10-13, FAILED as this specified overlay | | Survey cautions about on-chain/sentiment signals are literature context, not exhaustive repository tests or rejection of those families |

## 4. Project results to date
| Idea | Status | Evidence |
|---|---|---|
| BTC+ETH 28d trend, vol-scaled | **CANDIDATE** | `btc_eth_corrected_comparison_20261012/`, `dsr_btc_eth_trend_20261011/`, `stress_fee050_exploratory_20261011/` (exploratory), `edge_classification_btc_eth_20261011.md` |
| Same rule, registered stress test at 1.2% | REJECT (stands) | `research/research_corrections_20261009/stress_corrected_v1.json` |
| Altcoin event rules (~448 configs), breakout, recovery/regime, short-hold, CMC proxy, dynamic Coinbase, hybrid | Rejected or inconclusive | `consolidated_economic_summary_20261010.md`, `strategy_decision_report_20261011.md` |
| Top-gainer pullback dip-buying (8 variants) | FAIL: all lost before and after costs | `leader_pullback_study_20261012.md`, `leader_target_test_20261012.md` |
| Dip-recovery screen | Withdrawn (used future information) | `dip_recovery_screen_20261012.md` |
| Weekly altcoin cross-sectional momentum | FAIL; simulator defect annotated | `xs_momentum_20261012/` |
| Funding-rate crash brake (E7) on the candidate | FAIL on registered condition 1: D drawdown unchanged; H drawdown modestly lower, but ending value lower in every period. Original verdict stands; redundancy is the report's scoped interpretation | `crash_brake_20261013/` |
| Composite v1: 20/50/100/200-day trend ensemble + 10-pt rebalance band (E8) | FAIL: better in 2017-23, much worse in the reused 2024-26 historical segment (Sharpe 0.45 vs 0.87); the original result label is preserved | `composite_v1_20261013/` |
| Band 0.10 alone on the unchanged candidate (E9) | FAIL on the registered turnover criterion (0.90x, needed ≤ 0.75x); otherwise better Sharpe and ending value in D and H at both fees and half the trades. Criterion mis-specified; resolve with FORWARD tracking, not a re-test | `candidate_band_20261013/` |
| Slow-trend portfolio across 10 core pairs, equal 1/N (E10) | FAIL vs BTC+ETH incumbent (Sharpe 1.20 vs 1.46 in D, 0.51 vs 0.88 in H). Standalone: trend cut drawdowns on every symbol; per-symbol statuses in the registry | `multisymbol_trend_20261015/` |
| Chronos-2 volatility forecast vs trailing std (VOLFC-1, Module A) | FAIL on all three registered criteria: mean weekly rank correlation 0.5217 vs 0.5123 for trailing 60-day std (needed +0.03). Plain EWMA 0.94 ranked best (0.5283), an observation, not a tested claim. Module A keeps trailing 60-day volatility | `chronos_vol_forecast_20261018/RESULT.md` |
| Wikipedia attention as a signal (ATTN-1, phase 0) | BLOCKED_DATA: mapped coins cover 55.6% of the primary sample's selections (43.4% strict) against a required 70%; no pageviews were requested | `attn1_phase0_20261021/README.md` |
| New top-100 entrants, Coinbase-tradable only (ENTR-CB-1) | STOP under its pre-registered rule: paired mean vs control -7.17 per $1,000 cycle, and -30.00 without the largest cycle (CMC weekly prices; exploratory; reused archive). No further variants on this archive | `coinbase_tradable_entrants_20261019/RESULTS_V1.md` |
| Maker vs taker execution | Draft v3 correction, NOT frozen; operator chose delayed execution plus arrival-book observation. Account-tier evidence exists; product fees, timestamp/coverage and inference contracts remain unresolved. No collection or scoring authorization follows | `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md` |
| CMC trending | Collecting; primary analysis no earlier than 2027-02-15 | `cmc_trending_log/` |
| Forward tracker v2 | Separate research-only Codex schedule recorded ACTIVE; first delivery October18 20:47 New York remains UNVERIFIED. README records 27 tests and independent review; this brief does not rerun them. v1 artifacts/schedule are preserved, not independent evidence. **Update 2026-10-30 (SHOWN in `state/`):** the 2026-10-18 decision was reconstructed and recorded 168.87 hours late (2026-10-26 00:52 UTC); the 2026-10-25 decision was recorded on time (0.87 hours). Marks to 2026-10-25: rule $985.38, hold BTC $970.83, 25/25/50 $982.95, cash $1,000. One week; no conclusion | `paper_btc_eth_trend_v2_20261012/README.md` |
| Corrected ES prospective trial | Fixed endpoint completed; saved host report independently ACCEPTED_WITH_RISK. Zero orders/fills/positions, zero paper trading PnL; efficacy INCOMPLETE, no extension or promotion | `../checkpoints/es_prospective_endpoint_result_2026_10_16.md` |

Selection accounting: pass2 records a convention-specific floor of 747 configurations (577+113+57), not a verified complete selection count or effective N. Its CSV has six exact family counts, two lower bounds and one unknown; symbol pooling and selection exposure still need reconciliation. The older 576 and effective-N estimates are historical, not validated current inputs. See `trial_ledger_reconciliation_20261015/pass2_findings_20261015.md` and `discovery_engine_proposal_review_20261016.md`. No DSR is recomputed from this correction.

## 4a. Operational evidence is separate from research results
- **SHOWN in the October16 consolidated audit:** the documented local `127.0.0.1:8002/healthz` route refused connection. Older successful disposable integration tests do not establish current service availability. Other endpoints, durable operation and external alert delivery remain UNVERIFIED unless supported by a newer receipt.
- **Recorded point-in-time collector status:** the audit saw existing paper/context collector PIDs and fresh status files. This is not continuous health or approval to restart them.
- **Scheduling:** the v2 tracker schedule above is recorded configuration, not proof of its first unattended run. It is Sunday20:47 New York (UTC changes with daylight saving), not a fixed Monday UTC schedule. Do not create a duplicate job.
- **Test baseline:** the recorded broad run was 4,679 passed, 2 failed, 76 skipped and 1 collection error. A later isolated proxy test passed; that does not make the broad suite green. See `consolidated_review_20261016.md` for commands and limits.
- Operational permission is scoped, not ongoing. The separately authorized October27 V6i attempt is complete and consumed; its limited success is recorded above. No new service, Docker, server, account, credential, schedule or trading-operation change is implied.

## 5. Research rules (non-negotiable)
1. **Write the rules down before seeing data or results.** Amendments must be dated, made before running, and never replace the original.
2. **Count every variant tried.** Report all of them, losers included. Correct for selection: DSR at realistic N, with sensitivity.
3. **Use real costs:** fee + slippage on every trade, for every strategy AND every benchmark. Report results at both the confirmed tier and a higher-cost tier.
4. **No price filling.** A missing candle is not a tradable price. Failed downloads are recorded as failures, never as "no trading".
5. **Execution:** decide at a close, trade at the next open (or model limit fills honestly). Executions are labelled modelled unless they are actually observed.
6. **Benchmarks:** hold BTC, a fixed BTC/ETH/cash mix at comparable exposure, and cash. Label mixes fully (e.g. 25/25/50 means 50% cash).
7. **Judge new ingredients against the current candidate,** not just against BTC.
8. **Previously examined history is not untouched holdout data.** In particular 2024-26 was reused in candidate selection and later studies. Preserve original D/H labels as historical artifact labels, but use those periods only for exploration, reproduction or sensitivity. Genuine confirmation requires a dated frozen protocol before unseen observations; do not backdate activation or retune after inspection.
9. **Preserve originals and registered verdicts.** Exploratory results are labelled exploratory. No profitability claims; DSR is not a profit probability.
10. **Universe and survivorship:**
    - Survivorship bias is large (about 53% of tracked tokens have failed). Use datasets that include delisted coins, and say what is still missing.
    - Every symbol tested counts as a trial.
    - Every negative result is scoped to its symbols and conditions in `research/symbol_coverage.csv`.

## 6. Accepted next steps (2026-10-16)
1. Correct this active brief without rewriting frozen registrations or results.
2. Diagnose and repair the existing research/explanation source path; distinguish local fixture proof, endpoint availability and sustained operation. Operational changes require separate authorization.
3. Triage is complete for the bounded source/fixture scope, not for whole-suite integration: native Git/audit isolation repaired (8 controlled cases), proxy failure traced to sandbox bind denial, and article-body collection verified in a disposable dependency overlay (6 cases within a 42-test selection). Root `.venv` still lacks `bs4`; retain the original 4,679/2/76/1 broad result. See `research_path_repair_handoff_20261016.md`. Do not repeat this triage as an unstarted task.
4. Packaging is complete for the independently reviewed V3 slice: exactly 39 allowlisted files, hashes, preserved originals and a clean extracted 33-test receipt. October17 read-only verification confirms every archived/current file still matches. This reproduces independent per-symbol/arm behavior, not a shared-capital portfolio. Preserve the 25-symbol mandate, raw archives and verdicts; do not repackage or rerun failed backtests without new contradictory evidence.
5. Only after that path is usable, propose one prospectively registered comparison with universe, missingness, carry-forward sizing/cash, costs, benchmarks and acceptance criteria frozen before outcomes. No experiment is authorized by this brief.

Completed work is not a new queue: E7/E8/E9/E10 retain their registered FAIL results; tracker v2 and its band10 account already have saved code/review/schedule records. Maker/taker draft v3 still needs its remaining evidence and independent contract review before freeze, not a repetition of earlier unqualified arrival assumptions.

### Restoration checkpoint, October17 New York

SHOWN: a fresh paired selected-metadata capture at October18 03:22:50 UTC
(October17 23:22:50 New York) found the same seven pinned research containers
exited, zero restarts, restart policy `no`; both retained observations match.
Four source archives (241 per-application records) and 11 previously reviewed
artifact/source hashes still match current bytes. The refreshed four-service
recipe is review-only and is refused by the executable plan loader. The new
30-test collector/recipe selection passed; it is not a new full-suite run.

Installation and genuine explanation delivery remain INCOMPLETE. Outstanding
evidence includes actual mounted import/dependency behavior and strict registry
isolation; `build --pull=false --network=none` does not enforce the latter.
No accepted executable installation manifest was fabricated. No build, replacement,
startup, credential-value access or explanation request occurred in this batch.
See `../checkpoints/companion_batch_closeout_20261017.md` for the consolidated
evidence and operational boundaries. New comparison registration remains gated
on a usable explanation path, not on repeating already completed packaging.

Later October17 native builder check: the reviewed bare-ID parent correction
passed one present-parent and one deliberately missing-parent request. Seven
selected original container snapshots stayed unchanged. Saved evidence was
independently ACCEPTED_WITH_RISK; image/cache retained, no service installation
or startup. See `../checkpoints/companion_local_parent_proof_20261017.md`.
This narrows the registry-fallback evidence gap for that exact path; it does
not establish whole-install policy, import isolation or a usable explanation.

October18 isolated Python3.11 test: audit-log and risk-stub imports passed;
memory reached source validation then failed with RuntimeError, with insufficient
retained detail to identify the guard. Orchestrator was not attempted. All three
test containers were removed; the seven original services stayed unchanged and
stopped. An independently reviewed offline diagnostic correction does not resolve
that failure or authorize a retry. Complete imports and restoration remain
INCOMPLETE. See `../checkpoints/companion_installed_imports_20261018.md`.

October18 targeted continuation (04:53 New York): memory reached source
validation but failed the preserved activity guard, with one denied socket
operation and no denied repository import. Exact socket operation/caller is
UNVERIFIED; no outbound traffic or actual service failure is established.
Orchestrator was not attempted. One temporary helper removed; seven original
selected container snapshots unchanged/stopped. No rerun of the two passing
modules, package changes or service startup. Restoration remains INCOMPLETE.

October18 attribution follow-up (04:59 New York) identified the sole blocked
operation: socket bind from urllib3.util.connection._has_ipv6, line127. Memory's
application import returned before the strict zero-denial validation rejected
it. No absent dependency is shown; exact installed caller body/address not
captured. Orchestrator still unattempted. Guard unchanged, one helper removed,
seven selected original snapshots unchanged. This diagnoses the test rejection,
not a working explanation service. No further retry or contract change implied.

Read-only caller-source inspection subsequently found identical urllib3 code in
the stopped memory/orchestrator containers: `_has_ipv6("::1")` attempts only a
localhost ephemeral-port bind, catches failure and closes its socket. This
supports a capability-probe diagnosis, not an outbound request; exact loaded
helper bytes/arguments were not captured. Guards/acceptance unchanged, no new
import test, package change or startup. Seven selected original snapshots match.
See the checkpoint for hashes, source preservation and proposed narrow contract.

An optional source/code/argument-pinned blocked-local-probe contract is now
implemented and independently ACCEPTED_WITH_RISK offline (57 targeted tests).
Strict zero-denial mode remains default; the opt-in still physically denies the
bind, records its count/evidence, and rejects other or repeated operations.
No actual import attempt under this contract or existing-service startup yet;
installed3.11 behavior and explanation restoration remain UNVERIFIED/INCOMPLETE.

October18 05:23 New York: one authorized remaining-only v2 run passed actual
Python3.11 memory/orchestrator imports with synthetic settings/frozen source and
no lifespan. Memory's single local probe stayed blocked and visible; orchestrator
had zero events. Both helpers removed, seven selected original snapshots
unchanged. Separate evidence review ACCEPTED_WITH_RISK. Restricted import gap
closed; complete SDK/storage startup, installation and explanation still not
proven. Do not repeat audit/risk or infer whole-policy approval.

Portfolio reuse assessment is complete for the named source surfaces, not an
implemented ED-002 portfolio. Shared cash already exists in E10; baseline
accounts remain independent. Specific integration/contract gaps and existing
tests are in `portfolio_reuse_assessment_20261018.md`. No failed study rerun,
new comparison or financial-logic implementation. Consolidated remaining
installation/research boundaries: `../checkpoints/companion_batch_closeout_20261018.md`.

**Do not:**
- run unregistered signal hunts on any symbol;
- rescue failed variants;
- tune parameters on the holdout;
- generalize a scoped rejection to a whole asset class;
- add paid data or infrastructure without a cost-benefit case (`research_budget_90d_20261011.md`).
