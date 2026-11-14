# BTC+ETH forward experiment: pass/fail criteria (DRAFT v3.2 for the owner's signature, 2026-11-12)

Changes since draft v1, all made on 2026-11-12.

The owner's four clarifications (v2):
1. The Q2 drawdown and the 20% threshold are defined.
2. Decisions are split into on-time, reconstructed and missing.
3. Q1 is provisional until execution costs are measured.
4. Q3 is explicitly independent of Q1 and Q2.

The owner's three final checks (v3):
5. The Q2 extension is exactly 26 more weekly decisions.
6. Every cost observation and their range are reported, not only the average.
7. A missing decision is declared 48 hours after the close.

Three gaps Claude found in its own earlier drafts. Claude filled them as follows, for the owner to confirm or change
(v3):
8. The extension is for Q2 only. Q1's verdict is fixed at 26 weeks.
9. The 26 extension decisions are held to the same data-quality limits.
10. If Q2 is still untested after the extension, it counts as not passed. This follows "keep the rule only if… its
    worst drop is smaller than BTC's" in `second_stage_review_20261112/` section 6.

The owner's two wording corrections to v3 (v3.1):
11. With an extension, the 20% threshold is assessed over the whole 52-week window.
12. Measured execution cost is calculated separately for BTC and ETH and applied to each asset's own trades.

Claude's correction of its own omission (v3.2):
13. The reporting that AGENTS.md "Primary Objective Protection" requires for every result was missing from the
    earlier drafts. It is added as a reporting section and changes no pass/fail rule.

Bot relation: STANDALONE for questions 1 and 2 (tracker v2, research code); BOT_PAPER for question 3 once the bot
integration exists; runtime configuration not checked.

**Status: DRAFT.** Nothing here is in force until the owner approves it in writing. After approval, Claude records its
SHA-256 in the work log, and from then on it changes only through a dated amendment made before the data it affects.
Seeing interim results never changes it.

- Written by Claude from the second-stage review (`second_stage_review_20261112/` section 6) and the two outside
  reviews of 2026-11-12.
- It builds on the 2026-10-11 proposal in `strategy_decision_report_20261011.md` section 5.

## What is being tested
The frozen BTC+ETH 28-day trend rule, exactly as in tracker v2 (`paper_btc_eth_trend_v2_20261012/tracker.py`):
- L = 28, volatility target 50%, BTC and ETH;
- decided at the Sunday close, traded at the next day's open;
- 0.50% fee plus 0.05% slippage per side on every account.

No parameter, rule or cost assumption changes during the experiment.

**Three separate questions, each with its own pass/fail result.** None can be used to excuse another.

| Question | What it asks | Judged on |
|---|---|---|
| Q1 Strategy validity | After costs, does the rule do at least as well as a fixed BTC/ETH allocation? | Tracker v2: account `rule` against `mix_25_25_50` |
| Q2 Risk reduction | Does the rule have a smaller worst drop than holding BTC? | Tracker v2: `rule` against `hold_btc` |
| Q3 Implementation validity | Does the bot reproduce the research rule accurately and reliably? | The bot's paper account against tracker v2 (only once the integration is built) |

Q1 and Q2 use tracker v2, the reviewed research implementation, so a bot defect cannot hide or fake a strategy
result. Q3 is about the bot only, so a working bot cannot create the impression of an edge.

**Independence rule (clarification 4).**
- Q1 and Q2 never use bot data.
- No Q3 result can invalidate, rescue, extend or adjust Q1 or Q2. That covers any Q3 pass, failure, defect or
  restart.
- No Q1 or Q2 result changes the Q3 criteria.

**Approving these criteria does not approve code changes, bot deployment or real-money trading.** Each of those needs
its own approval.

## Window
- **Start:** the Sunday 2026-11-15 close. The first decision in the window is that day's decision. Window returns
  are measured from each account's daily close mark on 2026-11-15.
