# Runtime Check - 2026-08-30

## Scope

Operational check-in for the current local checkout, local paper campaigns,
local crypto-edge collector loop, paper gate progress, operator briefing, and
Hetzner paper/runtime/dependency status.

No strategy config, promotion gate, trading logic, live execution, order
routing, package installation, deployment, or service restart was changed.

One local research-only background loop was restarted through the accepted
OPERATOR control path:

- `dashboard.services.operator.start_crypto_edge_collector_loop(...)`
- script: `scripts/data/run_crypto_edge_collector_loop.py`
- source: `live_public`
- execution boundary: `execution_enabled=false`, `research_only=true`

## Local Repo

Commands:

```bash
git status --short --branch
gh pr list --state open --json number,title,headRefName,baseRefName,mergeStateStatus,statusCheckRollup
./.venv/bin/python scripts/validate.py --quick
```

Result:

- SHOWN: local checkout was clean before this checkpoint branch:
  `## master...origin/master`.
- SHOWN: open PR list was empty: `[]`.
- SHOWN: local quick validation completed with `validate OK`.
- SHOWN: quick validation included repo doctor, alignment guard tests, and quick
  pytest subset.

## Local Paper Campaigns

Command:

```bash
make status-paper-campaigns
```

Result:

- SHOWN: `all_running=true`.
- SHOWN: `running_count=2`.
- SHOWN: `es_daily_trend_v1` is running and idle with reason
  `waiting_for_next_day`.
- SHOWN: `es_daily_trend_v1` last completed day is `2026-08-30`.
- SHOWN: `es_daily_trend_v1` totals: `fills_total=20`,
  `closed_trades_total=10`, `net_realized_pnl_total=31.4368625683357`.
- SHOWN: `breakout_default` is running and idle with reason
  `waiting_for_next_day`.
- SHOWN: `breakout_default` last completed day is `2026-08-30`.
- SHOWN: `breakout_default` totals: `fills_total=23`,
  `closed_trades_total=11`, `net_realized_pnl_total=4.218297332061334`.

## Local Paper Gate

Command:

```bash
make status-paper-gate-qualification-json
```

Result:

- SHOWN: policy is `slow_daily_single_symbol_v1`.
- SHOWN: cohort start is `2026-06-16T00:00:00Z`.
- SHOWN: required thresholds are `45` calendar days, `60` qualified bars, and
  `5` provenance-qualified round trips.
- SHOWN: qualified round trips are `3/5`, with `2` remaining.
- SHOWN: counted evidence fills are `6`.
- SHOWN: excluded pre-cohort evidence fills are `10`.
- SHOWN: latest completed qualified round-trip close timestamp is
  `2026-07-09T00:04:00.377830+00:00`.
- SHOWN: no missing journal order IDs were reported.

## Local Crypto-Edge Collector

Commands:

```bash
make status-live-crypto-edges-loop
./.venv/bin/python scripts/data/run_crypto_edge_collector_loop.py \
  --plan-file sample_data/crypto_edges/live_collector_plan.json \
  --interval-sec 300 \
  --max-loops 1
./.venv/bin/python -c 'from dashboard.services.operator import start_crypto_edge_collector_loop; print(start_crypto_edge_collector_loop(interval_sec=300, current_role="OPERATOR"))'
make check-edge-cadence-json
```

Result:

- SHOWN: initial managed collector status was `dead`.
- SHOWN: initial managed collector reason was `process_not_running`.
- SHOWN: previous status PID `81461` was not alive.
- SHOWN: a one-loop foreground run completed successfully with
  `status=stopped`, `reason=max_loops`, `loops=1`, `writes=1`, and
  `errors=0`.
- SHOWN: the one-loop run collected OKX funding, open interest, basis,
  Coinbase/Kraken quotes, and Coinbase order book data.
- SHOWN: detached raw shell launches did not persist; the supported OPERATOR
  control path was then used.
- SHOWN: supported OPERATOR launch returned
  `started pid=73735 script=scripts/data/run_crypto_edge_collector_loop.py`.
- SHOWN: final collector status is `running`.
- SHOWN: final collector PID is `73735`.
- SHOWN: final collector `pid_alive=true`.
- SHOWN: final collector wrote `loops=1`, `writes=1`, `errors=0`.
- SHOWN: final collector capture timestamp is `2026-08-30T08:07:38+00:00`.
- SHOWN: final collector payload has `execution_enabled=false` and
  `research_only=true`.
- SHOWN: edge cadence check reported `ok=true`, with funding, open interest,
  and basis fresh.

## Operator Briefing

Commands:

```bash
make operator-briefing-json
make record-operator-briefing
```

Result:

- SHOWN: operator briefing is advisory-only and read-only.
- SHOWN: campaign summary reported `campaigns=2/2 all_running=True`.
- SHOWN: paper gate summary reported `paper_gate_round_trips=3/5 remaining=2`.
- SHOWN: cost assumptions overall status is `warning`.
- SHOWN: top recommendation is to keep the current paper gate running under the
  approved provenance policy.
- SHOWN: the briefing artifact was written through the repo target.

## Roadmap And Research Status

Commands:

```bash
make backlog-lane-status-json
make research-pipeline-status-json
make research-command-status-json
make research-artifact-inventory
make roadmap-tracking-status-json
make funding-threshold-research-pipeline
make price-action-research-pipeline
```

Result:

- SHOWN: backlog lane status reported `ok=true`.
- SHOWN: backlog lane counts were `15` passive/operator evidence items, `7`
  low-risk docs/tests items, `7` medium-risk runtime/read-only items, and `7`
  high-risk gate/execution/deploy items.
- SHOWN: research pipeline status reported `ok=true` with `2` wired pipelines
  and `2` latest OK pipelines: `funding_threshold` and `price_action`.
