# Hourly leader recovery: fixed research scope

HIGH financial research, READY_FOR_INDEPENDENT_REVIEW once results produced.
No private APIs, accounts, orders, settings, collectors or automation changes.

## Rules fixed before download/results

Plan research/hourly_leader_plan_20261012.json records registration UTC and source
hash. Download 312 completed hourly bars per current eligible USD product, then
use24 bars for warm-up and288hours (12days) for leader observations. All403 current
eligible products from the saved17:06UTC paginated snapshot requested. Rank only
markets with25 contiguous hourly closes and positive current-hour trading volume.
Rank change is current completed close / close24hours earlier minus1.

Each hourlyleader observation is its own overlapping event, not a portfolio trade.
Running peak is updated only with observed hourly closes. Wait up to72hours for
a10%/20% closing-price pullback. Buy at next hourly open. Profit targets5%/10%
above modeled entry require a completed hourlyclose; sell at following open.
Timeout24/48hours after entry. Retain gaps, terminalwaiting, open and pending exits.
No future-full-window admission filter. Last leader observation retained too.

USD1000perevent includingentryfee. Fee50bpseachside and adverseprice25bpseachside
are assumptions; historical executable spreads are absent. Same-timesBTC control
perclosed event. Gross, closed-net, unresolvedmarks and event sums kept separate.
First/last6day leader cohorts share a finalcutoff; firstcohort outcomes can cross
themidpoint. Therefore these are descriptive cohorts, NOT independent validation.

## Material limits

Current-listed universe excludes delistedmarkets; rankable coverage varies with
missingbars. Reconstructed hourly24h returns are not Coinbase's exact historical
live leaderboard. Shortrecentdata includes today'smarket; not untouched holdout.
Repeatedleadercoins/overlapping events exaggerate apparent sample independence.
No portfolio capitalallocation, empiricalcostcalibration or significance claim.

Originaldaily studies remain preserved. Three targetedtests passed before data
collection: next-open target, nofuturegap admission, timeout/gap/openretention and
closed-onlylabels/costbudget. Nofullsuite; noexistingproductioncodechanged.

## Results: positives and failures both retained

403/403 public requests succeeded, zero request failures. Because some markets
lack25 contiguous hourlybars, only258-312markets/hour can be ranked. Thus these
leaders are #1 among rankable markets, NOT certified #1 across all Coinbase.
Evaluation: Sep30 17:00UTC through Oct12 17:00UTC, end exclusive,288hourlyleaders.

Eight primary event arms have correlated repeated entries. Dependency audit keeps
the first chronological observation for each identical symbol/entrytimestamp;
this is a reporting robustness check, not optimized strategy selection. Different
entrytimes can still overlap. No sums or averages are an executable portfolio.

| Dip | Target | Max hours | Distinct entries | Closed | Closed net winners | Mean closed net USD | Mean closed-plus-unresolved-marks USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
|10%|5%|24|79|74|41|-4.35|-12.31|
|10%|5%|48|79|71|50|14.90|-0.06|
|10%|10%|24|79|71|25|-28.53|-34.90|
|10%|10%|48|79|68|34|-7.17|-20.66|
|20%|5%|24|56|51|35|29.10|23.62|
|20%|5%|48|56|46|40|52.03|37.48|
|20%|10%|24|56|51|23|5.19|1.85|
|20%|10%|48|56|44|31|55.23|36.27|

All USD figures are perUSD1000scenario and modeled net of stated assumed costs.
Open-position marks are not sales/realizedprofit. All distinctentries have a
savedmark orclosedoutcome, but missing-bar events can have stale lastmarks.
Positive20%arms deserve further investigation; none is statisticallyvalidated.
The48hour5%target has56distinctentries,46closes,10unresolved; worst primary
closedloss -USD160.89. Primary repeatedevent view is190closes/158wins mean+$40.51;
first6dayleadercohort+$63.41,last6day+$13.96. These are not independent periods.

The10%/5%/48hour closed-onlypositive disappears after unresolvedmarks. Positive
conclusions must not silently select that closed-only sample. The20%/10%/24hour
primary all-event markedmean isnegative despite its distinctentrymarkedmean being
slightlypositive; weighting dependence changes the conclusion. Preserve both.

Dailytestnegative andhourlytestpositive do NOT isolate a frequencyeffect: periods,
dipwait andtimeouts differ. Twelve-dayhistorical evidence/current-universecoverage
cannot demonstrate an enduring edge. Eightarms constitute multiplecomparisons.

Artifacts: hourly_leader_plan/raw/results_20261012.json and
hourly_leader_dependency_audit_20261012.json underresearch/. Originaldailytests
unchanged. Six targetedtests passed. SeparateFaradayreviewpending. No liveaction.

## Separate review received

Faraday GATE: ACCEPTED_WITH_RISK for the frozen historical diagnostic and
dependency supplement only. Independently reconciled2304events andallhashbindings;
six tests passed. No blocking implementation findings. Statistical edge,
executableprofitability andportfolio returns remain UNVERIFIED.

Importantvaluationlimit: three unresolvedmarks are105-107hours old. Thus+$37.48
is NOTcommon-cutoff currentvaluation. It must not be called current orrealizedprofit.
Positivecandidate claim permitted only underthese frozenmodel assumptions.
