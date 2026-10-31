# Backtest, data, operations and test integrity (capital-protection audit, stage 4)

Bot relation: not a strategy result (audit of the research process, data, operations and tests).
Research item 1 in `docs/PROJECT_STATE.md`, stage 4 (owner-approved 2026-10-31). Claude. Read-only. **Self-checked;
Codex to verify.** Each area had one defined check; the audit stops here.
Searches for earlier work: `integrity_audit_20261015/` (look-ahead perturbations, blind re-implementations),
`universe25_explainer_20261030/`, `breakout_economic_dissection_2026_09_23.md` (archive gaps), the trial ledger, the
owner's process checks of 2026-10-31, and the scheduled-task list read on 2026-10-31.

| ID | Area | Check and result | Evidence | Severity | Owner | Disposition |
|---|---|---|---|---|---|---|
| S4-01 | Look-ahead | The research engine computes signals on completed candles and fills at the next open; the 2026-10-15 integrity audit ran look-ahead perturbations for E7-E10 (outputs archived, not re-checked here). The bot runner uses the still-forming candle (D-4), which no backtest can reproduce. | SHOWN `next_open_research.py` `run_frozen_segment`; CLAIMED `integrity_audit_20261015/vm_scratch/perturbation_results/` | LOW | - | Caveat C-06 |
| S4-02 | Missing candles | The research engine refuses gaps (`incomplete_or_unordered_bar_grid`, lines 36-37), so they are not silently filled. Standalone studies handle gaps their own way: E6 traded at stale prices (H-02); the Coinbase 5-minute archive had 14% gaps (2026-09-23). Not checked study by study. | SHOWN (engine); CLAIMED (others) | LOW | - | Note |
| S4-03 | Survivorship | The 25-symbol list is survivor-selected; E10 bias unmeasured; the altcoin event studies used Binance data including delisted pairs. | CLAIMED from the cited reports | MEDIUM | Owner | Caveat C-09 |
| S4-04 | Redenominations | MATIC to POL is handled in the 25-symbol analysis (excluded, flagged); no general rule for token migrations was found. | SHOWN (universe README); search | LOW | Codex | Note |
| S4-05 | Data collection | The only data collector runs on the server (since 2026-10-24). A cadence checker exists (`scripts/check_edge_cadence.py`, read-only) but no scheduled run of it was found (the owner's server check listed no matching user timers; system-level timers were not listed). A silent stop is not detected automatically; one stop was missed after a laptop restart. | SHOWN (script); owner's check | MEDIUM | Codex | Propose: schedule the cadence check with an alert |
| S4-06 | Scheduled tasks | CMC daily log last ran 2026-10-30 (succeeded); research scout 2026-10-30 (succeeded); weekly BTC+ETH paper test 2026-10-26 (succeeded); weekly status first runs 2026-11-02. Tracker v2 is a Codex automation (delivery UNVERIFIED in the brief). | SHOWN (scheduled-task list, 2026-10-31) | LOW | - | Note |
| S4-07 | Backups | **The last 12 days of work exist only on the laptop.** HEAD is 389020130 (2026-10-19) on the local branch `checkpoint/2026-10-19`; GitHub `origin/master` was last updated 2026-10-01 (local is 4 commits ahead); 547 uncommitted entries, including POP, PROJECT_STATE.md, every audit and the work log. | SHOWN (`git status`, `git log`) | HIGH | Owner | Decision 1 (commit and backup) is now urgent |
| S4-08 | Stopping all trading | MacBook: kill switch armed, system guard HALTED. Server: no kill-switch file; the two paper jobs (started 2026-09-16 as a separate user) are not systemd services and stop only by ending the processes. No single stop covers both machines. | Owner's checks | LOW now (paper only); MEDIUM before live | Codex | Note for any live design |
| S4-09 | Quality of Codex's tests | 1,136 test files, 5,750 test functions; 29 skip markers (6 static, 23 conditional), 32 slow tests; no test file deleted since 2026-08-01 and none deleted in the working tree. The 169 tests for the trading path pass while D-1 and CP-09 exist: gaps in coverage, not removed tests. Weakened assertions were not checked. | SHOWN (search, git) | MEDIUM | Codex | Failing-test rule (AGENTS.md, 2026-10-31) |
| S4-10 | Do the rules work? | Too early: two days. POP is now 126 lines of AGENTS.md and PROJECT_STATE.md 203 lines, all written in two days. Deterministic parts: the weekly status checks (first run 2026-11-02), the failing-test rule and the "Bot relation" line. Measure: the register. If agent-caught omissions stay at 0 for several weeks, the rules are not working and should be cut back to the deterministic checks. | SHOWN (line counts, register) | - | Owner | Review after four weekly statuses |

**What could overturn this:** system-level timers on the server (not listed); backups outside git (for example Time
Machine) that this check cannot see; studies whose gap handling was not checked one by one.