- SHOWN: research command status reported `ok=true` with `20` wired commands and
  `0` not wired commands.
- SHOWN: research artifact inventory reported `ok=True`, `artifacts=14`,
  `missing=0`, `latest_ok=13`, `latest_not_ok=0`, and `action_required=0`.
- SHOWN: roadmap tracking reported `ok=true`, all `13` roadmap-listed commands
  exist in `Makefile`, and all `12` linked source docs exist.
- SHOWN: funding-threshold research pipeline reran after the local crypto-edge
  collector restart and reported `ok=true`.
- SHOWN: latest funding-threshold pipeline output directory was
  `.cbp_state/data/research/funding_threshold_pipeline/20260830T081716Z`.
- SHOWN: latest funding price-join had `279` joined rows.
- SHOWN: latest funding candidate triage and stability triage both returned
  `review_candidates=[]`.
- SHOWN: this pipeline output is marked research-only, not campaign evidence,
  not promotion evidence, not strategy config, and not execution input.
- SHOWN: price-action research pipeline reran and reported `ok=true`.
- SHOWN: latest price-action output directory was
  `.cbp_state/data/research/price_action_pipeline/20260830T081822Z`.
- SHOWN: latest price-action candidate triage returned `15`
  `candidate_for_manual_review` rows.
- SHOWN: top latest price-action candidate was `opening_range_state:inside`
  long with `avg_delta_vs_unconditioned_pct=0.12745632891795666`,
  `outperform_window_ratio=1.0`, `sample_size=44`, and `window_count=3`.
- SHOWN: next latest candidates included `break_and_retest:bearish_hold` long,
  `fair_value_gap:bearish` long, `break_and_retest:bearish_rejected` short,
  and `opening_range_state:forming` short.
- SHOWN: price-action pipeline output is marked research-only, not campaign
  evidence, not promotion evidence, not strategy config, and not execution
  input.

## Funding Stage 0 Readiness

Commands:

```bash
make crypto-edge-strategy-readiness
make check-short-context-readiness
make funding-stage0-readiness
```

Result:

- SHOWN: crypto-edge strategy readiness reported `ok=true`.
- SHOWN: `funding_extreme` status was `stage0_wired_research_only`.
- SHOWN: `open_interest_shift` remained `config_only_research_placeholder`.
- SHOWN: `order_book_imbalance` remained `signal_module_unregistered`.
- SHOWN: short-context readiness reported `status=live_public_ready`.
- SHOWN: short-context readiness had live-public rows for funding, open
  interest, basis, quotes, and order book families.
- SHOWN: the sandboxed run failed the public OHLCV preflight with
  `status=ohlcv_source_unreachable` for Coinbase `BTC/USDT` `public_ohlcv_5m`.
- SHOWN: rerunning the same read-only readiness command with network access
  returned `status=ready_for_operator_stage0`.
- SHOWN: final readiness had `blocking_checks=0`.
- SHOWN: edge cadence and funding context checks were ready.
- SHOWN: the generated Stage 0 command uses challenger state dir
  `.cbp_state_challengers/funding_extreme_default` and does not use
  `--daily-loop`.
- SHOWN: the funding Stage 0 verifier still failed against older evidence
  because the latest completed session commit was `1920d13b0`, while the
  verifier expected `fd7f11e9c`.
- SHOWN: after readiness passed, the one-shot 15-minute proof command was
  started for `funding_extreme_default`; this checkpoint does not record its
  terminal result.

## Hetzner Paper Campaign

Command:

```bash
make status-paper-hetzner
```

Result:

- SHOWN: Hetzner paper campaigns are `1/1` running.
- SHOWN: `ema_cross_default` is idle with reason `waiting_for_next_day`.
- SHOWN: strategy is `ema_cross`.
- SHOWN: fills are `16`.
- SHOWN: closed trades are `8`.
- SHOWN: net PnL is `-2.3183`.
- SHOWN: latest fill is `2026-08-29T00:02:44.159494+00:00`.

## Hetzner Crypto-Edge Runtime

Command:

```bash
make status-hetzner-edge-runtime
```

Result:

- SHOWN: status is `hetzner_crypto_edge_runtime_ready`.
- SHOWN: `ok=True`.
- SHOWN: remote branch is `master`.
- SHOWN: remote head is `d3b46e3c2f0541c20897f78739ce071c637d9647`.
- SHOWN: `blocking_checks=0`.

## Hetzner Dependency Alignment

Command:

```bash
make status-hetzner-dependency-alignment-json
```

Result:

- SHOWN: status is `hetzner_dependency_alignment_ready`.
- SHOWN: `ok=true`.
- SHOWN: remote checkout branch is `master`.
- SHOWN: remote checkout commit is
  `d3b46e3c2f0541c20897f78739ce071c637d9647`.
- SHOWN: remote git is clean.
- SHOWN: pin integrity is OK with `pin_count=83`.
- SHOWN: environment alignment is OK with `checked=83`,
  `mismatches=[]`, and `not_installed=[]`.
- SHOWN: pip dry run reported `no_changes`.
- SHOWN: no deploy, pip install, or service restart was invoked.
- SHOWN: vulnerability audit was not run: `reason=not_requested`.

## Remaining

- Paper gate is still blocked by qualified round trips: `3/5`, `2` remaining.
- Local crypto-edge collector is running again and should be monitored by
  `make status-live-crypto-edges-loop` and `make check-edge-cadence-json`.
- Host vulnerability audit remains unrun and still requires explicit approval
  or waiver before it can close release-policy proof.
- Host-side operator/platform event proofs remain open until real host journals
  exist and are scanned.
- Capped-live proof items remain deferred.

Acceptance state: `INCOMPLETE`.