- **End:** the Sunday 2027-05-16 close mark, after 26 weekly decisions (the last on 2027-05-09).
- **One extension only, if Q2 is untested** (see Q2; checks 5 and 8):
  - The extension is exactly 26 more weekly decisions, from 2027-05-16 to 2027-11-07. The end moves to the Sunday
    2027-11-14 close mark, which is 26 weeks after 2027-05-16.
  - The start does not move. Q2 is judged over the whole 52 weeks from 2026-11-15, with the same criteria (correction
    11). Both the drawdown comparison and the 20% `hold_btc` threshold are measured over the entire original-plus-
    extension window, not over the 26 added weeks alone.
  - The extension is for Q2 only. Q1's verdict is fixed at the 2027-05-16 end and is final. Q1 over 52 weeks is
    reported but does not decide anything.
  - The extended Q2 result is final.
- Tracker v2 needs no new code for Q1 and Q2. The clock can start this Sunday, before any bot work.

## Q1 Strategy validity
- **PASS** if the window return of `rule` is at least the window return of `mix_25_25_50` (25% BTC, 25% ETH, 50%
  cash, weekly, same timing and costs), after costs.
- **FAIL** otherwise.
- **Execution cost (clarification 3):**
  - The 0.05% slippage assumption is not yet measured, so **every Q1 result is labelled "PROVISIONAL with respect to
    execution cost"** until reliable bid/ask observations exist.
  - **Reliable** means at least 8 weekly observations of the quoted bid and ask for each of BTC-USD and ETH-USD,
    taken at the Monday-open execution time.
  - **Measured cost per side is calculated per asset** (correction 12). For each asset it is the 0.50% fee plus that
    asset's own average half-spread. BTC and ETH are never given one shared cost. Each asset's cost is applied only to
    trades in that asset, on every account.
  - **Every observation is reported individually** (check 6): its date, the bid and ask for each asset, and the
    half-spread. The lowest and highest half-spreads are reported as well as the average. Eight observations are a
    minimum. They do not show that the average is representative.
  - Once that exists, Q1 is computed at both the assumed and the measured costs. **For each asset, the verdict uses
    the higher of the two.**
  - If no reliable measurement exists by the end, Q1 stays PROVISIONAL.
- **Reported, not deciding:** return against `hold_btc` and against holding ETH (from the same public daily prices),
  `rule_band10`, and Sharpe on weekly returns.

## Q2 Risk reduction
- **Drawdown, defined (clarification 1).** For an account, the window drawdown on day d is
  1 - mark(d) / (highest daily close mark from the window start, 2026-11-15, up to and including day d). The maximum
  drawdown is the largest such value in the window.
  - Peaks before the window start do not count. A fall that began before 2026-11-15 counts only from the 2026-11-15
    mark onwards.
  - Marks are tracker v2's daily close NAVs. For `hold_btc` these follow BTC's daily close after its entry costs, so
    the 20% threshold is BTC's own peak-to-trough decline within the window.
- **PASS** if the maximum drawdown of `rule` is smaller than that of `hold_btc`.
- **FAIL** if it is equal or larger.
- **UNTESTED** if `hold_btc`'s maximum drawdown is below 20% over the window in force: 26 weeks, or the full 52 weeks
  after an extension.
  - The market never fell far enough to test the claim, so the window extends once (see Window).
  - The 20% level is a chosen threshold, not one derived from data. It marks a fall large enough for trend-exiting to
    matter. In the backtests the rule's advantage came in falls far larger than that: BTC fell 53-84% against the
    rule's 32-52%.
- **Reported, not deciding:** drawdown against `mix_25_25_50`.

## Q3 Implementation validity (starts only after the integration is built and approved)
- **Before the first live-price week:** a trade-for-trade replay on history. The bot's target weights must match the
  research harness within 1 percentage point on every decision, and NAV within 0.5%.
- **Every week:** the bot's target weights must match tracker v2's within 1 percentage point. 100% of bot fills must
  carry the quoted bid/ask. Cash, positions and fees must reconcile to $0.01.
- **Failures:**
  - A silent missed decision is an immediate FAIL.
  - Recorded missed decisions with a cause are allowed up to 1 in the Q3 period; 2 or more is a FAIL.
- **On FAIL:** the bot account stops, is fixed, and Q3 restarts with a new 26-week clock. Q1 and Q2 are unaffected.
- **PASS** after 26 weeks with no FAIL.

## Data quality of tracker v2 (applies to Q1 and Q2; clarification 2, checks 7 and 9)
Each weekly decision in the window is one of three kinds.

Lateness is tracker v2's `recorded_lag_hours`: the hours from the end of the decision's UTC day (00:00 UTC on the
Monday) to the moment the record was written.

