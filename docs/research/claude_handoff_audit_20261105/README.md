# Independent audit of Claude's imported-document and code-audit handoff

Bot relation: BOT_RULES for source findings; STANDALONE for document provenance. Runtime configuration not checked.

Role: AUDITOR. Checked 2026-11-05T18:43:55Z against working tree HEAD `82b5f216e`,
latest work log and PROJECT_STATE. Existing dirty changes were preserved.
This is an independent check of Claude's claims, not approval of Codex's own implementation.
The bounded handoff review is complete; the whole-bot audit and operational objectives remain INCOMPLETE.

## Answer and decision impact

Several defects are real, including a reproduced daily-loss accounting failure. But the handoff should not be
accepted literally: its default-pyramiding claim is contradicted by the upstream position-aware guard, its archive
assurance is too broad, and stale evidence files do not establish that ES is stopped. Do not change the simulation's
entry policy or restart ES on those assertions. No rules, queue priorities or operations are adopted by this review.

## Scope and evidence boundary

- SHOWN: the complete supplied attachment was read: 98 lines, 10,553 bytes, including the import and all three
  code-audit updates through BA-39. Input: `/Users/baitus/.codex/attachments/18b26e3d-699a-4db6-b14c-173c59fbfb29/Pasted text.txt`.
- SHOWN: the import README, complete 30-row reconciliation, BA-23 through BA-39 report sections, relevant source
  branches, reachability CSV, CMC primary timing amendment, queue and latest work-log entries were inspected.
- SHOWN: all 30 quoted rule strings were compared programmatically with the imported source; relevant surrounding
  source passages were read. This is NOT a fresh full semantic audit of every claim in the 668-line research document.
- UNVERIFIED: whether the local rev129 export is complete and unchanged relative to the private Claude artifact.
  Local fingerprints establish identity of files inspected, not fidelity to an inaccessible original or truth of cited papers.
- Not inspected: runtime trading settings, accounts, credentials, current processes, host services, scheduler UI or
  server state. Claude's whitelisted local configuration observations remain CLAIMED by Claude in this review.
- No production code, frozen results, source export, configuration, scheduler, server or trading operation changed.
  No backtest, market-data experiment, full suite or profitability evaluation was run.

## BA-23 through BA-39

SHOWN below means source behavior was checked, not observed production exploitation or operation. Synthetic
reproductions are explicitly identified; other rows are source/caller checks only.

