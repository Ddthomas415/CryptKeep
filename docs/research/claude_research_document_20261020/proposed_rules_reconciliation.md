# Proposed research rules in Claude's research document: reconciliation

Bot relation: STANDALONE; runtime configuration not checked.

Status of every rule below: **PROPOSED, not adopted.** The document calls its first list "proposed for the brief"
(`research_document_rev129.md`, section 8). No record of owner approval of any of these rules was found in the document.
None of them appears in `AGENTS.md` or `docs/research/RESEARCH_BRIEF.md`. Adopting any of them needs the owner's
approval of the exact wording, then an edit to the brief.

Rule wording is copied verbatim from the document. The ID (R01 to R30) is added here for reference only. Lead IDs
(T07-1 and so on) refer to scout reports in `docs/research/research_scout/reports/`.

**Search method (2026-11-05, Claude):**
- A case-insensitive keyword pattern per rule, run over `AGENTS.md`, `docs/research/RESEARCH_BRIEF.md` and
  `docs/PROJECT_STATE.md`.
- The same pattern run over `docs/research/**/*.md`, excluding scout reports and the conversation, on-chain and
  integrity audits.
- A keyword hit is not proof that an equivalent rule exists, and a miss does not prove that no differently worded rule
  exists. Only the hits marked "checked" were read.
- `PROJECT_STATE.md` lines 650, 664 and 665 are rows of the 2026-11-05 "Undecided ideas" table, not adoptions.
- The `PROJECT_STATE.md` line 45 hit for R22 is a false match ("design test").

## Rules proposed in section 8 (2026-10-21/22)

| ID | Proposed rule (verbatim) | Lead | Canonical files | Elsewhere |
|---|---|---|---|---|
| R01 | Any model-based signal needs a minimum forward paper period before promotion (T07-1: 23 of 24 ML methods were profitable in backtest, 2 of 8 in paper trading). | T07-1 | None | None |
| R02 | Every preregistration includes a planted-leak control that the integrity checks must flag (T07-3). | T07-3 | None | Checked: applied in one draft only, `ctrend_oos_20261022/PREREGISTRATION_DRAFT.md` lines 190-191 (CTREND-OOS, on hold) |
| R03 | LLM-derived signals are evaluated only on data after the model's training cutoff (T06-8, T07-5). | T06-8, T07-5 | None | None |
| R04 | Known Kaggle leakage cases go into the integrity checklist (T07-9). | T07-9 | None | None |
| R05 | Log the number of strategy legs combined, not only the number of trials (T09-5). | T09-5 | None | None |
| R06 | Treat light post-hoc tweaking as roughly doubling the apparent Sharpe (T09-6). | T09-6 | None | None |
| R07 | Any fill-model stress case includes altcoin depth at half its normal level, no fills while the venue is halted or cancel-only, and partial fills at the Price Protection Point, with a stated model turning depth into cost (T11-8; half is a chosen stress level, not a measured one). | T11-8 | None | None |
| R08 | Liquidation feeds are lower bounds (Binance pushes at most one liquidation per symbol per second; ADL never appears), so any liquidation input is an event flag, not a summed volume (T00-8). | T00-8 | None | None |
| R09 | Funding rates are compared per stated interval only; never annualise altcoin funding at 3 prints a day; applying today's interval to past prints is look-ahead (desk check T00-1). | T00-1 | None | Checked: related, not equivalent. `okx_funding_contract_20261029.md` line 40 (Codex fix 3) does not treat a gap as a verified funding interval; it states no annualisation rule |
| R10 | Any on-chain flow hypothesis names point-in-time data or a dated label snapshot in its pre-registration, because vendors revise exchange-flow history (CryptoQuant re-clusters weekly; Glassnode keeps computation times only from 2024-25) (T01-1). | T01-1 | None | None |
| R11 | Any volatility-forecast test also reports, pre-declared, the turnover and after-cost result of the frozen candidate under each estimator; better forecasts mainly cut turnover rather than raise Sharpe (T03-4). | T03-4 | None | None |

## Rules proposed in section 16 (2026-10-24)