| Kind | Definition | What it counts as |
|---|---|---|
| On time | `recorded_lag_hours` of 24 or less | Valid operational evidence, and used in the account calculations |
| Reconstructed | More than 24 and up to 48 | Used in the account calculations; **not** evidence of reliable operation |
| Missing | Not recorded within 48 hours, for any reason, including a halt on an anomaly or data error | A data-quality failure, declared at the 48-hour point |

- Tracker v2's own `reconstructed` flag is true for anything over 24 hours, so it covers both reconstructed decisions
  and missing decisions that were recorded late. The kind is read from `recorded_lag_hours`. No code change is
  needed.
- A missing decision that tracker v2 later back-fills by the frozen rules keeps the ledgers continuous and is used in
  the calculations. It still counts as missing.
- **More than 3 reconstructed decisions, or any missing decision, makes Q1 and Q2 INVALID.** The window restarts
  after the reliability fix.
- In an extension, the same limits apply to the 26 added decisions. Breaking them makes the extended Q2 result
  INVALID.
- Reliability is reported separately as "on-time decisions: N of 26" (N of 52 with an extension). Missed or
  reconstructed weeks are never presented as on-time evidence.

## No interim decisions on performance
- Weekly reports may show values, but no early stop, extension or change is allowed for performance reasons.
- Early stopping is allowed only for implementation or reliability failures, as above.

## What happens at the end

| Result | Consequence |
|---|---|
| Q1 PASS and Q2 PASS | The candidate continues. The next step is the real-money minimums (`second_stage_review_20261112/` section 7) and the owner's capital decision. If Q1 is still PROVISIONAL on execution cost, the cost measurement comes first. **Passing does not authorise real money by itself** |
| Q1 PASS and Q2 UNTESTED (first window) | Extend Q2 once to 2027-11-14 with the same criteria (see Window) |
| Q1 FAIL, Q2 FAIL, or Q2 still UNTESTED after the extension | Active trading of the rule stops. The honest alternative is a fixed BTC/ETH-plus-cash allocation with no bot. CryptKeep strategy development stops unless the owner decides otherwise in writing |
| Q3 FAIL | The bot's results are not trusted until fixed and re-run. The Q1/Q2 verdict stands on tracker v2 |

## Reporting required by AGENTS.md "Primary Objective Protection" (v3.2)
These rules apply to every result in the repo. They are reported at the end and **do not change the Q1, Q2 or Q3
results**.
- **Classification.** The result is classified in POP's categories:
  - return edge (higher net return than holding BTC);
  - risk-adjusted edge (higher Sharpe than a fixed BTC/ETH/cash mix of similar drawdown);
  - diversification benefit;
  - risk reduction;
  - no demonstrated advantage.
- **Deflated Sharpe.** Any claimed advantage must also pass the deflated Sharpe at the trial count in the ledger. A
  Q1 or Q2 PASS is not by itself a claimed advantage.
- **Cost levels.**
  - Results are also reported at 0.90% per side plus the same 0.05% slippage, computed from the same daily prices,
    and at the confirmed account fee tier if one is confirmed by the end.
  - The report states at which cost levels the result holds.
  - Bid/ask readings are quotes, not measured fills. Under POP the results stay labelled exploratory until real fills
    have been measured.
- **Per symbol and combined.** The BTC and ETH legs are reported separately as well as the combined account.

## Known limits, accepted in advance
- **Not statistical proof.** 26 weekly decisions cannot establish statistical significance. This is an operational
  and directional test that can stop a bad idea. It cannot prove a durable edge.
- **Quiet markets look bad.** The rule's history depends on a few large trends: 5 of 108 trades made 82% of its net
  trade profit (`second_stage_review_20261112/` section 2). A window without a strong trend may fail Q1 even if the
  rule works. That is accepted, because the criterion was fixed before the data.
- **Approximate execution.** Tracker v2's execution is modelled at the next public daily open, not an observed fill.

## To approve
The owner replies "approve the criteria" (or states changes). Claude then:
1. records the file's SHA-256 and the approval in the work log and `PROJECT_STATE.md`;
2. renames DRAFT to FROZEN in this file, with the approval date.

No code changes are needed for Q1 and Q2.
