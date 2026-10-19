# Repeated daily direction switches

AUDITOR; exploratory public Coinbase scan,182completed UTCdays.
Definition: consecutive open-to-next-open returns with opposite nonzero signs.
This is not the Coinbase rolling24hpercentage crossingzero or intradayoscillation.
Zero-returndays are excluded from signpairs and separatelycounted; no pricefilling.

Universe:25currentlyhighquote-volumeUSDproducts,excludingnamedstablecoins,plus
GTC/RSR.23of27passedexact183unique dailycandlegrid;VVV/LINK/W/ADA requests failed
HTTPError, so rankingcoverage incomplete. Failedmarkets were not assignedzeros.
Originaldata retained inresearch/reversal_scan_20261012T145033Z.json.

| Product | Signswitches | Firsthalf | Secondhalf | Mean nextday after red day, gross | Same mean at modeled0.5%eachfee |
| --- | ---: | ---: | ---: | ---: | ---: |
| AVAX |56.65%|51.16%|61.63%|-0.008%|-1.003%|
| QNT |55.93%|53.41%|59.09%|+0.705%|-0.297%|
| STRK |54.86%|49.06%|58.89%|+0.415%|-0.584%|
| ICP |54.14%|50.00%|58.89%|+0.159%|-0.837%|
| TAO |54.14%|51.11%|56.67%|+0.475%|-0.525%|

AVAX is the mostfrequent dailyalternator amongcompletedmarkets,notclockwork.
QNTshows a smallerbutpositive grossafter-red mean; this does not survive the
modelcost. Typicalabsolute dailyAVAXmove1.77%,QNT1.55%,ICP2.23% are whole-day
magnitudes,notcapturedstrategyreturns. STRK has21flatdays,so its144signpairs
are less directly comparable withICP/TAO181pairs. Alwaysshowdenominators.

Noholdout,multiple-testingadjustment,dependentintervals,spread/slippage or
realizedfills. The after-red model is diagnostic,not an executedportfolio; named
0.5%fees are assumptions,not the user's observedretail purchasefees. Higherwin
frequencycanstilllose through loss size/costs. This does not establish a profitable
buy-red/sell-green rule orauthorize shorts/trades. Current-universebias retained.
