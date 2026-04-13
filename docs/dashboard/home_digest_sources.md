# Home Digest Source Mapping

The Home Digest is an operator-facing summary surface. Page code should consume the section payloads built in `<your-repo-path>/dashboard/services/home_digest.py` and should not recompute ranking, safety, or freshness logic in UI code.

## Section Mapping

### Runtime Truth Strip
- Builder: `build_runtime_truth_digest(...)`
- Upstream sources:
  - `<your-repo-path>/services/config_loader.py` merged runtime trading config overlaying `<your-repo-path>/.cbp_state/runtime/config/user.yaml` on `<your-repo-path>/config/trading.yaml`
  - `<your-repo-path>/services/bot/start_manager.py`
  - `<your-repo-path>/services/admin/live_guard.py`
  - `<your-repo-path>/services/execution/live_arming.py`
  - `<your-repo-path>/dashboard/services/crypto_edge_research.py`
- Notes:
  - Runtime mode truth is driven by the merged runtime config, not the legacy file alone.
  - Live-order authority remains conservative and reflects current guard posture, not a deep end-to-end live self-test.

### What Needs Attention Now
- Builder: `build_attention_now_digest(...)`
- Upstream sources:
  - Overview summary input from `<your-repo-path>/dashboard/services/view_data.py`
  - Operations snapshot from `<your-repo-path>/dashboard/services/operator.py`
  - Structural freshness/digest summaries from `<your-repo-path>/dashboard/services/crypto_edge_research.py`
- Sorting:
  - severity first
  - then recency at digest-build time

### Strategy Leaderboard Summary
- Builder: `build_leaderboard_summary_digest(...)`
- Upstream sources:
  - `<your-repo-path>/dashboard/services/strategy_evaluation.py`
  - `<your-repo-path>/services/backtest/leaderboard.py`
- Persisted-artifact row metadata may also include:
  - `<your-repo-path>/services/backtest/evidence_cycle.py` row-level `strategy_feedback`
  - `<your-repo-path>/services/backtest/evidence_cycle.py` row-level `feedback_weighting`
- Notes:
  - Current leaderboard is synthetic and built on demand from preset candidates.
  - The digest does not persist leaderboard history yet.
  - When persisted strategy evidence exists, row caveats may include research-only paper-feedback and feedback-weighting summaries to explain why the ranking moved.

### Scorecard Snapshot
- Builder: `build_scorecard_snapshot_digest(...)`
- Upstream sources:
  - `<your-repo-path>/services/backtest/scorecard.py`
  - `<your-repo-path>/services/backtest/leaderboard.py`
- Notes:
  - Highlights are derived from current synthetic benchmark rows.
  - `most_changed` is intentionally unavailable because persisted delta summaries do not exist yet.

### Crypto-Edge Freshness Summary
- Builder: `build_crypto_edge_summary_digest(...)`
- Upstream sources:
  - `<your-repo-path>/dashboard/services/crypto_edge_research.py`
  - `<your-repo-path>/storage/crypto_edge_store_sqlite.py`
- Notes:
  - Missing rows mean no stored live-public snapshot is available.
  - Missing data does not imply the module is unsupported.

### Safety / Risk Warnings
- Builder: `build_safety_warnings_digest(...)`
- Upstream sources:
  - `<your-repo-path>/services/admin/live_guard.py`
  - `<your-repo-path>/services/bot/start_manager.py`
  - Overview summary risk warnings
  - Structural freshness summary
- Notes:
  - The section stays conservative and does not imply unsupported live capability.

### Freshness & Staleness Panel
- Builder: `build_freshness_panel_digest(...)`
- Upstream sources:
  - Collector runtime summary
  - Latest live structural-edge snapshot
  - Synthetic leaderboard/scorecard build time
  - Operations health timestamp
- Notes:
  - Paper PnL timestamp is not yet exposed upstream, so the digest reports it as missing.

### Mode Truth Card
- Builder: `build_mode_truth_digest(...)`
- Upstream sources:
  - `<your-repo-path>/services/config_loader.py` merged runtime trading config overlaying `<your-repo-path>/.cbp_state/runtime/config/user.yaml` on `<your-repo-path>/config/trading.yaml`
  - `<your-repo-path>/services/bot/start_manager.py`
  - `<your-repo-path>/services/execution/live_arming.py`
- Notes:
  - This section explains what is allowed and blocked right now.
  - It is explicit about paper-heavy defaults and promotion blockers.

### Recent Incidents / Operational Notes
- Builder: `build_recent_incidents_digest(...)`
- Upstream sources:
  - Overview active warnings
  - Collector runtime summary
  - Operations snapshot
- Notes:
  - Current incidents are synthesized from existing summaries.
  - There is no dedicated persisted incident/event stream yet.

### Next Best Action
- Builder: `build_next_best_action_digest(...)`
- Upstream sources:
  - `attention_now`
  - fallback to `leaderboard_summary`
- Notes:
  - The current recommendation is intentionally conservative.
  - When the digest falls back to `leaderboard_summary`, the top row caveat may carry persisted research-only strategy-feedback and feedback-weighting rationale into the action explanation.
  - It does not imply that any strategy is validated for promotion.

## Missing Upstream Summaries

The digest now has explicit placeholders/caveats for these gaps:

1. Persisted leaderboard age / change history
- Current behavior: synthetic on-demand build only
- Effect: leaderboard age is shown as `Just Built` with caveat

2. Persisted scorecard delta summary
- Current behavior: no historical comparison stream
- Effect: `most_changed` is explicitly unavailable

3. Paper PnL freshness timestamp
- Current behavior: portfolio value exists, but no digest-safe timestamp is exposed
- Effect: freshness panel shows `Missing`

4. Dedicated incident stream
- Current behavior: incidents are synthesized from warnings/runtime summaries
- Effect: recent incidents stay conservative and compact

5. Universal copilot provenance strip
- Current behavior: home summaries and some structural freshness surfaces expose provenance/freshness, but answer-level strips are not universal yet
- Effect: runtime truth marks the Copilot trust layer as `Partial`
