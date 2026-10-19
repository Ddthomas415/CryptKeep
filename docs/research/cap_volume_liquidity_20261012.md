# Capitalization, volume and execution context

AUDITOR. Public observations October12,09:23-09:24Eastern. No privateaccount
access,orders,tradingrules or frozenexperiment changes.

CoinGecko coins/markets, exact IDs gitcoin/reserve-rights-token, last_updated
2026-10-12T13:22:55Z, returned:

| Asset | Market capUSD | Global24hvolumeUSD | Volume/cap | Circulating/maxsupply |
| --- | ---: | ---: | ---: | ---: |
| GTC |25,927,083|91,442,784|3.53x|87.49%|
| RSR |151,087,515|194,391,012|1.29x|62.55%|

This is gross turnover,not netmoney entering thetoken,uniqueholder turnover or
confirmed genuine demand. Reportedvolumecan repeatedly trade the same supply.
Cap isprice times circulating supply,not investedcash or availableorderbookdepth.
Fullydilutedvaluation was29,633,830GTC and241,534,529RSR; these do not establish
futureunlock timing,forced selling or apriceforecast.

Coinbase publicproducts/books observed13:24:48UTC:

| Asset | Approx24hUSDvolumeproxy | Spread | Visiblebiddepth within1%ofmid | Visibleaskdepth within1%ofmid |
| --- | ---: | ---: | ---: | ---: |
| GTC |3,284,380|120.30bps|881.10USD|2,009.90USD|
| RSR |3,498,416|12.43bps|13,488.28USD|3,497.37USD|

Coinbasevolumeproxy isreportedbasetokenvolume times currentprice,not exact
historicalVWAPnotional. Only50levelsrequested;depth is displayed/ephemeral,not
guaranteedfillliquidity. Global and venue snapshots have differenttimestamps;
no crossvenuearbitrage or fullysynchronized comparison is claimed.

RSR had narrower spread and more nearbybiddepth at thisinstant. GTC's higher
turnover/cap does not establish betterexecution or betterfuturereturn.
The requestedhourlywatch now includes cap/supply/globalvsvenuevolume and
spread/depth context,identity-first joins and explicitmissingdata. No cap/volume
threshold was turned into a tradinggate. Creation/update not unattendedrunproof.

Sources:
https://docs.coingecko.com/reference/coins-markets
https://www.coingecko.com/en/methodology
https://api.coinbase.com/api/v3/brokerage/market/products/GTC-USD
https://api.coinbase.com/api/v3/brokerage/market/products/RSR-USD

No newsourcecode/tests. Publicrequests/calculationsSHOWN; sustainedrelation,
predictiveedge and profitabilityUNVERIFIED. A firstlocalbookcomparison command
had a syntaxerror before requests; corrected read succeeded withoutmutation.
