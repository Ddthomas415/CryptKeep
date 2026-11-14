# Exit-unblocked variants of the three default strategies: specification for engineering item 4

Bot relation: BOT_RULES; runtime configuration not checked. Dated source-stage correction below; original proposal retained.

Claude (Cowork), 2026-11-14. Owner direction 2026-11-14 ("take care of it", after Claude named eng 4 as the next
priority task). Engineering item 4 in `docs/PROJECT_STATE.md` (owner-approved 2026-10-30, priority 1 of the new work;
reaffirmed 2026-11-13T19:54:08Z: "isolated offline variants with defaults unchanged"). This document resolves the scope
gap the queue entry leaves open ("say which exits each variant tests") and gives Codex a bounded implementation and
test plan. Self-checked; Codex verifies before building. No code, config, preset or runtime was changed for this
document.

## 1. The defect, as it stands in HEAD (SHOWN, 2026-11-14, HEAD 3b49ead3f)

Each default signal function decides `buy`/`sell` first, then applies the same filter block to whichever action it
produced. A `sell` that fails any entry-quality filter becomes `hold`, so the position is not closed by the signal.

| Strategy | File (sha256 prefix) | Decision | Filters applied to sell too | Filter values from the default preset |
|---|---|---|---|---|
| Breakout | `services/strategies/breakout_donchian.py` (5de5765593c9) | lines 38-43 | lines 65-76: volatility, volume, chop, channel width, directional confirmation (75-76 is sell-specific) | `presets.py` 104-109 |
| EMA cross | `services/strategies/ema_cross.py` (68b3522c816b) | lines 87-92 | lines 119-126: volatility, volume, chop, cross gap | `presets.py` 36-39 |
| Mean reversion | `services/strategies/mean_reversion_rsi.py` (63d125e3ec91) | lines 36-41 | lines 63-74: volatility, volume, one-way trend, SMA distance, reversal confirmation (73-74 is sell-specific) | `presets.py` 71-75 |

The registry (`services/strategies/strategy_registry.py`, db4cc349310eac07, lines 100-152) passes the preset's
strategy block through to these functions. The runner (`services/execution/strategy_runner.py`, b7beecd23a9ec6ba)
enters on signal change and checks its own exit stack every loop while long: stop 3%, trailing 2%, take-profit 6%,
60 candles (code defaults, lines 1163-1166; order in `services/risk/exit_controls.py` lines 53-54).

Prior records (not new): breakout exit filtering documented 2026-09-23 (`breakout_economic_dissection_2026_09_23.md`,
28 of 42 trades); isolated comparison tool on branch `codex/breakout-exit-treatment` (909239e48, present locally,
reviewed, shelved for lack of contiguous data; models no runner exit stack); all three strategies in
`failure_diagnosis_20261030/` (blocked exits: breakout 28 = 9%, EMA 77 = 60%, mean reversion 28 = 97% of trades;
exiting at the first blocked signal would have changed before-fee profit by -$15, +$28, +$65 respectively, signal-only,
OKX hourly, 5 coins, $100 per trade; the dollar estimates were corrected by Codex on 2026-11-03 and are indicative, not
established); the runner's EMA invalidation exits are inert (`exit_parity_audit_20261031/` C4). Patch 0004 (multi-coin
runner) is a separate defect and is not part of this item.

## 2. Design: one parameter, three new presets, defaults byte-identical

- Add one keyword to each of the three `signal_from_ohlcv` functions: `filters_apply_to_sell: bool = True`.
  When `False` and `action == "sell"`, return the sell before the filter block (that is, immediately after the
  `if action == "hold"` return). Buys are filtered exactly as now. `raw_action`/`raw_reason` observer output is unchanged.
- Registry: pass `filters_apply_to_sell=bool(st["filters_apply_to_sell"])` only when the key is present in the
  strategy block, so the defaults' call signature is unchanged.
- Presets: add `breakout_exit_unblocked`, `ema_cross_exit_unblocked`, `mean_reversion_exit_unblocked`, each a deep copy
  of its default with the single extra strategy key `"filters_apply_to_sell": False`. Same `name`, so
  `_resolved_exit_controls`'s preset-identity check (runner lines 458-466) passes. The three default preset entries,
  the signal functions' behaviour for existing callers, and the runner are otherwise unchanged.
