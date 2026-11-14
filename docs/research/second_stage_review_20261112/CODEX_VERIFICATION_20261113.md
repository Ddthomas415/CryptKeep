# Independent verification of the forensic and second-stage reports

Bot relation: STANDALONE for historical research; BOT_RULES for inspected source and BOT_PAPER for attributed historical paper records. Current runtime trading configuration was not checked.

Checked 2026-11-13 UTC, starting 16:26:47Z; HEAD `3b49ead3fc41803d33cc270629f12f0e65b3d03c`, branch `backup/2026-10-31`. Role: AUDITOR. Report-only review of the next engineering queue item; no adoption of draft criteria, development, new market experiment or operational authority follows.

## Answer first

**SHOWN:** the main historical candidate calculations, trade-concentration figures, registered stress rejection and ES exit matrix reproduce. These are real historical model outputs, not invented results. The candidate made an absolute historical gain but finished below holding BTC over FULL at the primary cost. Lower drawdown/higher sample Sharpe are distinct from a demonstrated forward advantage.

**SHOWN:** the reports contain material interpretation errors. They revive a withdrawn paper confidence interval, understate later research exposure, call a `keep_researching` result a pass, and overstate readiness of the proposed forward protocol. The evidence does not justify dismissing all historical execution failures as merely future risks. **The draft v3.2 should not be frozen unchanged.**

This completes the six-item audit disposition, not every unresolved research question. Exact current trial accounting, inference qualification, full prospective measurement/evaluation readiness, current operations and profitability remain **INCOMPLETE**. Original reports, criteria, scripts, data and saved results are unchanged; this dated correction applies to the exact original report hashes below.

## 1. Six-item verification checklist

| Requested item | Result | Evidence and limit |
| --- | --- | --- |
| 1. Candidate comparison, description and concentration | DONE: numerical reproduction | Original comparison script: financial results and input hashes equal; only timezone-dependent date-label metadata differs. Description JSON is byte-identical. At 0.50% + 0.05%: 108 closed spells, net $84,530.94; top five contribute 82.084%; remaining 98 after removing the ten largest dollar winners lose $26,688.70. Two open spells add $16,894.75. These are compounded holding spells, not 108 proven independent outcomes. |
| 2. Registered 1.2% stress rejection | DONE: corrected frozen core replay | Baseline, all 13 one-at-a-time variants, Required 1/2, verdict and bootstrap equal saved corrected output. Verdict `reject`; 5/13 beat the matched mix's FULL Sharpe. The separate 105-cell grid was not rerun; no changed parameters or new cost experiment. |
| 3. Re-derive 747 and current total | PARTLY DONE: dated floor established; complete current count unresolved | 577 + 113 + 57 = 747. October 21 supplement already gives 752. Adding the register's 15 exit-parity configurations and 500 primary dip cells gives a conservative convention-specific subtotal of at least 1,267. Another 500 alternative-exit cells are visible; counting them separately gives 1,767. Neither is a complete independently effective trial count. |
| 4. ES exit matrix | DONE: all eight cells reproduce | 3,077 rows match frozen slice SHA256 `c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb`. SMA200/transition: no exits +854.35%, old defaults +1.28%; both saved results match. Fee 7.5 bps, slippage 5 bps, signal-bar-close fills, all-cash compounding, daily-close exit evaluation, no time stop. Current registry hash differs from historical registry, but outcomes/parity checks match. Not realistic-cost or live-execution proof. |
| 5. Challenge software-loss attribution | DONE: original conclusion requires narrowing | Withdrawn ES cohort inference and historical execution/record-integrity defects contradict the blanket account that defects concern only future runs. Inspected evidence does not establish a quantified economic trading loss causally attributable to a particular bug. No new causal counterfactual or raw-ledger reconstruction was run. |
| 6. Forward-tracker facts | DONE for local files/source; operational timing remains unverified | v2: October 18 recorded 168.87 h late, October 25 0.87 h late; November 1/8 absent; latest marks October 25. v1: initialization October 11 and four later rebalance rows through November 8; overwritten history/no per-decision recording times cannot prove on-time dispatch. No task run, UI inspection or current process check. |

