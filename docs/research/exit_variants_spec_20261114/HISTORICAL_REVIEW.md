# Independent historical comparison review

Bot relation: BOT_RULES; runtime configuration not checked.
Reviewer: Nash, separate agent `01a1cee8-b4ec-7343-9992-b771df07aba1`.
Recorded by Codex from actual independent responses, not self-certification.

## Pre-run review

2026-11-14T17:05:18Z: ACCEPTED_WITH_RISK for the pre-run source/synthetic gate, after the reviewer blocked the
initial ledger comparison for missing side, quantity and individual fee checks (O168). Independent pre-correction
probe accepted a ledger containing wrong sides and quantities/fees of999. Revised gate rejects each mismatch.
Prior nine synthetic tests passed0.31s; separate six correction cases passed0.21s. Those review runs blocked
database/network/subprocess access and used a90second alarm. Author95-case consolidation was not repeated.

Reviewed hashes before the historical invocation:

```text
1a92a0ba37862fc0cbf4da4d636d7667419c0ae82a6a98d002f8529bafaaab0f  replay_contract.json
fae0952ec51e28e48dad8e0a2a74a7d33b2f4f912af6c140c57a2e77355c182e  replay_exit_variants.py
2f56b2c99c69b6389d5d41e4599f48663112de0657277f43cdcce3895ade3718  legacy_exit_parity_replay.py
c616f25c028a57c75a55bbf05fcae4a3a152b983bf2290496cc01ea2a796544f  tests/test_exit_variants_replay.py
```

## Result review

2026-11-14T17:12:59Z: ACCEPTED_WITH_RISK for retained historical comparison/reporting. No material accounting
or integrity blocker. SHOWN independently by the reviewer:

- All28 pins, original output seals, five frozen prefixes and15 saved S ledgers verified.
- All120 cases reconciled against5,430 trade-cost CSV rows: quantities, fees, cash, close-marked drawdown and
  exposure bounds. Four selected R price traces matched; the120-row metrics export matched exactly.
- All41 prior coverage data rows unchanged;30 appended rows INCONCLUSIVE. Author additionally verified original
  CSV bytes preserved exactly after restoring the original mixed line endings; only appended rows are new.
- Economic conclusion supported: all60 unblocked cases lost after stated costs. S worsened each strategy's
  arithmetic five-sleeve total; R improved slightly but remained negative. The positive default ETH/EMA exception
  is **S-only**, clarified in the final report at the reviewer's request.
- Thirty descriptive opportunities are not a resolved project-wide DSR count.

Accepted result hashes:

```text
1f4a5ff2052ebc614b6b8582ea502adcb81e97288eda6b5c01a743b65917e967  historical_20261114T1706Z/exit_variants_result.json
2810482aebd3fd4a56972dd859cd2796c32d10b449a357ba547a603d8af97933  historical_20261114T1706Z/trades.csv
```

No strategy-signal replay was repeated. Historical parity relies on the pinned reviewed harness and saved gates.
This supports closing the retained source/offline comparison, not promotion, forward edge, runtime equivalence
or activation. Review did not access private accounts or current operating configuration and grants no further
operations. The source and result files were not changed after review; only this receipt/status wording and the
explicit S-only clarification were recorded. Original historical/source acceptance artifacts remain preserved.

What do I know that could change the owner's decision that I have not yet said? These losses do not disprove
every symbol, regime or alternative exit hypothesis, but provide no basis to promote these variants.
