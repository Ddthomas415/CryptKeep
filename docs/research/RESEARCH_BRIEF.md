# CryptKeep research brief: read before any strategy or edge work

Last updated 2026-10-16: corrected reused-history, universe, scheduling and operational-status statements. This brief is a map. The linked files are the evidence, and they win if the two disagree. Original experiments and registered verdicts are unchanged.

2026-10-18 supplement: the user explicitly requested separate low-unit-price and
lower-cap top-100 tests, rather than another BTC/ETH test. See
`low_value_top100_20261018/RESULTS_V2.md`: three exploratory CMC-reference
screens, no BTC/ETH purchases, 383 historical asset IDs across 100 four-week
cycles after explicit instrument classification repair. V1 was incomplete
because truncated tags admitted stable/wrapped instruments; all v1 artifacts
and review remain preserved. Under-USD1 and ranks51..100 mean net lower bounds
+USD28.43/+USD16.11 per independent USD1,000 cycle; new entrants +USD129.35 point estimate, heavily
concentrated, median -USD1.25 and worst -USD528.27. All paired advantage
intervals cross zero; no executable edge established. Missing exits stay unknown,
not fabricated fills. Basket evidence does not change individual-symbol status,
the 25-symbol mandate, old FAILs, or operational authorization. This direct user
request authorizes the bounded screen separately from backend restoration;
restoration remains incomplete and no services were touched.

Labels follow AGENTS.md: SHOWN (evidence in repo), CLAIMED, UNVERIFIED.

## 0. Scope (read first)
- **CryptKeep is multi-symbol.** See `MULTI_SYMBOL_MANDATE.md`. Project scope remains the 25 symbols in `config/candidate_universe.yaml`; this is not a current or historical trading-eligibility list. The mandate's October15 check records 24 Coinbase USD products, MATIC-USD delisted with POL-USD as successor, and XRP's historical suspension. No automatic substitution or scope change follows.
- **The findings below are research evidence for specific symbols and conditions. They are not the project's scope.**
- **Coverage (2026-10-15, after E10; `research/symbol_coverage.csv`):**
  - The 10 Coinbase core pairs have each had a standalone slow-trend test. Results:
    - CANDIDATE vs hold: ETH, AVAX, DOT;
    - INCONCLUSIVE: BTC, SOL, DOGE, ADA;
    - REJECTED under tested conditions: LTC, LINK, XRP.
  - The equal-weight 10-symbol trend portfolio was rejected vs BTC+ETH.
  - 15 symbols (BNB and the tier-2 and watchlist symbols) remain UNTESTED.

## 1. Bottom line
- **No demonstrated dependable trading income or validated profitability** in the reviewed evidence. This does not reject all possible edges or the untested universe.
  - **Candidate:** the BTC+ETH 28-day volatility-scaled trend rule has scoped historical risk-reduction evidence at the tested costs. Its registered 1.2% stress rejection stands; lower-cost results remain exploratory, not confirmation.
  - **Return:** it has no proven return advantage over BTC, and it depends on costs.
- **Literature context:** `crypto_trading_edges_survey_20261013.md` is a research survey, not proof that only one family can survive costs. Existing negative findings apply to their tested rules, assets, periods and assumptions.
- **Further work:**
  - cost reduction and risk engineering around the candidate;
  - restore the existing research/explanation path and reproducible delivery before new experiments; E10 is completed, not queued to run again;
  - prospective, pre-registered comparisons across justified subsets of the wider universe, after data, sizing, cost and evaluation contracts are frozen;
  - no unregistered signal hunting.

## 2. Costs: confirm before trusting any backtest
- **Account fee tier:** 0.25% maker / 0.50% taker per side. SHOWN for the account-level SPOT tier via an authenticated read on 2026-10-08 (`research/coinbase_fee_observation_20261008.json`). Product-specific fees are UNVERIFIED.
- **Conflicting secondary sources:**
  - entry tier 0.40% / 0.60%;
  - a reported Sep 2026 US change to 0.50% / 0.90%.
  - Both are UNVERIFIED. They do not override the dated account-level observation. BTC-USD/ETH-USD product-specific all-in rates and historical applicability remain UNVERIFIED; no new credential or account action is authorized by this brief. See `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md` for the preserved observation and remaining evidence requirements.
- **Round trip at 0.25/0.50:** 0.50% (maker/maker) to 1.00% (taker/taker), plus spread.
  - Weekly full turnover costs about 26-52%/yr.
  - Monthly full turnover costs about 6-12%/yr.
- **Never use the simple Coinbase buy/sell flow** (0.5-2% spread built in). Use Advanced only.
- **Limit fills are adversely selected:** easy fills tend to be followed by adverse moves. A backtest must model unfilled orders and post-fill drift.
- **Server:** about $20/month. This is an operator estimate (CLAIMED); the invoice is not seen. Workloads: `server_workload_inventory_20261011.md`.
- **Tax:** short-term gains are taxed as ordinary income. Brokers have issued Form 1099-DA since 2025.

