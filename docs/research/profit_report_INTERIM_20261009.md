# R12 profit-focused report - INTERIM (not final; R11 forward evidence not yet mature)

Claude (cloud session), 2026-10-09 ~11:25 UTC. Every number below is read from the corrected artifacts in
research/research_corrections_20261009/ at the 0.50% observed Coinbase taker fee (primary) unless noted. All are
simulated MARKED balances on historical data - sample results, not forward-confirmed and not realized profit.
Cash = $1,000 kept as $1,000 (0%). Nothing here authorizes trading.

## Hurdle
Shared infrastructure ~$20/month = $240/year. On a $1,000 account that alone is a 24%/year hurdle; on $10,000 it
is 2.4%. A strategy must beat BTC buy-and-hold AND clear this after fees to be worth running.

## Scorecard (best COMPLETE candidate per family vs matched BTC, same window)
| Family (artifact) | Window | Best candidate result | BTC hold | vs cash | vs BTC |
|---|---|---|---|---|---|
| Dynamic Coinbase rotation/breakout (dynamic_corrected_v2) | prior 10 months, outage policy | $270.44 from $1,000 (breakout trail 8%); rotations $0-$15 | $582 | loses | loses |
| Short holds, top gainers (short_hold_corrected_v1) | last 60 days | $736.65 (top-3 by 24 h gain, hold 12 h) | not in artifact | loses | - |
| Short holds | prior 10 months | $1.97 best | - | loses | - |
| Hybrid momentum/trend (hybrid_corrected_v1) | test segment, marked | +8.0% (trend each coin, vol-scaled 28d); 4 of 12 INCOMPLETE | +93.3% | small gain | far behind |
| Altcoin event rules (altcoins_corrected_v1) | test segment | best $601.00 (new listings) from $1,000; block Sharpe vs BTC range entirely below 0 for all 4 complete | $1,840.38 | loses | loses |
| BTC+ETH 28-day trend (stress_corrected_v1) | FULL period | $102,425.63 (Sharpe 1.42, max DD 51.9%) | $134,319.33 (Sharpe 1.05, DD 83.8%) | gains | behind in $, better risk; REJECTED by its registered rules (5/13 variants) |

At the registered 1.2% stress fee the BTC+ETH rule ends $50,447.62 vs BTC $133,390.25.

## What this means for profit
- No tested rule beat simply holding BTC in dollars in its corrected window.
- Two families beat cash on paper (hybrid vol-scaled trend +8.0%; BTC+ETH trend), neither beats BTC, and the
  BTC+ETH rule failed its own robustness test. At a $1,000 account the $240/year infrastructure cost would erase
  the hybrid's +8.0%.
- Lower drawdown (BTC+ETH rule 51.9% vs 83.8%) is the only consistent advantage found; it is not a profit edge.

## Still open before a FINAL report
Forward evidence: CMC trending study (scoring no earlier than ~2027-01; gate = all ranges above zero) and the
Coinbase USD confirmation study (evaluation 2026-10-10 to 2027-04-08, checkpoint 2027-01-08; not yet activated).
Realized profit requires real fills; none exist.