- Decision recorded here (Codex may object with evidence): the variant bypasses **all** post-decision filters for sells,
  including the sell-specific confirmation lines (breakout 75-76, mean reversion 73-74). This is the failure diagnosis's
  pre-registered hypothesis ("sell signals bypass the entry filters, with nothing else changed") and the 2026-09-23
  tool's arm 2 ("allowed to sell regardless of entry-quality filters"). A partial bypass would be a fourth variant,
  not approved.

## 3. Which exits each variant tests (the scope gap)

Both, as two arms per strategy, reported side by side. Reason: the frozen paper spec runs the defaults with the
runner's code-default exit stack (`paper_simulation_spec_20261031/README.md` line 53), and the exit-parity audit
showed the stack changes every strategy's result (trailing 2% closes most trades within hours). A signal-only result
alone would not predict the bot.

| Arm | Entries | Exits | Mirrors |
|---|---|---|---|
| S (signal only) | every buy signal while flat | signal sell only | `failure_diagnosis_20261030/diag_trades.py`; `exit_parity_replay.py` scenario A (`entry_rule='level'`, `stack_mode=None`) |
| R (runner rules) | signal change only, completed candles | runner stack (stop 3%, trailing 2%, TP 6%, 60 bars) then signal sell | `exit_parity_replay.py` scenario C_path (`entry_rule='transition'`, `stack_mode='path'`, lines 212) |

Each arm runs default vs variant on identical data; the only difference between the two runs is
`filters_apply_to_sell`. Pre-registered expectations from the diagnosis (signal-only): EMA cross and mean reversion
improve before fees, breakout does not; trade counts rise for all three (unblocked sells re-arm entries). A
result is reported, not promoted: no variant goes to paper or live without owner approval.

## 4. Offline tests (no market data run; the archive already exists)

Data: `research/multisymbol_baseline_v1/public_archive.sqlite` (OKX hourly; BTC, ETH, SOL, ADA, XRP; 2026-01-01 to
09-30; frozen, `dataset.freeze.json`). Costs as in the diagnosis: 0.50% per side plus 5 bps slippage, next-bar open.

1. Unit tests (new `tests/test_exit_unblocked_variants.py`): for each strategy, a sell with each filter failing in turn
   is returned when `filters_apply_to_sell=False` and becomes `hold` when `True`/absent; a buy failing the same filter is
   `hold` in both; each `*_exit_unblocked` preset equals its default plus the one key; the three default preset dicts
   are byte-identical to HEAD (hash of `json.dumps(sort_keys=True)` recorded in the test).