## 3. What the evidence says (details and sources: `crypto_trading_edges_survey_20261013.md`)
| Scoped historical candidates / hypotheses | Access or execution feasibility unresolved | Rejected or inconclusive under tested conditions |
|---|---|---|
| BTC/ETH slow trend and volatility scaling; E10 also tested 10 core symbols, with scoped results in the registry | Futures carry / basis; existing modeled feasibility is not verified access, fees or liquidation safety | Cross-sectional momentum, size, reversal as tested (E6 basket, leader pullback; scoped in the registry) |
| Volatility scaling and rebalance bands have scoped historical results; E9's registered FAIL stands | Selling options (variance premium) | Calendar/overnight/intraday rejections apply only to the tested rules, assets, periods and costs |
| Avoidance filters are research hypotheses, not established profitable rules | Arbitrage, order flow, MEV, liquidity-pool provision | Listing/event results are limited to the reviewed models and data |
| Funding/basis crash brake: tested 2026-10-13, FAILED as this specified overlay | | Survey cautions about on-chain/sentiment signals are literature context, not exhaustive repository tests or rejection of those families |

## 4. Project results to date
| Idea | Status | Evidence |
|---|---|---|
| BTC+ETH 28d trend, vol-scaled | **CANDIDATE** | `btc_eth_corrected_comparison_20261012/`, `dsr_btc_eth_trend_20261011/`, `stress_fee050_exploratory_20261011/` (exploratory), `edge_classification_btc_eth_20261011.md` |
| Same rule, registered stress test at 1.2% | REJECT (stands) | `research/research_corrections_20261009/stress_corrected_v1.json` |
| Altcoin event rules (~448 configs), breakout, recovery/regime, short-hold, CMC proxy, dynamic Coinbase, hybrid | Rejected or inconclusive | `consolidated_economic_summary_20261010.md`, `strategy_decision_report_20261011.md` |
| Top-gainer pullback dip-buying (8 variants) | FAIL: all lost before and after costs | `leader_pullback_study_20261012.md`, `leader_target_test_20261012.md` |
| Dip-recovery screen | Withdrawn (used future information) | `dip_recovery_screen_20261012.md` |
| Weekly altcoin cross-sectional momentum | FAIL; simulator defect annotated | `xs_momentum_20261012/` |
| Funding-rate crash brake (E7) on the candidate | FAIL on registered condition 1: D drawdown unchanged; H drawdown modestly lower, but ending value lower in every period. Original verdict stands; redundancy is the report's scoped interpretation | `crash_brake_20261013/` |
| Composite v1: 20/50/100/200-day trend ensemble + 10-pt rebalance band (E8) | FAIL: better in 2017-23, much worse in the reused 2024-26 historical segment (Sharpe 0.45 vs 0.87); the original result label is preserved | `composite_v1_20261013/` |
| Band 0.10 alone on the unchanged candidate (E9) | FAIL on the registered turnover criterion (0.90x, needed ≤ 0.75x); otherwise better Sharpe and ending value in D and H at both fees and half the trades. Criterion mis-specified; resolve with FORWARD tracking, not a re-test | `candidate_band_20261013/` |
| Slow-trend portfolio across 10 core pairs, equal 1/N (E10) | FAIL vs BTC+ETH incumbent (Sharpe 1.20 vs 1.46 in D, 0.51 vs 0.88 in H). Standalone: trend cut drawdowns on every symbol; per-symbol statuses in the registry | `multisymbol_trend_20261015/` |
| Maker vs taker execution | Draft v3 correction, NOT frozen; operator chose delayed execution plus arrival-book observation. Account-tier evidence exists; product fees, timestamp/coverage and inference contracts remain unresolved. No collection or scoring authorization follows | `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md` |
| CMC trending | Collecting; primary analysis no earlier than 2027-02-15 | `cmc_trending_log/` |
| Forward tracker v2 | Separate research-only Codex schedule recorded ACTIVE; first delivery October18 20:47 New York remains UNVERIFIED. README records 27 tests and independent review; this brief does not rerun them. v1 artifacts/schedule are preserved, not independent evidence | `paper_btc_eth_trend_v2_20261012/README.md` |
| Corrected ES prospective trial | Fixed endpoint completed; saved host report independently ACCEPTED_WITH_RISK. Zero orders/fills/positions, zero paper trading PnL; efficacy INCOMPLETE, no extension or promotion | `../checkpoints/es_prospective_endpoint_result_2026_10_16.md` |

