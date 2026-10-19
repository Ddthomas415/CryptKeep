# Coinbase completed-warmup coverage

AUDITOR. Observation covers September27,2026 12:00UTC through October8 23:00UTC
exclusive:275completed hourly buckets. Full300hour planned warmup is not yet
available. No registration, activation, signals or evaluation results generated.

## Source and archive evidence

SHOWN VERIFIED_ENV: existing bounded public backfill tool, five exact Coinbase
USDT products,limit300,max2pages,max300bars per product. Canonical symbol routing
was inspected and matches each requested USDT symbol without substitution.
Separate research/coinbase_confirmation_v1/public_archive.sqlite only.
Per-product receipts saved alongside the archive; default/OKX archive untouched.

| Product | Expected completed hours | Stored hours | Missing |
|---|---:|---:|---:|
| BTC-USDT | 275 | 275 | 0 |
| ETH-USDT | 275 | 275 | 0 |
| SOL-USDT | 275 | 275 | 0 |
| ADA-USDT | 275 | 273 | 2 |
| XRP-USDT | 275 | 192 | 83 |

Strict coverage CLI reports BTC/ETH/SOL ARCHIVE_VERIFIED,ADA/XRP INCOMPLETE,
all_markets_completeFalse,full_phase_completedFalse. Receipt:
research/coinbase_confirmation_v1/warmup_preflight_20261008.json.
Exit0 means the coverage command completed, not that coverage passed.
ADA missing September30 04:00/08:00UTC; XRP has83missing buckets across sample.

Seven additional direct public GET candle requests used exact productIDs,
start1790510400,end1791500400,ONE_HOUR,limit350. Raw timestamps inside the
end-exclusive window independently reproduce ADA273/XRP192 and the same
missing buckets: this is not merely a local loader row-count discrepancy.
It does not prove why Coinbase omitted those buckets; no no-trade/spoofing/
exchange-outage explanation is asserted. No gap filling or row substitution.

Official endpoint:
https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/public/get-public-product-candles

## Preservation alternative

The same direct request window on BTC-USD,ETH-USD,SOL-USD,ADA-USD,XRP-USD
returned all275expected hourly timestamps for every product. This establishes
sampled timestamp coverage, not numeric OHLCV validation, full300hour warmup,
future continuity, account tradability or executable liquidity. No USD prices
were inserted into the USDT archive or used to evaluate strategies.

Raw public-response SHA256 from the bounded direct probe:

| Product | SHA256 |
|---|---|
| ADA-USDT | 7687ea808bedb5750b519e562ff32cfe693472743a233adb2719f28a18ecc558 |
| XRP-USDT | fed40a83926bb867f6433e27e92282c91f27d7194992f7e23cc6ded70467e879 |
| BTC-USD | c3931e7426aa34d43e2dbd302291d73e77d02b258956864f2447c676af728156 |
| ETH-USD | 60bba72dd58b6fae78ae3902d96cca1946f287dc4133fff038f49404a60ef69d |
| SOL-USD | 9e8695bb5eb27d2218646e6389e6789489e8af817a61adbfafae06cd6b9ccca9 |
| ADA-USD | f12b56b3c97ffe3096cc2a57cb6d414c0a08f01b9251cd29f14420dd997cf79a |
| XRP-USD | b0c44c21f6db5b1d2eff21ea47bdc76fd738db39a62e93521aaf16b83c212cf6 |

Hashes are command-observed response identifiers; raw bodies were not archived
by this direct comparison command. The saved USDT backfill/coverage is replayable
locally. USD comparison can be repeated publicly; no stronger preservation claim.

## Impact and decision

All-five USDT activation cannot meet the current strict continuity contract.
This is source-data evidence, not a reason to drop ADA/XRP, relax integrity,
invent candles or reframe the platform as three coins.

Recommendation: separately revise confirmation to all five Coinbase USD products,
retain all strategies and strict grids, keep USDT preflight and prior OKX results
intact. Quote currency changes; do not label it the identical USDT study or mix
its cash/PnL with USDT without an explicit conversion. USD products also expose
USDC aliases; exact requested product identity must remain enforced.
Alternative: preserve strict USDT draft and report those two markets infeasible,
without silently narrowing the universe. A later independent no-trade-bar
methodology would be a new hypothesis, not repair by fabricated prices.

Operator decision required before the USD contract change. No live/campaign
authority requested. Runner implementation independently ACCEPTED_WITH_RISK,
40targetedtests independently passed; real data preflight demonstrates that
code support is not data readiness or profitability.

Separate read-only AUDITOR independently verified saved USDT counts,gaps,
allfivebackfill hashes,BTC/ETH/SOL strict row hashes and contract identities.
Confirmed no registration/simulation and partialwarmup flags. Direct-public
replication andUSDcoverage were shown in the sending thread's command output,
but not independently rerun or reproducible from saved response bodies; no
claim of independent USD validation is made. USD numeric validity unverified.
