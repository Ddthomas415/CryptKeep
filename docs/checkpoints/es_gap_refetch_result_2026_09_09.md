# ES Bounded Gap Re-fetch Result

Active role: AUDITOR. Read-only public-source check; research artifacts only.

SHOWN: a bounded Coinbase BTC/USDT 5m re-fetch covered all three qualified trade
windows with complete pagination, using 10 OHLCV calls (2, 3, 5) within a 15-call
budget. Exchange metadata discovery is additional to this OHLCV-call count.
The sandbox attempt failed at network access; the authorized network retry
completed. No credentials or persistent configuration changed.

| Window | Returned rows | Still absent | Recovered | Changed archived rows |
| --- | ---: | ---: | ---: | ---: |
| June 16-18 | 552 | 15 | 0 | 0 |
| June 21-24 | 780 | 85 | 0 | 0 |
| July 4-9 | 1148 | 287 | 0 | 0 |

Every returned OHLCV row equals its archived row. This supports that the stored
archive matches this current public API response in these windows. It does not
prove why the API omits the 387 grid timestamps, nor recover historical tick
order, loop timing or trailing-peak state. No forward filling or substitution.

Decision: stop repeated requests for the same windows. Exact historical replay
remains unsupported; do not delay all research on recovering unavailable ticks.
Proceed with existing archive/walk-forward research as a separate modeled
comparison, keeping runner-exit replay explicitly unverified. Before deployment
of the accepted fixes, inspect open positions and plan a labeled configuration
transition; do not rewrite prior evidence or reset the campaign implicitly.

Artifacts in .cbp_state/data/research/es_gap_refetch/20260908/:
- es_gap_refetch_20260908.json SHA256:
  440b5b1c27ecc50f24d4045f714241e24a60c04d2c10cdbe551693175891352e
- es_gap_refetch_20260908.py SHA256:
  c5a4d3be25b79dc6189b559c16d7f1fbe4139e4876871b77f8cff1ece362cd57

Verification: successful bounded network run plus mode=ro SQLite row comparison.
No production code changed; full suite not run. No campaign, archive or host
mutation. Acceptance state: ACCEPTED for this source-coverage observation only.