Selection accounting: pass2 records a convention-specific floor of 747 configurations (577+113+57), not a verified complete selection count or effective N. Its CSV has six exact family counts, two lower bounds and one unknown; symbol pooling and selection exposure still need reconciliation. The older 576 and effective-N estimates are historical, not validated current inputs. See `trial_ledger_reconciliation_20261015/pass2_findings_20261015.md` and `discovery_engine_proposal_review_20261016.md`. No DSR is recomputed from this correction.

## 4a. Operational evidence is separate from research results
- **SHOWN in the October16 consolidated audit:** the documented local `127.0.0.1:8002/healthz` route refused connection. Older successful disposable integration tests do not establish current service availability. Other endpoints, durable operation and external alert delivery remain UNVERIFIED unless supported by a newer receipt.
- **Recorded point-in-time collector status:** the audit saw existing paper/context collector PIDs and fresh status files. This is not continuous health or approval to restart them.
- **Scheduling:** the v2 tracker schedule above is recorded configuration, not proof of its first unattended run. It is Sunday20:47 New York (UTC changes with daylight saving), not a fixed Monday UTC schedule. Do not create a duplicate job.
- **Test baseline:** the recorded broad run was 4,679 passed, 2 failed, 76 skipped and 1 collection error. A later isolated proxy test passed; that does not make the broad suite green. See `consolidated_review_20261016.md` for commands and limits.
- The current authorized repair is local source/docs/tests and packaging only. No service, Docker, server, account, credential, schedule or trading-operation change is implied.

## 5. Research rules (non-negotiable)
1. **Write the rules down before seeing data or results.** Amendments must be dated, made before running, and never replace the original.
2. **Count every variant tried.** Report all of them, losers included. Correct for selection: DSR at realistic N, with sensitivity.
3. **Use real costs:** fee + slippage on every trade, for every strategy AND every benchmark. Report results at both the confirmed tier and a higher-cost tier.
4. **No price filling.** A missing candle is not a tradable price. Failed downloads are recorded as failures, never as "no trading".
5. **Execution:** decide at a close, trade at the next open (or model limit fills honestly). Executions are labelled modelled unless they are actually observed.
6. **Benchmarks:** hold BTC, a fixed BTC/ETH/cash mix at comparable exposure, and cash. Label mixes fully (e.g. 25/25/50 means 50% cash).
7. **Judge new ingredients against the current candidate,** not just against BTC.
8. **Previously examined history is not untouched holdout data.** In particular 2024-26 was reused in candidate selection and later studies. Preserve original D/H labels as historical artifact labels, but use those periods only for exploration, reproduction or sensitivity. Genuine confirmation requires a dated frozen protocol before unseen observations; do not backdate activation or retune after inspection.
9. **Preserve originals and registered verdicts.** Exploratory results are labelled exploratory. No profitability claims; DSR is not a profit probability.
10. **Universe and survivorship:**
    - Survivorship bias is large (about 53% of tracked tokens have failed). Use datasets that include delisted coins, and say what is still missing.
    - Every symbol tested counts as a trial.
    - Every negative result is scoped to its symbols and conditions in `research/symbol_coverage.csv`.

## 6. Accepted next steps (2026-10-16)
1. Correct this active brief without rewriting frozen registrations or results.
2. Diagnose and repair the existing research/explanation source path; distinguish local fixture proof, endpoint availability and sustained operation. Operational changes require separate authorization.
3. Triage is complete for the bounded source/fixture scope, not for whole-suite integration: native Git/audit isolation repaired (8 controlled cases), proxy failure traced to sandbox bind denial, and article-body collection verified in a disposable dependency overlay (6 cases within a 42-test selection). Root `.venv` still lacks `bs4`; retain the original 4,679/2/76/1 broad result. See `research_path_repair_handoff_20261016.md`. Do not repeat this triage as an unstarted task.
4. Packaging is complete for the independently reviewed V3 slice: exactly 39 allowlisted files, hashes, preserved originals and a clean extracted 33-test receipt. October17 read-only verification confirms every archived/current file still matches. This reproduces independent per-symbol/arm behavior, not a shared-capital portfolio. Preserve the 25-symbol mandate, raw archives and verdicts; do not repackage or rerun failed backtests without new contradictory evidence.
5. Only after that path is usable, propose one prospectively registered comparison with universe, missingness, carry-forward sizing/cash, costs, benchmarks and acceptance criteria frozen before outcomes. No experiment is authorized by this brief.

Completed work is not a new queue: E7/E8/E9/E10 retain their registered FAIL results; tracker v2 and its band10 account already have saved code/review/schedule records. Maker/taker draft v3 still needs its remaining evidence and independent contract review before freeze, not a repetition of earlier unqualified arrival assumptions.

### Restoration checkpoint, October17 New York