| Finding | Independent assessment and practical consequence | Evidence |
|---|---|---|
| BA-23 | **Contradicted as a default-behavior claim; conditional defects SHOWN.** `position_aware=True` is the runner default and the shared decision function suppresses a held-position buy before scaling. With it false, the unused multiplier, reset references and disabled-scaling `is_scale=False` behavior remain genuine concerns. A changed buy signal alone does not prove an add. Do not demand an owner choice between disabling/modeling default adds without checking the intended mode. Six decision probes and one scaling probe reproduce the distinction. | `services/execution/strategy_runner.py:414`, shared call to `select_exit_decision`; `services/execution/runner_decision.py:66`; `services/risk/position_scaling.py` |
| BA-24 | **SHOWN for the inspected percentage gate's paper-row input contract.** Position rows have no percentage fields, so percentages summarize to zero. Position-count and open-intent limits are separate; this is not proof that every safeguard or every order route is inert. Read failures in the collection helper become empty lists. | `services/risk/exposure_controls.py`; `storage/paper_trading_sqlite.py:list_positions`; `services/validation/paper_multi_symbol_validation.py:collect_runtime_rows`; synthetic row probe |
| BA-25 | **SHOWN missing normal-path metric ingestion, not an unconditional impossibility.** ExecutionGuardStore realized P&L has no production writer found; paper fills do not increment its trade counter. Configured gates can still react to stored metrics supplied elsewhere. Distinguish this store from live `risk_daily` and other paper risk engines; no current settings were independently inspected. | `services/execution/safety.py`; ExecutionGuardStore caller searches; `services/execution/_executor_submit.py` trade-attempt path |
| BA-26 | **SHOWN in the legacy guard.** Zero timestamps skip its age refusal; future timestamps have negative age. The separate staleness guard refuses zero but also permits future time. Do not extend this finding to the newly reviewed strict paper quote adapter without tracing that caller. | `services/risk/market_quality_guard.py`; `services/risk/staleness_guard.py`; separate `services/market_data/paper_snapshot_quote.py` boundary |
| BA-27 | **SHOWN, opt-in.** Missing probability uses 0.5 and refuses both default buy and sell thresholds. Additional issue: NaN clamps to 1, allowing buys and refusing sells. Disabled gate permits both. Synthetic probes reproduce all three cases; current enablement unknown. | `services/feature_gate.py:proba_gate` |
| BA-28 | **SHOWN and reproduced; HIGH before live.** A failure inside the real daily-loss transaction returns False, the sink ignores it, returns `ok=True`, and never calls the failure-flag writer. False also means duplicate, so simply treating all False as fatal is not a complete repair contract. Existing October finding/U-09 is not new work. | `services/journal/fill_sink.py:147`; `services/risk/risk_daily.py:apply_fill_once`; injected SQLite failure probe |
| BA-29 | **SHOWN, narrower wording required.** Missing `risk_daily_fills` suppresses this accounting-invariant check, even with a canonical fill. It does not prove that every health check reports healthy. | `services/risk/system_health.py:_check_accounting_invariant`; disposable SQLite probe |
| BA-30 | **SHOWN known best-effort contract.** Counter-update errors are caught after an attempt. A successful submission is not proof that daily trade/notional counters persisted. No live failure reproduced. | `services/risk/risk_daily.py:record_order_attempt`; existing substrate backlog |
| BA-31 | **SHOWN conditional monitor gap.** Filtering symbol/time after taking the newest 1,000 global fills can omit a quiet symbol. Whether nine isolated paper accounts share this exact journal is not established; do not assume cross-account contamination. | `services/analytics/paper_sim_monitor.py:_trade_journal_snapshot`; `storage/trade_journal_sqlite.py:list_fills` |
| BA-32 | **SHOWN stage-authority gap, not absence of all order protection.** The inspected default paths do not consult `action_allowed`; placement still has its own arming/guards. | `services/control/deployment_stage.py`; caller searches in runner, paper engine, `place_order.py` |
| BA-33 | **SHOWN conditional TLS weakness.** SMTP calls `starttls()` without a verifying context. This Mac's Python default was reproduced as CERT_NONE with no hostname check. TLS errors return failure rather than proceeding to login. Selecting Slack does not itself prove no email caller is configured. | `services/alerts/email_notifier.py:46`; local `smtplib`/`ssl` probe, no SMTP connection |
| BA-34 | **SHOWN helper inconsistency.** Flat windows return RSI 100 in momentum/pullback recovery versus 50 in the default implementation. Other predicates may prevent an actual sell; no whole-strategy outcome is established. | RSI helpers in `services/strategies/momentum.py`, `pullback_recovery.py`, `impl_mean_reversion_rsi.py` |
| BA-35 | **SHOWN; impact understated.** Same-signal-close fills are idealized and their bias is not bounded as merely slight. Non-finite archive rows are rejected, but finite zero/negative prices survive; missing time continuity is not validated there. The archive therefore does not guarantee immunity to zero-valued equity. No historical result was recomputed. | `services/backtest/parity_engine.py:run_parity_backtest`; `services/backtest/ohlcv_archive.py:normalize_ohlcv_rows`; zero/negative/NaN probes |
| BA-36 | **SHOWN promotion evidence gap, known pre-live concern.** The cited capped-live size check hard-codes success. No order caller of the cited strategy `decide()` cap was found. Other sizing helpers exist, so this does not prove that all conceivable order paths lack caps. | `scripts/check_promotion_gates.py:1094`; `services/strategies/es_daily_trend.py`; `services/control/kernel.py:contracts` |
| BA-37 | **SHOWN.** `or 1.0` converts measured zero fill/stability to nominal values in live-stage evaluation. NaN stability leaves the allocator's base weight unpenalized: the synthetic result is 0.10 with a 0.25 cap, NOT allocation of the full account. Missing metrics/budget evidence are permissive. Paper/shadow return no new-risk permission. | `services/control/kernel.py:evaluate`; `allocator.py:compute_allocation`; `cognitive_budget.py`; NaN allocator probe |
| BA-38 | **SHOWN opt-in stale-signal gap.** Placement evaluates gate state without signal age. Missing/invalid payloads can be fail-closed separately, but enabling that does not add timestamp freshness. Current settings unknown; no order or account call made. | `services/execution/place_order.py:482-524`; `services/ops/risk_gate_contract.py:RiskGateSignal` |
| BA-39 | **SHOWN accounting-label inconsistency.** Gross win rate can report a winner with negative closed-trade net P&L. Summary net-realized also expenses open-lot buy fees, so it differs from sum of closed-trade net P&L; specify conventions rather than assume missing cash or wrong NAV. Some newer expectancy/return fields already use net P&L. | `services/analytics/journal_analytics.py:fifo_pnl_from_fills`; feedback/evidence callers; synthetic gross win +$0.25, closed net -$0.75, summary net -$1.00 with an open-lot $0.25 fee |

## Import and all 30 rule mappings

SHOWN fingerprints at inspection (original imported files left unchanged):

```text
research_document_rev129.md  146703 bytes  8f138aec87e859c8426320101c50b911852fa8cbf98c0273261d0a8294b67152
proposed_rules_reconciliation.md          86a9d6b86d40e885000ec1c91cae7a40e17befa2bf73cb6b26b1d356196d9cbe
README.md                                328463ec908e4c71f2f54711043611a215a1db755a00b3603bd0c89806842142
```

- SHOWN: 30 reconciliation rows. R01-R13 and R15-R23 (22) match literally. R24-R30 (7) match after ignoring
  initial capitalization. R14 inserts an explanatory parenthesis in place of the source's direct request.
  Thus "all word for word" is inaccurate, but seven discrepancies are cosmetic, not invented research findings.