2. Default parity on the archive: action sequences for the three defaults, before and after the code change, identical
   for all 5 coins (reuse `exit_parity_replay.py`'s `actions_for`). This is the "defaults unchanged" proof.
3. Variant replay: extend `exit_parity_replay.py` (copy into this folder; do not alter the frozen audit copy) with the
   new kwarg; run arms S and R for default and variant; write `exit_variants_result.json` and per-trade CSVs with
   SHA256SUMS. Report per strategy and arm: trades, net $ after costs, blocked-exit count (variant must be 0), max
   drawdown, in-market share.
4. Independent review (Nash) of the source diff and the replay result; `git diff --check`; no commit or push.

Stopping point: source proof plus replay result plus one independent review. Anything further (a paper account for a
variant, inclusion in the 25-symbol comparison or the frozen simulation) is a separate owner decision.

## 5. Out of scope
Tuning any threshold; new exit rules; changing the runner's exit stack or entry latch; touching the paper simulation's
frozen presets or manifests; the inert EMA invalidation exits (C4); patch 0004.

## 6. What could change the owner's decision
The variant can only sell on a downside signal that the strategy already produces; mean reversion's "no loss exit"
(RSI must reach 70 above the SMA) is not fixed by unblocking, only the runner's stop/trailing cover it. Arm R therefore
matters more than arm S for the bot's actual behaviour. Trade counts and fees will rise; the net effect is the question.

## 7. Dated correction and source implementation boundary - Codex, 2026-11-14T16:51Z

- SHOWN: the original paragraph's -$15/+$28/+$65 estimates were **WITHDRAWN**, not established or merely indicative.
  See `failure_diagnosis_20261030/README.md` November 3 correction: the original calculation did not value the price
  difference at the original position quantity. Section 3's expectation of economic improvement is an untested
  hypothesis, not evidence; even higher trade counts are not guaranteed. The original text above is retained to make
  the correction visible, not endorsed.
- SHOWN: the source path also includes `services/strategies/config_tools.py`; its Boolean allowlists must preserve
  the new flag for runner preset resolution. The initial design omitted this necessary integration boundary.
- Independent review of the first draft found Boolean coercion could opt in with malformed configuration. Revised
  contract: only literal Boolean `False` bypasses SELL filters. The parser rejects a present non-Boolean flag;
  the registry preserves its type and direct signal calls bypass only on `is False`. Other Boolean fields are unchanged.
- Current increment implements and verifies source and synthetic behavior only; the historical default-parity test
  and S/R archive comparison in section 4 remain **NOT DONE**. No historical data was opened or run in this increment.
  Do not call all of item 4 complete. A subsequent approved historical replay must preserve the specified arms,
  dataset, sizing, costs and outputs; no new strategy search or tuning is implied.
- Arm R is a completed-candle model using an assumed intrabar price path, not current runtime parity or executable
  fill evidence. The runner's forming-candle behavior, actual configuration and fills were not inspected here.
- Evidence, hashes, test command, reviewer findings and unresolved questions:
  `docs/review_artifacts/exit_unblocked_variants_20261114/README.md`.

What do I know that could change the owner's decision that I have not yet said? A source-correct opt-in exit is not
an established financial improvement; earlier dollar expectations cannot justify promotion or live/paper selection.

## 8. Historical stage completed - 2026-11-14T17:13Z

The owner subsequently approved the next recommended historical stage. One unchanged-contract run finished
at17:07:49Z; no retry, new data or tuning. All five frozen prefixes,98,280 before/current default output comparisons,
BUY parity, zero variant-filtered SELLs and15 saved signal-only trade-ledger comparisons passed. Both S/R arms
and50/90bps fees were reported for every symbol, with5bps slippage, correct quantity/fee accounting, bar-close
drawdown and exposure bounds. All60 unblocked cases lost net quote currency; S five-sleeve totals worsened and
R totals improved only slightly while remaining negative. Original expectations are not promotion evidence.

Separate Nash17:12:59Z ACCEPTED_WITH_RISK for historical comparison/reporting; source/offline requirements of
engineering item4 are complete within the documented model limits. See `HISTORICAL_COMPARISON.md`,
`HISTORICAL_REVIEW.md` and `historical_20261114T1706Z/`. Original source-stage NOT DONE statements above describe
the earlier boundary, not current historical status. No paper/live use, configuration, deployment or R10 change.

What do I know that could change the owner's decision that I have not yet said? Correctly returning SELL does
not by itself make a strategy profitable; this fixed historical comparison gives no reason to promote the variants.

## 7. Measured result, 2026-11-14T18:41Z (added by Claude; see `RESULTS.md`)
The measurement half of sections 3-4 was run without a production change, using the signal functions' existing
`observer` hook to recover the raw sell before the filters (`exit_variants_replay.py`; default arm reproduces the saved
baseline 15 of 15). Under the bot's rules (arm R) the variant changes net results by +$1 to +$3 per strategy over nine
months and five coins; signal-only (arm S) it trades more and loses more after fees in all three strategies. The
pre-registered "at least as good" expectation is not met in arm S. Whether Codex still builds the production parameter
and presets (section 2) is the owner's decision; this document's sections 1-6 are unchanged.

### Dated handoff clarification - Codex, 2026-11-14T22:38:11Z

SHOWN in the current checkout: the three opt-in parameters/presets already exist and received separate source
acceptance at16:53:05Z, followed by historical comparison acceptance at17:12:59Z (work-log closeout17:15:22Z).
The preceding question about whether they still need building is therefore stale for this checkout. Preserve
Claude's separate replay as additional evidence, not authority to repeat implementation, promote a variant or
reopen the accepted source task. This clarification does not independently certify Claude's separate script or
its original workspace visibility; it changes no strategy, result or owner restriction.

What do I know that could change the owner's decision that I have not yet said? The current next-step boundary
is the separately paused 25-symbol protocol, not an unimplemented exit parameter.