SHOWN: a fresh paired selected-metadata capture at October18 03:22:50 UTC
(October17 23:22:50 New York) found the same seven pinned research containers
exited, zero restarts, restart policy `no`; both retained observations match.
Four source archives (241 per-application records) and 11 previously reviewed
artifact/source hashes still match current bytes. The refreshed four-service
recipe is review-only and is refused by the executable plan loader. The new
30-test collector/recipe selection passed; it is not a new full-suite run.

Installation and genuine explanation delivery remain INCOMPLETE. Outstanding
evidence includes actual mounted import/dependency behavior and strict registry
isolation; `build --pull=false --network=none` does not enforce the latter.
No accepted executable installation manifest was fabricated. No build, replacement,
startup, credential-value access or explanation request occurred in this batch.
See `../checkpoints/companion_batch_closeout_20261017.md` for the consolidated
evidence and operational boundaries. New comparison registration remains gated
on a usable explanation path, not on repeating already completed packaging.

Later October17 native builder check: the reviewed bare-ID parent correction
passed one present-parent and one deliberately missing-parent request. Seven
selected original container snapshots stayed unchanged. Saved evidence was
independently ACCEPTED_WITH_RISK; image/cache retained, no service installation
or startup. See `../checkpoints/companion_local_parent_proof_20261017.md`.
This narrows the registry-fallback evidence gap for that exact path; it does
not establish whole-install policy, import isolation or a usable explanation.

October18 isolated Python3.11 test: audit-log and risk-stub imports passed;
memory reached source validation then failed with RuntimeError, with insufficient
retained detail to identify the guard. Orchestrator was not attempted. All three
test containers were removed; the seven original services stayed unchanged and
stopped. An independently reviewed offline diagnostic correction does not resolve
that failure or authorize a retry. Complete imports and restoration remain
INCOMPLETE. See `../checkpoints/companion_installed_imports_20261018.md`.

October18 targeted continuation (04:53 New York): memory reached source
validation but failed the preserved activity guard, with one denied socket
operation and no denied repository import. Exact socket operation/caller is
UNVERIFIED; no outbound traffic or actual service failure is established.
Orchestrator was not attempted. One temporary helper removed; seven original
selected container snapshots unchanged/stopped. No rerun of the two passing
modules, package changes or service startup. Restoration remains INCOMPLETE.

October18 attribution follow-up (04:59 New York) identified the sole blocked
operation: socket bind from urllib3.util.connection._has_ipv6, line127. Memory's
application import returned before the strict zero-denial validation rejected
it. No absent dependency is shown; exact installed caller body/address not
captured. Orchestrator still unattempted. Guard unchanged, one helper removed,
seven selected original snapshots unchanged. This diagnoses the test rejection,
not a working explanation service. No further retry or contract change implied.

Read-only caller-source inspection subsequently found identical urllib3 code in
the stopped memory/orchestrator containers: `_has_ipv6("::1")` attempts only a
localhost ephemeral-port bind, catches failure and closes its socket. This
supports a capability-probe diagnosis, not an outbound request; exact loaded
helper bytes/arguments were not captured. Guards/acceptance unchanged, no new
import test, package change or startup. Seven selected original snapshots match.
See the checkpoint for hashes, source preservation and proposed narrow contract.

An optional source/code/argument-pinned blocked-local-probe contract is now
implemented and independently ACCEPTED_WITH_RISK offline (57 targeted tests).
Strict zero-denial mode remains default; the opt-in still physically denies the
bind, records its count/evidence, and rejects other or repeated operations.
No actual import attempt under this contract or existing-service startup yet;
installed3.11 behavior and explanation restoration remain UNVERIFIED/INCOMPLETE.

October18 05:23 New York: one authorized remaining-only v2 run passed actual
Python3.11 memory/orchestrator imports with synthetic settings/frozen source and
no lifespan. Memory's single local probe stayed blocked and visible; orchestrator
had zero events. Both helpers removed, seven selected original snapshots
unchanged. Separate evidence review ACCEPTED_WITH_RISK. Restricted import gap
closed; complete SDK/storage startup, installation and explanation still not
proven. Do not repeat audit/risk or infer whole-policy approval.

Portfolio reuse assessment is complete for the named source surfaces, not an
implemented ED-002 portfolio. Shared cash already exists in E10; baseline
accounts remain independent. Specific integration/contract gaps and existing
tests are in `portfolio_reuse_assessment_20261018.md`. No failed study rerun,
new comparison or financial-logic implementation. Consolidated remaining
installation/research boundaries: `../checkpoints/companion_batch_closeout_20261018.md`.

**Do not:**
- run unregistered signal hunts on any symbol;
- rescue failed variants;
- tune parameters on the holdout;
- generalize a scoped rejection to a whole asset class;
- add paid data or infrastructure without a cost-benefit case (`research_budget_90d_20261011.md`).
