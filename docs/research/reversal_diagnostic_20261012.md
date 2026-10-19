# Fixed reversal diagnostic

ENGINEER. Historical diagnostic, CF-MODELLED, not fresh holdout or live profit.
Plan frozen before execution: research/reversal_diagnostic_plan_20261012.json.
Results: research/reversal_diagnostic_results_20261012.json. Source/data hashes
checked before and after execution. Original scan data preserved unchanged.

## Rules and scope

AVAX/QNT/ICP were selected from already explored data. Existing unchanged RSI
mean-reversion and volatility-reversal presets, daily bars,52warmupbars,130evaluation
bars. Signals see completed candles only; execute nextopen. No perfectlow/high fills,
intrabarstops,parametergrid or newly relaxedfilters. Terminalremainingposition is
liquidated at lastcompletedclose as explicitly modeled,not nextopen execution.
Signal-only simulation does not include the campaign's protectiveexit/risk stack.

Each arm has1000USDcash,one100USDnotionalposition plusfees at a time,nopyramiding.
These are independent researchaccounts,not the user'sEURholdings or allocation.
Comparecash and100USDbuy-and-hold plus remainingcash,not1000USDbuy-and-hold.

Costs per side: primary50bpsfee+10bpsslippage; stress100+25;retailsensitivity300+50.
Assumptions,not confirmedfee/spread for these orders. Retailsensitivity is not the
user's exact futurefee.36armruns include18strategy and18control runs,allretained.

## Results

| Coin | RSIreversion | Volatilityreversal primary | Volatilityreversal retail sensitivity | Equalnotionalhold primary |
| --- | --- | ---: | ---: | ---: |
| AVAX |0trades|+1.60USD,1closedcycle|-4.26USD|+34.85USD|
| QNT |0trades|0trades|0trades|+232.55USD|
| ICP |0trades|0trades|0trades|+10.28USD|

No-trade arms did not exercise the profit hypothesis; they are INCONCLUSIVE,not
proven losers. AVAX's one trade is insufficient for statistical evidence or a
repeatableedge. Its small modeledprofit becomesnegative underhighercosts.
Do not advertise the holdingcontrol'shindsightprofit as a reason to buy now.
This result does not demonstrate profitablecapture of recurring priceoscillation.

## Verification and disposition

26targeted tests passed: tests/test_reversal_diagnostic.py plus
tests/test_next_open_research.py. Fullsuite notrun for isolated researchwrapper.
Separate source/plan review requested; READY_FOR_INDEPENDENT_REVIEW.
Separate reviewer independently reproduced all36runs exactly and26tests passed.
Inherited defect found in volatility_reversal.py:59: the default volume average
sums four previous bars but divides bythree, understating its computed spike ratio
by25%. Consequently the frozen diagnostic tests existingcode,not a correct arithmetic
mean of the selected window. Entries may be suppressed. Preservedplan/results are
not replaced; a repaired arithmetic variant requires its own version and review.
Do not infer noopportunities from zeroentry arms or loosen otherfilters here.
Reviewer initialworklogfinding was a timing overlap: the parent added the required
handoff while reviewran. Finaldisposition requested after this disclosure.
Final separateGATE: ACCEPTED_WITH_RISK solely as existing-code historical diagnostic.
Source/data/plan/result hashes remainmatching. No correctedvolumeaverage, predictive
edge, profitability or liveexecution accepted. Bounded diagnostic objective complete.
No privateaccounts,orders,campaignchanges,promotion orparameterretuning.
Nextdecision must not loosenrules against thissamehistory to manufacturetrades.
Any newintraday/range rule requires a separately recordedhypothesis and later
confirmationdata; dailyalternation does not establish intradaypredictability.