- SHOWN: the reconciliation itself warns that keyword misses cannot establish semantic absence. Its headline/count
  "0 in AGENTS/brief" should mean no exact adoption located, not no equivalent protection. POP already requires
  forward evidence, costs, preregistration, trial accounting and evidence-qualified conclusions.
- UNVERIFIED: original empirical/source claims supporting these 30 rules; this pass did not reopen their primary
  papers, vendor timing claims or URLs. No wholesale adoption is justified by this import audit.
- Recommendation: retain the proposals for owner selection, adapt only demonstrated gaps. R06's rough Sharpe
  multiplier is not a universal adjustment; R10/R23 need labels available at each historical decision, not merely
  a snapshot dated before inspecting results; R12/R24 need an executable exit policy rather than a fictional market
  fill in limit-only mode or a universal 30-day warning. R29 needs calibrated null false-positive behavior, not a
  guarantee that every null sample fails; Clark-West is not universally applicable to arbitrary forecasting comparisons.
- R28 timing: the accepted `cmc_trending_log/primary_analysis_schedule_20261010.md` fixes entries November 10
  through February 7 and earliest primary analysis February 15, 2027 at 12:00 UTC. No interim scoring is allowed.
  A question using that entire primary window needs prospective registration, but November 10 is not a universal
  deadline for every future question: a separately registered future window is possible. No scoring was enabled here.

## Coverage and operational assertions

- SHOWN: CSV has 165 rows: 27 cited by earlier audit, 35 changed in the working tree, 103 gap_unaudited.
  CLAIMED by Claude: 61 gap modules read or scanned, leaving 42. The CSV does not identify those 61 by session;
  line counts/read-or-scanned assertions are not independently reproducible review coverage. Static imports also
  are neither a runtime trace nor exhaustive dynamic-call coverage.
- Contradicted as an assurance: "none of the remainder is on the simulation order path" cannot be certified from
  this map. `storage/trade_journal_sqlite.py` is still gap_unaudited and is imported by `paper_runner.py:20`.
  An earlier narrative says it was read, reinforcing that the map is not a current per-file completion ledger.
- SHOWN only as archive evidence: ES records end October 29 according to the inspected audit evidence. UNVERIFIED:
  that ES is stopped now, the cause, or an owner intent to run it. Historical endpoint results do not establish
  today's process state. No server access or restart is justified by that file timestamp.
- Scheduler/tracker/weekly-status and past server-authorization statements in this handoff were not refreshed
  through the app or host. They are not certified current by this source audit. Owner direction must not be invented.
- New evidence during this review: Claude's 15:03:05Z independent R3 packet review is ACCEPTED_WITH_RISK for the
  packet/proposal only (`r3_linux_packet_review_20261105/README.md`). This supersedes my 14:51 observation that
  review was missing. It did not run the packet. Timeout/start-receipt and non-vacuous fork checks are recommended;
  Linux behavior, host wiring, delivery and operating readiness remain unverified. No operational action was taken.

## Verification and disposition

Command (VERIFIED_ENV: existing local venv; cleared environment, synthetic inputs and disposable SQLite only):

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 CBP_STATE_DIR=/private/tmp/cbp-claude-handoff-audit ./.venv/bin/python -B -m pytest -q -p no:cacheprovider docs/research/claude_handoff_audit_20261105/test_claim_probes.py
```

SHOWN result: **17 passed, 1 warning in 0.19s**. Warning: existing `datetime.utcnow()` deprecation in canonical
journal code. These are reproductions of current defects/guards, not a repaired-code regression suite, full-suite
result or acceptance of production safety. No proposed production fix was implemented.

Bounded task acceptance criteria: input/provenance checked DONE; every BA-23..39 source claim checked DONE;
coverage/operational inference checked DONE; correction report and work-log entry DONE. Whole 103-file completion,
all rev129 source claims, current runtime/host state and repair implementation NOT DONE and not certified.

Recommendation: keep current engineering item 2/R3 as ordered; do not invent an extra simulation-policy decision
from BA-23. Preserve live-money blockers BA-28/36/37/38 and accounting concerns in the existing queue/parked record,
not an audit-triggered live repair. Research item 1 needs an explicit coverage disposition, not a claim of full closure.
Use net closed-trade metrics with an explicit open-fee convention in future authorized reporting (BA-39).

What could overturn these conclusions: a different runtime `position_aware` setting, deployed code differing from
this working tree, an updated coverage ledger, other verified gate callers, raw current ES/runtime evidence, or
independent reproduction contradicting these probes. Do not assume the Mac source is the server's installed code.

What do I know that could change the owner's decision that I have not yet said?
The most consequential owner choice in this handoff was based on a missing upstream guard. Real conditional
scaling defects remain, but there is no evidence here that default adds require changing the simulation. Conversely,
the daily-loss failure is not just theoretical: it reproduced through the real sink with a disposable database.
