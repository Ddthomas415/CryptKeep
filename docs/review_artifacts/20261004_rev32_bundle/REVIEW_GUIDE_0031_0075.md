# Review guide for patches 0031-0075

Written 2026-10-05 by Claude for the operator, who is the sole reviewer. No code
is changed by this document. It replaces nothing in REVIEW_HANDOFF.md, which
covers 0001-0030 with Codex's recorded statuses.

## State

- 45 patches, 0031-0075, on branch `claude/series-rev33` in the review clone,
  on top of `origin/master` @ `97c24c8e4` plus 0001-0030 (0011 HELD, 0019 not
  applied). Head: `7242a23ba53a8ec7ff9ec2bad4a06be9cd2b468d`.
- None is reviewed, accepted, pushed, merged or deployed. Every one is
  READY_FOR_INDEPENDENT_REVIEW by my own statement only.
- Full suite at head: 4904 passed, 33 skipped, 0 failed (with `PYTHON` and
  `PYTHON_BIN` set to the venv interpreter).
- Bundle folder for patch N is N + 8 (0031 is folder 39, 0075 is folder 83).
  Each folder has the patch, a production-only diff and a README.

## Why review now

Each patch was built on the unreviewed ones before it. Two needed a later
correction that a review would likely have caught sooner:

- 0057 kept every venue lookup error tracked, including the venue's explicit
  "order not found" (corrected by 0074), and let the tracked set outgrow the
  reconciler's 60-row window (corrected by 0075).
