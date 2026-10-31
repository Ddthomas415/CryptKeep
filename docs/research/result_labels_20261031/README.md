# Which results describe the bot? (capital-protection audit, stage 2)

Research item 1 in `docs/PROJECT_STATE.md`, stage 2 (owner-approved 2026-10-31). Claude. Read-only. **Self-checked;
Codex to verify.** Started before Codex checked stage 1 because it does not depend on stage 1 and the owner asked
agents not to stall on each other.

**What was labelled:** the 42 entries of the trial ledger (`trial_ledger_reconciliation_20261015/trial_inventory.csv`)
and 8 results recorded after or outside it (`result_labels.csv`, 50 rows). `label_results.py` reproduces the CSV:
it searches each result's scripts for the bot's code (signal functions, research engines, the runner's exit stack);
17 ledger entries and the 8 added results are labelled by hand from their reports, and the evidence column says which. Not inspected: the
content of every report; the ledger's own completeness (its 747 is a floor, not a verified count).

| Label | Meaning | Entries | Configurations (numeric counts only) |
|---|---|---:|---:|
| STANDALONE | Own simulation code; never implemented in the bot | 30 | 743 (+3 unresolved) |
| SIGNAL_ONLY | The bot's strategy signals, without its entry rule and exit stack | 5 | 15 (+1 unresolved) |
| BOT_RULES | The runner's entry rule and exit stack replayed | 3 | 63 |
| BOT_PAPER | An actual paper run through the bot | 4 | 2 (+2 unresolved) |
| NO_RESULT | Not run, blocked, withdrawn, duplicate, data collection, not a trading test | 8 | 0 |

## What this means (SHOWN unless marked)
- **Almost all research tested rules the bot cannot run.** 30 of 42 results with a trading outcome, about 743
  configurations, are STANDALONE. Their verdicts stand on their own assumptions, but none says what the bot would do,
  and none could be traded without new code and its own parity check.
- **The project's only CANDIDATE (BTC/ETH 28-day trend, volatility-scaled) is STANDALONE.** It and its forward
  tracker (`paper_btc_eth_trend_v2_20261012/tracker.py`) use no bot code; a search of `services/` and `scripts/` by
  its names found no implementation. Trading it with the bot would need new code first. (Name search; an
  implementation under another name is possible but none was found.)
- **Only one result checked the bot's actual runtime configuration:** the exit-parity audit of 2026-10-31. The two
  earlier runner-rule replays (ES exit matrix 2026-10-07, horizon scan 2026-10-08) used code-default or stated exits
  without checking the configuration: INCOMPLETE under AGENTS.md "Configuration inspection".
- **The four bot paper runs are small:** ES trial zero orders; ES v1 none profitable; Coinbase EMA campaign 8 trades,
  -$2.32; breakout campaign failed economically (CLAIMED from the ledger's recorded verdicts).
- **Three measures, first question** ("does the bot execute what the research says it executes?"): for STANDALONE
  results the bot does not execute them at all; for SIGNAL_ONLY results it executes something else; only the BOT_RULES
  and BOT_PAPER rows describe the bot, and none of them shows an advantage.

**Open questions that could change this:** an implementation of the candidate under another name; rows labelled
by hand from reports rather than code (25 rows); ledger entries with unresolved counts.