## 2. Material corrections to the inspected reports

### F1. A withdrawn ES confidence interval is presented again as strategy evidence

**SHOWN, decision-relevant:** [forensic section 3d](../forensic_audit_20261112/README.md#3d-paper-runs-through-the-actual-bot) cites eight losing ES records and the -$1.05 to -$0.09 interval, qualifying only the old fee figures. The [October 7 reconciliation](../economic_evidence_current_20261007.md) explicitly says not to reuse this interval. The [original correction](../paper_evidence_standing_20261005.md#corrections-2026-10-07-after-the-shared-review-paper_evidence_shared_review_20261007md) withdraws it because five records are development/mispriced observations, not a coherent strategy cohort. The [identity correction](../es_laptop_records_identity_correction_20261007.md) establishes zero qualified corrected-SMA200 records; the three later trades used a legacy SMA20-like/default-exit policy.

The original breakout +$3.07 figure is also superseded by fee-reconciled **+$2.5136**. [Per-fill reconciliation](../trade_record_qualification_and_fee_reconciliation_20261007.md) records zero slippage for those 40 paper fills, not the blanket 5-bps assertion in forensic section 3d. Preserve the raw rows but do not use those obsolete figures to judge strategy efficacy.

### F2. Historical software defects cannot be classified solely as future risks

**SHOWN:** the [paper audit](../e01_paper_evidence_audit_20261002.md), [ES identity/lockout evidence](../es_laptop_records_identity_correction_20261007.md), and per-fill reconciliation document past lockout, wrong-symbol pricing/contamination and inconsistent P&L semantics. These affected historical execution or evidence. They do not identify how much economic loss each defect caused.

Replace the broad attribution in forensic sections 6/10 with: **No inspected evidence establishes a quantified past trading loss causally attributable to a software defect. Historical defects did affect execution and record integrity; their incremental economic impact remains unquantified.** Missed modeled opportunities are not realized loss. This does not make every failed signal an engineering problem.

### F3. Lower-cost sensitivity is not a pass; selection accounting is not current

**SHOWN:** second-stage section 3 says a pass at 0.5%. Its own cited [saved sensitivity](../stress_fee050_exploratory_20261011/stress_fee050_result.json) says `exploratory_verdict_same_rules: keep_researching`, not pass. Period A's drawdown is worse than the matched mix at that fee. The registered 1.2% rejection is preserved. Both cost levels can produce positive absolute historical returns without satisfying the robustness criteria.

**SHOWN:** the [pass-2 ledger](../trial_ledger_reconciliation_20261015/pass2_findings_20261015.md) and [October 21 supplement](../trial_ledger_supplement_20261021_record_repair/README.md) are already more specific than the audit's approximate 750. Later [dip-study source](../dip_recovery_majors_20261108/describe.py) has 10 coins x 5 dips x 5 targets x 2 datasets = 500 primary cells, plus the alternative touch/close exit convention. Fee scenarios, benchmarks, corrected reproductions and period splits are not new configurations. Some earlier sources pool symbols while others count each symbol, so harmonizing the complete total remains unresolved. The pass-2 CSV has six exact rows, two lower bounds and one unknown, not its prose's seven exact rows.

The 1,267/1,767 subtotals expose omitted research exposure, **not** a defensible DSR input or a claim that all later searches preceded the candidate's original selection. The old [DSR](../dsr_btc_eth_trend_20261011/README.md) is conditional on its historical N/dispersion assumptions. The [reconciliation warning](../trial_ledger_reconciliation_20261015/count_reconciliation.md) already withholds a valid current DSR until N and V are independently checked. No DSR was recomputed here.

### F4. Forward histories cannot be added into five independent clean weeks

**SHOWN:** v1 and v2 overlap on the same coins/market dates. Their files do not establish five independent weeks. v1 reconstructs and overwrites its history, trades at Sunday close, uses 60/5-bps costs and gives its BTC control no entry fee. v2 models next-day opens at 50/5 bps, keeps append-only recording times and explicitly records `observed_fill: false`.

Sources: [v1 source](../paper_btc_eth_trend_20261009/paper_btc_eth_trend.py), [v2 source](../paper_btc_eth_trend_v2_20261012/tracker.py), and their state/ledger files. The independent source check read the restored automation's public definition: its intended November slot is Monday 01:47 UTC under the documented New York assumption, but app dispatch/timezone and future reliability were not demonstrated. The cause of the vanished automation remains **UNVERIFIED**. Sleep/off causation for CMC gaps and universal alert absence were not independently established.

## 3. Draft v3.2: preserve the separation of questions, repair the contract

**SHOWN:** the 26/52-week dates are internally consistent. Q1/Q2 separation from Q3 is useful; continuing the existing tracker does not require first implementing the bot adapter. No new framework is needed.

**INCOMPLETE before freezing the whole protocol:**

1. **State the continuation baseline.** The unchanged tracker continues October 18 accounts. November 15 return normalization is a valid continuation-window design, but inherited holdings and pre-window costs must be explicit. It is not a fresh $1,000 start. Changing `--start` changes that contract and the availability of the first decision-day mark. Fixed 25/25/50 in v3.2 also differs from the second report's exposure-matched benchmark; specify the intended benchmark rather than treating them as interchangeable.
2. **Separate existing primary output from additional work.** Tracker v2 supplies scalar 50-bps fee/5-bps-slippage marks, not Monday-open bid/ask observations, per-asset cost reruns, 90-bps results, a hold-ETH account or the full requested per-leg report. Those need a separately specified evaluation/observation path preserving primary ledgers. A half-spread is a quote-based component, not measured total execution cost or maker fill evidence.
3. **Freeze the cost evaluation details and cutoff.** Define percentage half-spread denominator, valid observation window/eligibility, minimum observations per asset, and a hard evaluation cutoff. Resolve Q1 being final at 26 weeks while permitting recomputation "once" measurements exist. Alternative costs change quantities/cash path; they cannot simply be subtracted from the saved NAV. State starting holdings and the counterfactual accounting method without changing the primary experiment after viewing outcomes.
4. **Define who observes the 48-hour deadline.** Classification from ledger lag is possible retrospectively; actual timely declaration/notification is not supplied by a weekly task that failed to run. The missed-run check is still a proposal. A documented manual observer could be considered instead of another scheduler; neither was installed or adopted here.
5. **Keep Q3 conditional and complete its parity contract separately.** Initial wallet, clock, modeled-versus-quoted fill comparison, sizing/rounding and rejected/unfilled legs need explicit treatment. Any parity, accounting or required-evidence breach must have a defined failure outcome, not just missed decisions. Existing no-add/full-close runner semantics conflict with weekly target resizing; no casual configuration-only integration.

These are contract/measurement gaps, not permission to restart held infrastructure or delay existing tracking unnecessarily. Broadly stopping CryptKeep development after one candidate fails is an **owner scope decision**, not a mathematical conclusion or an adopted policy hidden in draft consequences. Preserve the multi-symbol mandate and other accepted work.

**SHOWN:** the final approval procedure says hash the file and then change its DRAFT heading. Freeze the **final bytes after** heading/date edits; otherwise the registered hash names different bytes. No criteria edits or approval occurred here.

## 4. Reproduction evidence and safety boundary

Commands were one scratch invocation of each named analysis using existing `.venv` Python **3.12.10**, `-B`, bounded 120 seconds per child, no retry. All finished: comparison **1.275 s**, description **0.668 s**, stress core **14.163 s**, ES **28.692 s**. These are script replays, **not a test-suite pass** or independent new simulator implementation.

The [replay driver](codex_verification_20261113/replay_driver.py), [manifest](codex_verification_20261113/manifest.json), four stdout/stderr pairs, generated results, [checks](codex_verification_20261113/checks.json) and [checksum inventory](codex_verification_20261113/SHA256SUMS.json) preserve the evidence. Scratch root is recorded in the manifest. Only the two required public daily files were extracted from the archived BTC/ETH input; archive SHA256 matched `fbfb78339db65dfecd7b7ca5d293cca71c7c2241318f7915dfb651b8e6db6fb0`, and both file hashes matched frozen majors inputs. Selected public ES rows were queried read-only and placed in a scratch database only after the exact frozen-slice hash matched. Source copies match original bytes before execution; the manifest's post-check confirms original copied source/input files unchanged. Ancillary state/log writes were directed to scratch. No credentials/configuration reads, current application queries, network/data downloads, services, tasks, accounts or trading actions.

Two qualifications are not hidden by "matches":
- `compare.py` formats period metadata with timezone-local `date.fromtimestamp`. Here those labels shift one calendar day earlier than the saved UTC labels. The actual UTC-indexed periods and financial results do not change. The full comparison JSON is **not** byte-identical; only date-label metadata differs. No rerun to improve the match and no source repair.
- ES current `strategy_registry.py` hash differs from its October artifact. All eight cells, input, assumptions, benchmark and parity validations still match. This demonstrates compatibility of this inspected path, not identity of the whole historical checkout or full-harness correctness.

Report input hashes, before any correction:
```text
forensic_audit_20261112/README.md
26214c8c1b19a44080afc1b664acd1141cebc57f225685d073b88d674f8de630
second_stage_review_20261112/README.md
ea82402772f40fae078cebe55bc58f71c4a4656b58f529bb927b07c1cda117e0
btc_eth_forward_experiment_20261112/CRITERIA_DRAFT.md
9dc85f1ad05c57947e14c6df67991604b49041cb37da773f7165ddf3edd811d1
```

## 5. Disposition and the next decision

Audit report: **READY_FOR_INDEPENDENT_REVIEW** pending the final separate GATE. Nash independently inspected trial accounting/historical software claims; Darwin independently inspected tracker/criteria. They did not run the main agent's numerical replays. Their independent source findings support the corrections, not current runtime or economic acceptance.

Recommend retaining existing forward tracking and revising only the demonstrated contract/reporting gaps before the owner chooses whether to freeze Q1/Q2 and separately authorize Q3 work. Do not automatically adopt the second report's relaxed paper minimums: the existing full simulation contract/hold remains unless the owner explicitly changes it. No source, account, service, schedule, deployment, capital or strategy change is authorized by this audit.

Evidence still needed: complete convention-consistent trial/selection accounting; qualified inference if claiming an advantage; prospective observations with dated source identity; a complete evaluation contract; current operational evidence when separately authorized; later candidate implementation/reconciliation/fault proof if Q3 is chosen. Raw historical paper databases, intraday causal loss paths, live services, account fees/current funds, external artifacts/Claude hidden tool outputs and scheduler dispatch histories were not inspected. These limits prevent broad causal, current-runtime, comprehensive-history or profitability certification.

Two material assumptions: the hash-bound named scripts/results are the intended frozen evidence; the owner's continuation refers to the current queue's audit item, not adoption of v3.2 or release of held work. If either is false, this audit's scope must be corrected before further action.

What do I know that could change the owner's decision that I have not yet said?

The historical candidate and exit-policy effects are reproducible, so the repository is not just paperwork without any usable result. But the latest summaries again reuse invalid evidence and overstate forward readiness. Neither failure makes the candidate worthless; neither a repaired summary nor a six-month descriptive PASS establishes a durable after-cost edge or that the bot can execute it. The smallest next decision is the corrected prospective contract, not another broad build or a blanket rejection of research.

## Independent review receipt (appended after review)

Separate GATE Pascal `01a1d5c4-7caf-7133-8d86-234d8bdb36be`, checked through **2026-11-13T16:39:10Z**, returned **ACCEPTED_WITH_RISK, report-only; no blocking report errors** for the exact pre-receipt report SHA256 `9dbca20968e46d26a5be0319253f4994eb8e625f88c5e54c2005d74908ca70ef`. This supersedes section 5's pending-review status only. The reviewed report body was not otherwise changed.

The reviewer inspected underlying reports/source/preserved results, verified all 14 evidence-inventory file hashes and 565 manifest source hashes, and confirmed O-136 to O-138/count bookkeeping. No analyses/tests or runtime operations were repeated. Acceptance excludes economic proof, complete trial accounting, criteria adoption, development readiness and operations. Complete selection accounting, causal loss attribution and prospective measurement remain unresolved. No additional finding within the bounded review was withheld.
