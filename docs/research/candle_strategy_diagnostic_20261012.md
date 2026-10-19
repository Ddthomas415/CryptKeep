# Completed-candle strategy diagnostic

AUDITOR; public Coinbase observation October12 10:31Eastern. Read-only evaluation
of unchanged repository EMA, Donchian, RSI mean-reversion, momentum and pullback
presets. No strategy tuning, portfolio sizing, orders or campaign mutation.
Receipt: research/candle_strategy_diagnostic_20261012T143118Z.json, rawcandles,
sourcehashes,historycounts and outputs preserved. This is not a backtest, accepted
profitable strategy or instruction to act on the user's holdings.

The requested300bargrids contain missing intervals. Initialstrictgridassertion
failed; no falsecomplete claim. Subsequent diagnostic uses only completed hourly
and5minute contiguoussuffixes, no filling of missing bars. Histories:
GTC5m54bars/1h298;RSR5m117bars/1h300. Fifteenminute suffixes19/46bars are below
the shared52bar diagnostic requirement and are unavailable, not neutral signals.
Pullbackrecovery itself reports insufficient_data forGTC5m; distinguish this from
an informedhold. Different seed/historylengths limitcrossmarketcomparability.

| Preset | GTC5m | GTC1h | RSR5m | RSR1h |
| --- | --- | --- | --- | --- |
| EMA12/26 |hold,no freshcross|hold,no freshcross|hold,no freshcross|hold,no freshcross|
| Donchian20 |hold,insidechannel|hold,insidechannel|hold,insidechannel|hold,insidechannel|
| RSImeanreversion |hold,noedge|hold,highvolatilityfilter|hold,noedge|hold,noedge|
| Momentum |hold,1.875%<2%|hold,RSI77.94>=75|buy,momentum_entry|buy,momentum_entry|
| Pullbackrecovery |unavailable|sell,rebound_mature_exit|hold,RSI>55|hold,RSI>55|

Latest5mcandle ends10:30Eastern; latesthourlycandle ends10:00Eastern. HourlyGTC
selloutput is therefore an earlier modelcondition, not a new10:31marketorder.
EMAholdmeansnofreshcross,notflatmarket. No unanimousbuyconsensus is present.
Momentum andmeanreversion use different RSIimplementations; quote each preset's
ownindicator rather than silently mixing them.

GTC5mclose0.326,priorchannelupper0.329,RSImeanreversion65.83,volume ratio2.74.
The existing0.05%breakoutbuffer implies a close above0.3291645 for that channel,
with otherfilters passing. Channelrolls eachbar; this is not a permanent target.
RSR5mclose0.002503,priorchannelupper0.002584,RSImeanreversion57.65. Its momentum
modelreads+2.582%betweencompletedcloses andRSI62.87;1hmomentum+5.4754%/RSI67.87.
Signals do not include the user's retailtransaction/exitfees or futurefill certainty.
No feesadjustedpositiveEV,profitability,protective-exit instruction orforecasterror
calibration inferred. Sourceunchanged,no newtests; savedoutputreplayreview requested.