| ID | Proposed rule (verbatim) | Lead | Canonical files | Elsewhere |
|---|---|---|---|---|
| R12 | Rule: no modelled market-order fill while a product is in auction or limit-only, and a held coin turning limit-only is a forced-exit or higher-cost event. | T05-1 | Checked, partial: `PROJECT_STATE.md` line 501 (engineering item 5, ED-002) requires a "held-coin rule for limit-only or delisting announcements" for that comparison only | Codex fix 2 code work: `coinbase_mode_gate_20261028.md`, `exit_deferral_20261028.md` (not read for equivalence) |
| R13 | Pre-state a tail-robust check (median or trimmed-mean sign test), reported only, beside mean tests; for CTREND-OOS r3 and later studies. | T04-6 | None | None |
| R14 | Rule: one-off promotional fees never enter backtest costs. (The document also asks the owner to check the promotion's terms in the app.) | T05-3 | None | 1 keyword hit, not read: `fc01_gate2_eligibility_count_20261004.md` |

## Rules proposed in section 17 (2026-10-27)

| ID | Proposed rule (verbatim) | Lead | Canonical files | Elsewhere |
|---|---|---|---|---|
| R15 | Preregistrations carry a leakage checklist: point-in-time membership and listing dates, token migrations measured rather than assumed (e.g. TOMO to VIC, GAL to G), silent zero-fills and empty-but-successful API responses (T07-3). | T07-3 | None | 6 keyword hits on "zero-fill"/"migration" in unrelated reviews, not read for equivalence |
| R16 | An ML classifier must beat a volatility-only baseline (T07-4). | T07-4 | None | None |
| R17 | Listing-event logs record the announcement time and its source, not only the first trade (T08-10). | T08-10 | None | None |
| R18 | Preregistrations state the benchmark correlation and the minimum detectable effect (T09-3). | T09-3 | None | 2 keyword hits, not read: `information_edge_assessment_20261018.md`, `faster_context_hypothesis_draft_20261004.md` |
| R19 | Preregistration folders keep an ERRATA file, and checksums are committed before any data access (T09-8). | T09-8 | None | None |
| R20 | Event studies on correlated coins use clustered or bootstrap inference across simultaneous events (T11-7). | T11-7 | None | 2 keyword hits, not read: `e01_paper_evidence_audit_20261002.md`, `liquidation_data_feasibility_20261012.md` |
| R21 | Funding normalisation must know the venue's formula version: OKX divides sub-8-hour rates by 8/N from 2026-06-01, Bitget from 2025-09-22 (T00-1; for Codex fix 3). | T00-1 | None | Checked: `okx_funding_contract_20261029.md` line 94 says no formula version is adopted there |
| R22 | Open-interest studies use one venue, an OI-to-volume sanity check and no vendor aggregates (T00-5). | T00-5 | None | None |
| R23 | On-chain features fix and archive a dated label snapshot and state their specification choices before results are seen (T01-4). | T01-4 | None | None |

## Rules proposed in sections 20 to 26 (2026-10-28 to 2026-10-30)

| ID | Proposed rule (verbatim, without the supporting evidence that follows it in the document) | Lead | Canonical files | Elsewhere |
|---|---|---|---|---|
| R24 | Treat a Coinbase delisting announcement or a limit-only switch as an exit or avoid trigger, about 30 days before suspension, and never label a regional restriction (such as Binance Brazil) as a global delisting. | T02-2 | Checked, partial: `PROJECT_STATE.md` line 501 (ED-002 held-coin rule, that comparison only) | 13 keyword hits on "delisting", not read for equivalence |
| R25 | If the candidate's volatility scaling or Module A's volatility estimate is ever re-tested, score each estimate on after-cost turnover and drawdown, not on forecast accuracy alone, and include a range-based (Garman-Klass) EWMA as a declared arm. | T03-1, T03-4 | None | None |
| R26 | Use daily-price spread estimators (Corwin-Schultz, EDGE) only to rank coins by cost, never as a cost level, and do not trust volume-based measures for smaller coins. | T05-5 | None | None |
| R27 | Treat news sentiment as following prices unless shown otherwise. Any future news-sentiment pre-registration must first test whether prices predict sentiment. | T06-2 | None | None |
| R28 | No new question may be scored on the CMC trending log unless it is registered before the log's window opens on Nov 10; afterwards it would be post-hoc. | T06-3 | None | None. **Time-sensitive: the window opens 2026-11-10.** The document recommended against adding the scout's suggested question. |
| R29 | Any future test of a forecasting model must also run it on placebo data where no skill can exist (a driftless random walk, shuffled days, shuffled blocks) and must fail there, and must compare against a random walk with the Clark-West test, which is built for nested models. | T07-1, T07-4 | None | 1 keyword hit, not read: `unlock_data_feasibility_20261020.md` |
| R30 | In any forward listing study (FRESH-1, if approved), check each coin's first-bar time against the announced trading start. | T08-4 | None | None |

## Counts

- 30 proposed rules.
- 0 in `AGENTS.md` or `RESEARCH_BRIEF.md`.
- 2 partly covered for one study only: R12 and R24, through the ED-002 held-coin rule in `PROJECT_STATE.md` engineering item 5.
- 1 applied in one unfrozen draft: R02, in CTREND-OOS.
- 2 with related, non-equivalent Codex fix 3 text: R09 and R21.
- The document's own running total was "31 rule leads". Several leads feed one rule (for example T07-1 and T07-4 feed R29), so the leads do not map one-to-one onto rules.