- 0071's notes said market-rule refusals lack the boundary prefix. They carry
  it (corrected in 0072's work-log entry).

Earlier READMEs (folders 39-69) report "19 failed, same as master". That was
my test environment, not master; see the MANIFEST note at rev73.

## Order to review in

Groups 1-6 are the live order path and are ordered by how much money is
behind a mistake. Groups 8-9 affect the evidence being collected today.
Subsets were not tested on their own: the series was only ever built and run
in number order.

### 1. Live reconciler (read as one change)

The lane that follows an order after it is sent. 0057 changed when an order stops being tracked; 0074 and 0075 correct two things 0057 got wrong. Do not apply 0057 without them.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0057 | `194fa2ac` | 65 | live_reconciler.py | Reconciler keeps tracking orders the venue still has working; base-asset fees valued in USD. |
| 0073 | `dd972ca6` | 81 | live_exchange_adapter.py, live_reconciler.py | A failed venue lookup is not counted as "order not found". |
| 0074 | `1e1460c1` | 82 | live_reconciler.py | An explicit venue "order not found" closes the intent again (corrects 0057). **Needs 0057, 0073.** |
| 0075 | `7242a23b` | 83 | live_reconciler.py | Reconciler looks at every tracked intent each pass, not the newest 60. |

Check or decide:

- Is one explicit `OrderNotFound` past five minutes enough to close an order (documented rule), given 0073 asks three clean answers over 15 minutes for an unknown submit?
- Nothing closes or cancels an order that stays tracked for good (lookup error that never clears; resting limit order).
- Drill 3.4 with a real venue: which exception does a fake order id raise? Not verified.

### 2. Canonical live consumer

The process that turns a queued live intent into an order.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0037 | `fccd63aa` | 45 | intent_consumer.py, live_intent_consumer.py | Consumers refuse an intent with no reference price instead of claiming zero notional. |
| 0071 | `bc325a33` | 79 | live_intent_consumer.py, live_intent_queue_sqlite.py | A boundary refusal is rejected, not an unknown submit; its daily claim is returned. |
| 0072 | `da740471` | 80 | live_intent_consumer.py | An intent whose exchange adapter could not be built is rejected, not an unknown submit. **Needs 0071.** |

Check or decide:

- 0071 and 0072 make a refused or unbuildable intent final (`rejected`). It is not retried.
- 0071 gives the daily trade/notional claim back for refusals and router rejections. Confirm you want refusals not to count against `max_trades_per_day`.

### 3. Order boundary (`place_order`)

The last check every live order passes.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0055 | `7c9ed268` | 63 | place_order.py, fetch_coinbase_ccxt.py | Order boundary refuses non-spot markets explicitly. |
| 0070 | `4990c292` | 78 | place_order.py | Order boundary refuses buys on a symbol locked after consecutive losses. Relies on the lock that 0059 makes work. |

Check or decide:

- 0070 refuses buys only on a locked symbol; the legacy executor holds back both sides. **Your decision.**
- The lock is matched on the symbol text of the fill against the symbol text of the order.

### 4. Fill accounting and the order-block flag

What a fill does to positions, daily loss and the consecutive-loss lock, and how the fail-closed flag is lifted.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0059 | `c15d5664` | 67 | fill_sink.py, risk_daily.py | Loss lock counts closing fills once; a failed daily-loss write is a failure. |
| 0065 | `5c3b64df` | 73 | repair_risk_sink_failed.py | Order-block flag cleared only for a verified cause, with an operator event. Uses `RiskDailyDB.fill_applied` from 0059. |

Check or decide:

- 0065: a run that used to end `repair_complete` for a drift flag now exits 1; `--force-clear --reason` is the override.
- A replayed loss counts on the day of the replay, not the day of the fill.

### 5. Live enable and kill switch

Operator actions that turn live trading on or off.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0062 | `4a5d112b` | 70 | scripts/killswitch.py | Kill-switch command records its changes; release needs a record. |
| 0069 | `1c2e7768` | 77 | live_enable.py, live_enable_wizard.py, config_editor.py | A failed live enable really restores the config and reports truthfully. |

Check or decide:

- 0069 changes failure handling only. A token consumed by a failed enable stays consumed.

### 6. Gates in front of an order

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0047 | `b6d87e23` | 55 | clock_sanity.py | A clock measurement is cached as OK only when its uncertainty is inside the threshold. |
| 0056 | `d39f74ff` | 64 | signal_service.py, model.py, feature_gate.py | Enabled AI and probability gates refuse when they cannot evaluate. |

Check or decide:

- 0056: a broken or missing model now refuses orders where it used to let them through. Confirm that is what you want when the AI gate is enabled.

### 7. Legacy executor

Nothing feeds this path today (docs/research/live_order_origin_review_20261005.md). Lower urgency unless you choose it as the live path.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0039 | `5ebd5eb9` | 47 | _executor_submit.py | Legacy executor does not submit an intent older than the intent TTL. |
| 0045 | `b2b3a48f` | 53 | _executor_submit.py, exchange_client.py | Legacy executor classifies submit errors by type; TTL never cancels a possibly-sent intent. |
| 0058 | `024023fb` | 66 | _executor_reconcile.py, execution_store_sqlite.py | Legacy executor reconciles partially filled orders to completion; accounts before recording. **Needs 0057.** |

### 8. Promotion gates and evidence qualification

What decides paper -> shadow -> capped live -> scaled live.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0034 | `3be364a6` | 42 | paper_engine.py, paper_evidence_qualification.py, paper_gate_qualification_report.py | Fills carry sample-origin fields; flagged fills do not qualify. |
| 0035 | `088b2805` | 43 | check_promotion_gates.py | Paper gate withholds expectancy when the journal does not match qualified evidence. |
| 0036 | `1b9f2dd2` | 44 | check_promotion_gates.py | Retirement check reports a journal that does not match qualified evidence. |
| 0063 | `9ebc4cf2` | 71 | check_promotion_gates.py | Capped-live gate counts only capped-live evidence. |

Check or decide:

- All four only make a gate harder to pass or a report more explicit.
- Still not checked by code: "Position size at 25% of intended" is reported passed without a check.

### 9. Paper engine and campaigns

The path producing evidence now.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0031 | `f78a00d8` | 39 | strategy_runner.py | Runner lock: two starters cannot both reclaim a stale lock; a runner releases only its own lock. |
| 0032 | `300753b6` | 40 | run_es_daily_trend_paper.py | Sample-data short run gets its own state directory; paper make targets import again. |
| 0033 | `c5393e46` | 41 | signal_quality.py, forward_returns.py, local_data_reader.py | Sample OHLCV snapshots are not returned to research readers. |
| 0038 | `9564bee0` | 46 | paper_engine.py | Paper market orders are safety-checked at the market price. |
| 0040 | `714b38ae` | 48 | paper_engine.py | Paper engine refuses to trade on unusable fee, slippage or cash settings. |
| 0041 | `969585bb` | 49 | paper_engine.py, paper_trading_sqlite.py | Paper ledger refuses invalid fills; float rounding no longer strands positions. |
| 0042 | `77545877` | 50 | paper_engine.py | Paper orders are not filled against a quote that fails the market-quality check. |
| 0044 | `877401c2` | 52 | paper_engine.py, paper_runner.py | A paper fill whose evidence record was lost is repaired at the next runner start. |
| 0051 | `f57547b6` | 59 | _executor_submit.py, paper_engine.py | Recorded fill slippage is measured against the decision price, or absent. Also touches the legacy executor. |
| 0067 | `7244a65d` | 75 | outcome_logger.py, outcome_summary.py | Strategy outcome log follows the state directory, not the working directory. |
| 0068 | `21d7a505` | 76 | paper_stop.py | Paper stop acts on the current state directory's campaign only. Edits a test added by 0067. |

Check or decide:

- 0068: `make paper-stop-now` no longer stops `make paper-run-short` or managed campaigns. **Operator-visible.**
- 0067: each campaign with its own state directory starts its own outcome file; existing mixed rows stay where they are.
- 0040, 0041, 0042 can turn a paper order that used to fill into a refusal. Expect fewer, cleaner paper fills.

### 10. Liveness and alerts

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0043 | `8066e739` | 51 | heartbeat.py, paper_strategy_evidence_service.py, run_paper_strategy_evidence_collector.py | Dead-man check sees the paper collector; a future-dated beat is not trusted. |
| 0060 | `7d491270` | 68 | cbp-dead-man.service, cbp.env.example, check_dead_man.py | Dead-man heartbeat names are set per host. |
| 0046 | `f411c52f` | 54 | alert_dispatcher.py, alert_router.py, send_test_alert.py | Alert results say whether anything was delivered; real delivery test command. |

Check or decide:

- Alerts are off on the laptop; none of this was exercised against a real channel by me.

### 11. Research and data collection

No order path.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0049 | `dea64378` | 57 | parameter_sweep.py, walk_forward.py, run_archive_parameter_sweep.py | Parameter sweep can hold windows out of its ranking; reports no-effect grids. |
| 0050 | `84fe6413` | 58 | ohlcv_preflight.py | A venue-rejected OHLCV probe is a configuration problem, not an outage. |
| 0052 | `e4789f4b` | 60 | funding_context_price_join.py + 2 research scripts | Funding/price join reports coverage and fails on a stale archive. |
| 0053 | `58c49840` | 61 | crypto_edge_store_sqlite.py, crypto_edge_context.py | Capture time and row identity validated; future-dated funding context refused. |
| 0054 | `986817a9` | 62 | edge_cadence.py, check_edge_cadence.py, crypto_edge_collector_service.py | Cadence check reads collector rows only and reports holes; collector stores families independently. |

Check or decide:

- 0054 changes the cadence check's default to collector rows only (`--source any` restores the old view).
- Finding recorded, not a code matter: funding_extreme thresholds were never reached in the laptop archive.

### 12. Labels, tests, CI

No trading behaviour.

| Patch | Commit | Folder | Production files | Change |
|---|---|---|---|---|
| 0064 | `520f1153` | 72 | config_manager.py, preflight.py, settings_view.py, 70_Settings.py | Preset and Settings risk values are labelled as stored, not enforced. |
| 0066 | `07fd078e` | 74 | (tests/conftest.py only) | Test suite runs in a temporary state directory; fails if real operator files change. |
| 0048 | `5ea94373` | 56 | (tests only) | End-to-end paper pipeline test, queued intent to the gate's figures. |
| 0061 | `ad7b13e7` | 69 | .github/workflows/ci.yml | Slow-marked tests run in required CI. Changes required CI; not run on GitHub. |

Check or decide:

- 0066 should be applied before anyone runs the suite on a host with real state.

## Decisions I took that are yours to confirm

| Patch | Decision | Alternative |
|---|---|---|
| 0070 | Symbol lock refuses buys only at the boundary | Refuse both sides, as the legacy executor does |
| 0071, 0072 | A refused or unbuildable intent is final | Return it to the queue for a later attempt |
| 0071 | Refusals and router rejections give the daily claim back | Count every attempt against the day |
| 0068 | `make paper-stop-now` stops one campaign | Keep the machine-wide stop as the default |
| 0056 | An enabled AI/probability gate that cannot evaluate refuses | Let the order through, as before |
| 0054 | Cadence check counts collector rows only by default | Count every source |
| 0065 | A drift or journal-loss flag needs `--force-clear --reason` | Keep clearing on a clean replay |

## How to check a patch yourself

```
git checkout <commit>            # from the table
PYTHON=<venv python> PYTHON_BIN=<venv python> <venv python> -m pytest -q tests/<test named in the folder README>
git stash push -- services scripts storage   # on the commit, to see the test fail on the previous code
```

Each folder README names the tests and how many fail on the previous code.

## Not in any patch

- Which live path runs and what feeds it: nothing produces live orders today.
- The test-written files on the laptop (order-block flag from 2026-09-23, test
  rows in the operator-event journal and outcome file).
- Open decisions listed in docs/research/backlog_completion_map_20261005.md.
