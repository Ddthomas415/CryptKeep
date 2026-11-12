# Whole-bot audit for flaws (research item 1): simulation path first

Bot relation: audit of the bot's own code (not a strategy result).
Owner direction 2026-10-31. Claude, read-only on the repository (probes run on a copy in the Linux shell's home with a
temporary state directory). **Self-checked; Codex to verify.** Budget: three sessions for the simulation path;
all three are below. The simulation-path audit is complete; the rest of `services/` is not audited. Searches for earlier work: `capital_protection_audit_20261031/`, `exit_parity_audit_20261031/`,
`integrity_audit_20261015/`, the Hetzner paper tooling (`scripts/*paper*`), the July 2026 audit (chat summary).

| Area | Status |
|---|---|
| Paper engine (fills, fees, cash, positions, profit) | Session 1: done below |
| Paper runner (intent consumption) | Session 1: rejection handling done below |
| Market data (candles, quotes, staleness) | Session 2: done below |
| The three default strategies' signal code | Session 2: done below (exit filters already known: failure diagnosis) |
| Restart and recovery on the paper path | Session 3: done below |
| Monitoring and alerts | Session 3: done below |
| Runner decisions and exits | Done in earlier audits (D-1, CP-09, C-06); session 3 adds the kill cooldown (BA-16), which those audits missed |

## Session 1 findings
| ID | Finding | Evidence | Severity (simulation) | Owner | Disposition |
|---|---|---|---|---|---|
| BA-01 | Market orders fill at the mid price plus configured slippage, never at the ask (buy) or bid (sell). In the probe (bid 99 / ask 101, then 109 / 111) the engine booked +$44.75 on a round trip that is +$39.27 at the quoted prices. | SHOWN by reading (`paper_engine.py` 396-401) and by running (probe P-3) | HIGH | Codex | Fix, or record bid/ask at every fill (spec item 1) |
| BA-02 | The runtime config charges 7.5 bps fees and 5 bps slippage on paper; the account's taker fee is 50 bps. | SHOWN (whitelisted config read) | HIGH | Owner (decided: 50 bps) | Set per account (spec) |
| BA-03 | Accounting is correct by its own rule: fee-inclusive average cost; cash, quantity and realized profit match hand arithmetic to the cent. | SHOWN by running (probe P-3) | Control present | - | - |
| BA-04 | Every paper order is refused unless the system-status snapshot is fresh, the master read-only flag is off, market quality passes and the safety gates allow it. Without the snapshot publisher running, the bot trades nothing. | SHOWN by running (first probe run: `staleness:snapshot_missing`) and reading `_pre_submit_gate` | HIGH (operational) | Codex | Run the publisher; alert on refusals (spec item 6) |
| BA-05 | A refused or rejected intent is final: `paper_runner.py` marks it rejected and the runner does not re-send the same action, so a missed exit stays missed while its condition lasts. | SHOWN by reading (`paper_runner.py` 140-215; runner line 1512) | HIGH | Codex | Record and alert (spec item 7); fix with CP-09 |
| BA-06 | Positions and cash are kept per state directory and per symbol, not per strategy: two strategies in one state directory would share a position. | SHOWN by reading (`paper_trading_sqlite.py` apply_fill) | MEDIUM | Codex | One state directory per account (spec) |
| BA-07 | Fills are whole and immediate (no partial fills, no order-book depth). | SHOWN by reading | LOW at $1,000 | - | Note |

Probe P-3 (`probes/test_probe_paper_engine.py`): the real `PaperEngine` with fixed quotes; its submit gates are
replaced only to test the accounting. Rerun from the repository root:
`CBP_STATE_DIR=$(mktemp -d) python -m pytest -p no:cacheprovider -q -s -o addopts="" docs/research/bot_audit_20261031/probes/`

## Session 2 findings: market data and the three strategies' signal code
Scope: `strategy_runner.py` (sha256 7006466d...) `public_ohlcv_*` branch (lines 813-907, 1180-1290), the signal
functions `ema_cross.py`, `mean_reversion_rsi.py`, `breakout_donchian.py`, `indicators.py`, `market_filters.py`,
`strategy_registry.py`, the default presets, and ccxt 4.5.48 `coinbase.fetch_ohlcv`. Searches for earlier work:
failure diagnosis 2026-10-30 (exit filters), PROJECT_STATE caveat C-06 (forming candle), the exit-parity replay
(60-bar window, variant C_path_w60), the review handoff, `docs/audit_artifacts/`.

| ID | Finding | Evidence | Severity (simulation) | Owner | Disposition |
|---|---|---|---|---|---|
| BA-08 | **The volume filter reads the still-forming hourly candle** (consequence of C-06, not recorded before). `market_context` divides the last candle's volume by the previous 7; with `public_ohlcv_1h` the last candle is the current hour, so its volume is only part of an hour's. Holding prices fixed and scaling only that volume, the share of the strategies' signals that still pass at 25% / 50% / 75% / 90% of the hour: EMA cross buys 18 / 51 / 80 / 90%, sells 14 / 47 / 79 / 91%; mean reversion buys 7 / 18 / 66 / 90%, sells 1.5 / 13 / 54 / 82%; breakout buys 23 / 67 / 89 / 96%, sells 24 / 67 / 90 / 97%. Entries and signal exits therefore mostly wait until late in the hour, and a cross or breakout that reverses before the hour's volume builds up never fires (for EMA cross the signal exists only in the hour of the cross). | SHOWN by reading (`market_filters.py` 41-43) and by running (probe P-4; OKX hourly candles, BTC/ETH/SOL, 6,852 hours each; volume assumed to build evenly through the hour) | MEDIUM (parity with research on completed candles) | Codex / Claude | Do not change during the run; record the minute of the hour of every signal and fill (spec) |
| BA-09 | **The entry filters remove most of the strategies' own exit signals** (already known: failure diagnosis 2026-10-30, C1-C2; counted here on the bot's 60-candle window). Completed hours: EMA cross keeps 128 of 360 cross-down sells (removed: low volume 155, cross gap 50, chop 22, low volatility 5); mean reversion keeps 67 of 1,160 overbought hours (removed: low volume 466, no reversal 376, high volatility 156, too far from average 68, trend 27; counted per hour, and an overbought spell lasts several hours, so fewer exits are lost than hours); breakout keeps 680 of 727 (removed: low volume 45, low volatility 2). A position whose exit signal was removed leaves by stop, trailing stop, take-profit or the 60-hour limit. | SHOWN by running (probe P-5) | MEDIUM (known; the exit-parity replay already includes it) | Owner / Codex | Do not change during the run (it would change the strategy); fix decision after, with ED-002 exit scope |
| BA-10 | **A failed candle fetch skips the whole decision, exits included.** On an exception or empty reply `_fetch_public_ohlcv` returns no rows and the runner sleeps and continues (lines 1194-1203) before stops, trailing stops or signals are evaluated; stops exist only in the bot, not on the exchange. | SHOWN by reading | MEDIUM on paper (missed decisions); HIGH before live | Codex | Record every skipped loop with its reason; alert on runs of failures (spec) |
| BA-11 | **Request rate.** Every loop fetches 300 hourly candles (ccxt caps the bot's `max_bars` 400 at 300), and the loop sleeps `loop_interval_sec`, default 1 second (lines 367, 1814): about one request per second per process for a decision that changes once an hour. 9 accounts make up to about 9 requests per second from the server's address, 18 with Group B, plus the data collector. A limit of 10 public requests per second per IP is commonly cited for Coinbase Advanced Trade (CLAIMED by a third-party summary; not verified against Coinbase's documentation). Over the limit, fetches fail and BA-10 applies. | SHOWN (code, ccxt source); limit UNVERIFIED | MEDIUM | Codex | Set `loop_interval_sec` in the spec (15 s) and count HTTP 429 replies |
| BA-12 | **An unbounded debug file.** Every loop of the `public_ohlcv_*` branch appends a line to `/tmp/cbp_debug.txt` (line 1208), shared by all processes and never rotated: about 60 bytes a loop, up to about 5 MB a day per process at 1-second loops, up to about 8 GB over 26 weeks for 9 processes. | SHOWN by reading | LOW (disk) | Codex | Remove the line (behaviour unchanged) or rotate it; monitor disk (spec) |
| BA-13 | **No freshness or gap check on candles.** The runner does not compare the last candle's time with the clock and does not check for missing hours; the research engine refuses gaps (S4-02). Coinbase omits hours without trades. | SHOWN by reading | LOW for BTC/ETH/SOL; MEDIUM for Group B's smaller coins | Codex | Record the last candle's time and any gaps at each decision (spec) |
| BA-14 | The indicators start again on each loop's 60-candle window: the slow EMA keeps about 1% of its weight on the window's first close, Wilder RSI about 3% on its first 14 changes. Signals near a threshold can differ from a long-history calculation. | SHOWN by reading (`indicators.py`) | LOW (the exit-parity replay variant C_path_w60 already models the 60-candle window) | - | Note |
| BA-15 | Look-ahead in the signal code: none found. Breakout compares the current price with the previous channel (`up[-2]`, excluding the current candle); EMA cross and mean reversion use the latest close only. The only "future" in live use is the opposite: the forming candle (C-06, BA-08). | SHOWN by reading | Control present | - | - |

Probes P-4 and P-5 are scripts, not tests, run on the existing archive `research/multisymbol_baseline_v1/public_archive.sqlite`
(sha256 e74aa378..., untracked, read-only) with the copy of the code (identical to the repository for the files used):
`python3 -I docs/research/bot_audit_20261031/probes/probe_forming_volume.py <repo root> <archive> <out.json>` and the same for
`probe_filtered_sells.py`. Outputs: `probes/forming_volume.json`, `probes/filtered_sells.json`. OKX volumes, not Coinbase's.

**What could overturn this:** intra-hour volume is not even (it bunches around news and the hour), so BA-08's shares
are indicative; Coinbase's real rate limit (BA-11); whether Coinbase returns the forming candle for every product
(C-06 was shown on the runner's code path, not per product).

## Session 3 findings: restart, recovery, monitoring and alerts
Scope: `strategy_runner.py` (sha256 7006466d...) state keys, kill gate and lock (lines 256-290, 1077-1160, 1386-1510,
1540-1660, 1668-1700); `services/risk/kill_conditions.py`, `performance_kill.py`; `storage/strategy_state_sqlite.py`,
`intent_queue_sqlite.py`; `paper_runner.py`; `live_intent_consumer.py` (for comparison); `packaging/systemd/`;
`scripts/check_dead_man.py`, `check_hetzner_paper_host_health.py`, `restore_paper_campaigns.py`, `run_paper_sim_monitor.py`;
`services/alerts/alert_dispatcher.py`. Read only; nothing run in this session. Searches for earlier work: kill_cooldown,
kill_until, cooldown, lockout, Restart=, heartbeat in `docs/` and `packaging/`; found `e01_paper_evidence_audit_20261002.md`
item 7, `es_performance_kill_effect_20261007.md`, `cooldown_patch_current_base_review_20261007.md`,
`cooldown_protective_combined_review_20261007.md`, `cooldown_exit_quantity_treatment_20261007.md`.

| ID | Finding | Evidence | Severity (simulation) | Owner | Disposition |
|---|---|---|---|---|---|
| BA-16 | **A restart can lock an account out of trading for days** (known since 2026-10-02, not fixed, and missing from the engineering queue, the simulation spec and this audit's session 1). The kill cooldown is stored as an absolute loop number (`kill_until`), the loop counter starts at 0 in every process (line 1098), and `kill_until` is cleared only when an entry passes the risk check (line 1611). After a restart the account is blocked until the new process reaches the old loop number, about as long as the old process had run before the trigger. Signal changes during the block are used up (change-only entries), so entries are lost even after it. The kill gate also skips exits (line 1492-1509 runs after the exit decision). On the laptop this held the ES candidate out from 2026-07-09 to at least 2026-10-02. Patches 0001 (cooldown as a persisted count) and 0002 (protective exits during a cooldown) were reviewed 2026-10-07 (combined: ACCEPTED_WITH_RISK, deployment not authorised) and are not in the current runner. | SHOWN by reading (current code); the lockout SHOWN in practice by the 2026-10-02 audit | HIGH | Codex / owner | Before the start: apply the reviewed patches with tests that fail on the current code, or record and alert on every `kill_cooldown` status; add to the engineering queue |
| BA-17 | Both cooldowns are counted in loops: 20 after repeated risk blocks, 50 after 3 losing exits or a 10-point drawdown on the running sum of trade results. At the default 1-second loop that is 20 and 50 seconds, which barely delays an hourly strategy. At the spec's 15-second loop it is 5 and 12.5 minutes. The spec's loop setting was written without checking this (O-13). | SHOWN by reading (`kill_conditions.py` 43, `performance_kill.py` 69, presets) | LOW (simulation); MEDIUM before live (the drawdown stop does not stop) | Owner / Codex | Record the wall-clock cooldowns in the run manifest; decide the intended pause separately |
| BA-18 | **A crash between taking an intent and filling it strands the intent at `submitting`.** The paper path has no recovery for it (the live consumer has one: `_recover_stale_submitting`). The runner counts only `queued` and `submitted` as open, and treats the action as already sent, so a lost exit is not sent again while its condition lasts (as BA-05). | SHOWN by reading (`intent_queue_sqlite.py` 249-280; search for `submitting`) | MEDIUM (needs a crash in a short window) | Codex | Record intents at `submitting` older than one minute; alert |
| BA-19 | **Nothing restarts the bot processes.** `packaging/systemd/` has units with `Restart=on-failure` for the live consumer, reconciler, collectors and dashboard, but none for the strategy runner, the paper runner or the snapshot publisher; the two trial units for the paper evidence collector (`packaging/systemd/trials/`, which starts all three) have no restart policy, and the server's two paper collectors run as plain processes. `scripts/restore_paper_campaigns.py --restore` restarts dead collectors without duplicating them, but no schedule for it was found. After a server reboot every account stays down until someone notices. | SHOWN by reading; owner's server check of 2026-10-31 | MEDIUM | Codex | Schedule the restore tool (or add units) and record every restart; with BA-16, a restart needs the cooldown fix |
| BA-20 | A leftover lock is reclaimed only if its process number is no longer in use; if a reboot reuses that number, the runner refuses to start (fails closed; status `lock_exists`). | SHOWN by reading (`managed_component.py` 40-70) | LOW | - | Covered by BA-21's watcher |
| BA-21 | **No alert would reach the owner if an account stops.** The bot processes write a status file every loop but no heartbeat; the dead-man check (systemd timer, every minute) watches only the live consumer and reconciler, by heartbeat. The paper simulation monitor records fills and profit and sends nothing. The paper processes alert on two events of their own: the evidence collector's campaign status changing into a stop or failure state (`campaign_events.py`, called from `paper_strategy_evidence_service.py` 117-135) and the evidence writer refusing or degrading (`paper_gate_events.py`). A process that dies or a server that reboots writes nothing, so neither fires then; neither covers a cooldown lockout, stale candles or a refused exit. All alerts go out only through `alert_dispatcher` (Slack webhook or email) when `alerts.enabled` is set in the server's configuration, which was not checked (no server access). | SHOWN by reading (search for `send_alert` callers) | HIGH for a 24/7 unattended run | Codex / owner | Before the start: one watcher over every account's status file (age over 10 minutes; notes `kill_cooldown`, `no_public_ohlcv`, stale snapshot, `lock_exists`; refused exits) that calls `send_alert`; send a test alert and confirm it arrives |
| BA-22 | Correction to S4-05 (integrity checks): a systemd timer for the data-collector cadence check is in the repository (`packaging/systemd/cbp-edge-cadence.timer`, hourly, `--alert`); whether it is installed on the server is not known. S4-05 said none was found; its search did not cover `packaging/` (O-14). | SHOWN (file) | - | Owner / Codex | Check `systemctl list-timers` on the server |

**What could overturn this:** the server may run supervision or timers outside the repository (not visible here);
the alert configuration on the server; BA-18 and BA-20 were not reproduced by running.

## Before the simulation starts (summary of all three sessions)
Must: BA-04 snapshot publisher running; BA-16 cooldown fix or alerting; BA-21 a watcher with a confirmed test alert;
BA-19 restarts; BA-12 remove the debug line; the settings in the spec. Record, do not fix during the run: BA-01 mid
fills (record bid and ask), BA-05/BA-18 lost intents, BA-08/BA-09 filters, BA-13 candle gaps.

## Live path, session 1 (2026-10-31): order placement, retries, key scope, dashboard control, outages
Scope: callers of `place_order`; `services/execution/exchange_client.py` (submission and retry); `services/security/`
(credential loading, permission probes); `dashboard/auth_gate.py`, `dashboard/pages/60_Operations.py` (live control),
`services/app/dashboard_launch.py`; `services/execution/live_reconciler.py` (outline); `services/live_router/router.py`;
`services/ai_copilot/`. Read only; nothing run. Searches for earlier work: the capital-protection audit (CP-01 to CP-15),
the work log for key permissions (found the 2026-10-29 scope probe), docs and code for an exchange-side stop (none).
Already registered and not repeated here: CP-09 (entry limits block exits), D-1/CP-03, CP-02 (no strategy reaches live),
CP-14 and H-06 (position limit), BA-16 (cooldown lockout), BA-05 and open decision 3 for live (refused exits not
retried), BA-10 (a failed fetch skips exits).

| ID | Finding | Evidence | Severity | Owner | Disposition |
|---|---|---|---|---|---|
| LP-01 | Every exchange order still goes through `place_order.py`: its callers are `exchange_client.py`, `live_exchange_adapter.py`, `order_router.py` and `order_manager.py` (async); `trading_runner/run_trader.py` uses a paper venue. | SHOWN by search | Control present | - | Consistent with CP-01 |
| LP-02 | A retried live order cannot be placed twice by this path: each submission sends a client order ID to the exchange; a dedupe store refuses a second submission once one is recorded; an ambiguous error (for example a timeout) marks the order unknown and checks the exchange; a retry is allowed only when the exchange confirms the order was not placed. Tests exist (`tests/test_exchange_client_retry_flow.py`, the file Codex changed in group D). | SHOWN by reading (`exchange_client.py` 160-235); not run | Control present | - | Keep; fix the group D guard failure in that test file |
| LP-03 | **The key's permissions were checked once, not enforced.** On 2026-10-29 one authorised read showed the Coinbase key can view and trade but not transfer funds (CLAIMED from Codex's log; artifact `docs/review_artifacts/coinbase_scope_probe_20261029/`). Nothing checks this when trading starts, so a key replaced by one that can transfer would trade without notice. | SHOWN by search (no permission check in `services/`); probe CLAIMED | MEDIUM before live | Codex | Before live: read the key's permissions at live start (one read request) and refuse to trade if it can transfer |
| LP-04 | Dashboard live control: binds to 127.0.0.1 by default; login with password, MFA, lockout and roles (a bypass only with `APP_ENV=dev` and an explicit flag). "Halt" arms the kill switch and halts the system guard; "Resume" needs the OPERATOR role, a recent live-enable ceremony and passing guards. Not checked: the server's real bind address and user list. | SHOWN by reading (`auth_gate.py` 140-146; `60_Operations.py` 77, 1060-1120; `dashboard_launch.py` 61-95) | Control present; LOW: an operator, not only an admin, can resume live trading | Owner | Decide whether resuming live trading should be admin-only |
| LP-05 | **No protection on the exchange.** Stops, trailing stops and time exits exist only inside the bot. If the server, the network or the bot stops while a live position is open, nothing closes it (BA-10, BA-19). | SHOWN by reading; no exchange-side stop in code or docs (search) | HIGH before live | Owner / Codex | Before live: decide on a backstop stop order on the exchange after each entry (wider than the bot's own stop, cancelled when the bot exits) and/or an outside alert with a written manual procedure |
| LP-06 | Live reconciler: matches orders and fills by exchange and client order IDs; an order "not found" becomes final only after repeated observations; it places and cancels nothing. Read in outline only. | SHOWN by reading (outline) | Control present, not verified in depth | Codex | Review in depth at the live cutover |
| LP-07 | The AI copilot and the live router place nothing: the copilot has no order, queue, arming or shell call; `live_router/router.py` only returns allow or deny to the consumers. | SHOWN by search | Control present | - | - |

**Summary of the live path so far.** The machinery that places an order is careful: one gate, client order IDs,
duplicate refusal, reconciliation of ambiguous submissions. The gaps are around it, and all matter only once a strategy
can reach live (CP-02): exits blocked by entry limits (CP-09), refused exits not retried (decision 3, live), the
cooldown lockout (BA-16), no backstop on the exchange (LP-05), key scope not enforced (LP-03), the position cap
incomplete (CP-14, H-06).
**Next session (live path 2):** the live-enable ceremony and resume gate (`services/admin/`), the live risk gates
(`live_risk_gates.py`, H-06), credential handling in logs and errors, and the order sizing and precision path.

## Live path, session 2 (2026-10-31): switching live on, the final gate, reviewed patches, keys, order size
Scope: `services/admin/resume_gate.py`, `live_enable_wizard.py`, `services/execution/live_enable.py`, `live_arming.py`,
`scripts/killswitch.py`, `place_order.py` (`_enforce_fail_closed` 581-640, `_is_armed` 351-359, precision 440-455,
market rules 679-700), `services/risk/live_risk_gates.py`, `services/security/credential_store.py`,
`credentials_loader.py`. Read only; nothing run. Searches for earlier work: `e01_paper_evidence_audit_20261002.md`
items 23-25, `docs/safety/live_mode_contract.md`, `killswitch_cli_audit_review_20261005.md` and the other ten
2026-10-05 patch reviews, `docs/review_artifacts/rev87_review_20261005/`.

| ID | Finding | Evidence | Severity | Owner | Disposition |
|---|---|---|---|---|---|
| LP-08 | **The live-enable ceremony is not what the final gate checks** (known since 2026-10-02: E01 audit items 23-25, `live_mode_contract.md`). `place_order` treats a process as armed if one of three environment variables is set (`_is_armed`); it does not read the ceremony, its token or the persisted arming state. New detail: two more ways around the ceremony are in the code. `services/admin/live_enable_wizard.enable_live()` turns live on, arms and sets the system guard to RUNNING with no token, checklist or preflight (no production caller found; tests only). `scripts/killswitch.py --disarm` releases the kill switch with no ceremony and no record. All need shell access to the machine; the ceremony protects only the dashboard path. | SHOWN by reading and search | MEDIUM before live | Codex / owner | Before live: the final gate requires the ceremony-backed arming state, not an environment variable; remove or gate the wizard path; record kill-switch releases (patch 0062, LP-10) |
| LP-09 | The ceremony itself: five self-declared checklist items, a preflight, a one-time token (random, 30-minute expiry, stored hashed, usable once); resuming is allowed within 1 hour of the token's use and re-checks the guards. The preflight checks the Python version, packages, config, a free port and market reachability; it does not check the open pre-live defects (CP-09, BA-16, LP-05, CP-14 and others). | SHOWN by reading (`live_enable.py` 12-50; `live_arming.py` 196-328; `resume_gate.py` 18-110) | Control present; MEDIUM gap before live | Codex | Before live: the preflight refuses while any defect on the pre-live list in `PROJECT_STATE.md` is open |
| LP-10 | **Reviewed safety fixes are missing from the code and nobody tracks them.** Of the early-October patch series, these are absent from the current code by marker search: 0001 and 0002 (cooldown, BA-16; combined review ACCEPTED_WITH_RISK), 0055 (spot-only boundary at the order gate), 0059 (fill-sink loss count), 0060 (dead-man names per host), 0062 (kill-switch release recorded). Markers of 0056 (AI and probability gates fail closed) and 0057 (reconciler keeps working orders) are present. The patch files are not in the repository and `PROJECT_STATE.md` does not list them; their reviews say "not applied to this checkout". Not checked: 0052-0054, 0058, 0063 and patches outside these reviews. | SHOWN by search (marker strings named in each review's "Correction" section; a missing marker could also mean the fix was written differently) | HIGH (process: fixes reviewed for live money do not reach the code) | Owner / Codex / Claude | Proposed: one inventory of every reviewed patch since September with its review status, whether it is in the code, and the owner's decision (apply or drop). Claude does the documents; Codex finds the patch files |
| LP-11 | The position limit in the live risk gate is still parsed and never checked (H-06, 2026-10-20): `max_position_notional_usd` appears only where limits are read, not in `check_live`. | SHOWN by search (current code) | HIGH before live (known) | Codex | With engineering item 3 (position cap) |
| LP-12 | Credentials: the OS keyring is read first (`credential_store.py`, service "crypto-bot-pro"); no logging or printing of key values was found; scripts exist that scan events and backups for secrets. | SHOWN by search (not exhaustive) | Control present | - | - |
| LP-13 | Order size and price are rounded to the exchange's precision and checked against stored market rules before sending; stale or invalid rules block the order. | SHOWN by reading (`place_order.py` 440-455, 679-700) | Control present | - | - |

**Live path, both sessions:** the order machinery is careful; the controls around it have gaps that matter at the live
cutover (LP-05, LP-08, LP-09, LP-11, CP-09, BA-16, decision 3), and LP-10 shows why: fixes are reviewed and then lost.
The live-path audit stops here. The rest of `services/` has no order path of its own (every order passes `place_order`,
LP-01; nothing in production writes the live queue, CP-02) and was not audited for other flaws.

**Correction to LP-10 (2026-10-31, omission O-17):** LP-10 said the markers of 0056 and 0057 are present in the code.
Those strings were already in the base commit `97c24c8e4` before the patches, so they show nothing. The full check
(`docs/research/patch_inventory_20261031/`) finds none of the 72 patches of the series in the laptop's code. It also
finds that the multi-symbol fix (D-1) has existed since 2026-10-02 as patch 0004 (O-18). The original LP-10 row above
is kept unchanged.

## Rest of `services/`, session 1 of 3 (2026-11-05): reachability map, entry gates, position scaling

**Task card:** work log, 2026-11-05T12:43:47Z. Read only. Static parsing only; nothing run.

**Scope and method**
- Static import closure (Python `ast`, imports inside functions included) from six entry points:
  `services/execution/strategy_runner.py`, `services/execution/paper_runner.py`,
  `services/market_data/system_status_publisher.py`, `scripts/run_paper_sim_monitor.py`, `scripts/run_group_a_alert.py`
  and `services/execution/place_order.py`.
- Result: 165 reachable modules in `services/` and `storage/` (33,724 lines). Per-module status is in
  `rest_of_services_reachability_20261105.csv`:
  - 27 cited by earlier audits. Citation is a proxy; it does not prove the module was read in full.
  - 35 changed in the working tree by Codex's item 2, under its own GATE reviews. Not re-audited here.
  - 103 neither cited nor changed (16,693 lines): the gap.
- Read this session:
  - `services/execution/safety.py` and `storage/execution_guard_store_sqlite.py`;
  - `services/risk/market_quality_guard.py`, `staleness_guard.py` and `position_scaling.py`;
  - `services/market_data/tick_reader.py` and `services/feature_gate.py`;
  - `services/risk/exposure_controls.py` (limits and `evaluate_entry`);
  - `services/validation/paper_multi_symbol_validation.py` (`collect_runtime_rows`);
  - `services/risk/risk_daily.py` (outline);
  - `strategy_runner.py` lines 400-420, 1134-1146, 1510-1566 and 1686-1800.
- A pattern scan (exception handling, defaults, NaN handling, environment switches, clock use) covered 20 risk,
  execution and storage modules. Not read in full: the rest of the gap, including `services/control/` (12 modules),
  `services/alerts/` (17), the non-default strategies (20), `services/admin/config_editor.py` and `state_report.py`,
  `storage/position_state_sqlite.py` and `trade_journal_sqlite.py`.
- **Runtime configuration** (whitelisted keys only, AGENTS.md "Configuration inspection"): `config/user.yaml` and
  `.cbp_state/runtime/config/user.yaml` have no `safety` or `market_quality_guard` section and no scaling keys under
  `risk`, so the code defaults below apply on this Mac. The server's configuration was not checked.
- **Earlier work searched:**
  - this file (BA-01 to BA-22, LP-01 to LP-13);
  - `capital_protection_audit_20261031/` (CP-01 to CP-15), `exit_parity_audit_20261031/`, `integrity_checks_20261031/`,
    `patch_inventory_20261031/`, `overlooked_sweep_20261031/` (OV-01 to OV-06);
  - `REMAINING_TASKS.md` deferred items 16 and 29;
  - `r01_reachability_map_20261004.md` (an earlier repo-wide static map; this one covers only the simulation and live
    entry points);
  - the `PROJECT_STATE.md` omission register.

| ID | Finding | Owner | Evidence | Severity | Disposition |
|---|---|---|---|---|---|
| BA-23 | **The runner adds to winning positions, and no backtest or replay models it.** A buy transition while a position is open and at least 1.5% in profit adds another entry (defaults: scaling on, at most 2 adds; `position_scaling.py` 20-28 and 50-76; runner 1692-1701). The 0.5 size multiplier set in every preset is never used: no code outside `position_scaling.py` reads `size_multiplier`, so adds are full size (runner 1686). Each add resets the entry price, trailing peak and bars held of the whole position to the add price (runner 1796-1798), moving the stop, take-profit and hold-limit references. Setting `enable_position_scaling: false` removes the add limits instead of blocking adds: `evaluate_scale_in` then returns `is_scale: False`, and the runner blocks only when `is_scale` and not `ok`. No scaling code was found in `services/backtest/` or `scripts/replay_runner_decisions.py`, and no earlier audit row mentions it. | Codex (items 2 and 4) | SHOWN (code, search); not run | MEDIUM-HIGH for the simulation's check that the bot does what the research says; up to three entries per symbol | Owner decides whether the simulation disables adds or the replay models them; no change without approval |
| BA-24 | **The runner's exposure-percentage limits never block.** `evaluate_entry` compares per-symbol, total and strategy exposure (20%, 80% and 50% by default) with `exposure_pct` or `notional_pct` on each position row. No code sets either field (search over `services/` and `storage/`), so all three exposures are 0. Only `max_concurrent_positions` (5) and open intents per symbol (1) can block. If reading positions or intents raises, `collect_runtime_rows` returns empty lists and nothing blocks. CP-14 said the runner "checks exposure limits"; it checks them, but they are inert. | Codex (item 3, position cap) | SHOWN (code, search) | MEDIUM; with BA-23, nothing limits the size of adds | Add to the position-cap work; no change without approval |
| BA-25 | **The paper path's daily-loss and trade-count gates can never fire.** `paper_engine.py` 219 and `decide_order` (`live_router/router.py` 85, used by `paper_runner.py`) call `safety.should_allow_order`, which reads `ExecutionGuardStoreSQLite`. Nothing writes that store's realized P&L: `add_realized_pnl` has no caller outside the store, `dist/` and tests. Its trade count is raised only by the live executor (`_executor_submit.py` 464) and the unused `live_trader_multi` and `live_trader_fleet`. So `max_daily_loss` never triggers anywhere, and `max_trades_per_day` never triggers on the paper path. The store's day is the machine's local date (`date.today()`), while `risk_daily` uses UTC. The live path has separate limits that are fed (`place_order.py` with `risk_daily`, fed by `fill_sink`). | Codex (item 2) | SHOWN (code, search); no `safety` section configured here | MEDIUM for paper-versus-live parity if limits are set; LOW now | Owner decides whether the simulation applies live-equivalent daily limits |
| BA-26 | **Market-quality guard: a quote without a timestamp skips the staleness check.** `tick_reader.py` returns `ts_ms` 0 when missing, and the guard checks age only when `ts_ms > 0`. A future timestamp also passes (negative age), here and in `staleness_guard.py`. Adds to known deferred item 29 (fail-open defaults `block_when_unknown: false` and `require_bid_ask: false`), which this configuration does not override. The paper engine separately refuses orders without a finite reference price. | Codex | SHOWN (code); configuration absent | MEDIUM live (item 29); LOW paper | Add missing and future timestamps to item 29's proof |
| BA-27 | **The probability gate, if switched on without a value, blocks exits.** `proba_gate` treats a missing `CBP_FUSED_PROBA` as 0.5 (non-strict). That fails both the buy threshold (0.55) and the sell threshold (0.45), so sells routed through `decide_order` would be refused. A NaN value clamps to 1.0: buys pass, sells are refused. The gate is off by default (`CBP_USE_FUSED_PROBA` unset, router override false). Same class as CP-09 (an entry-style gate applied to exits). | Codex | SHOWN (code) | LOW (off) | Add to deferred item 16 (quarantine) |

**Status:** session 1 of 3 done. Self-checked; Codex to verify. Next: `services/control/`
(`deployment_stage.py`, `kernel.py`, `paper_promotion_*`), `services/admin/config_editor.py` and `state_report.py`,
a full read of `risk_daily.py` and `system_health.py`, and `storage/position_state_sqlite.py` and
`trade_journal_sqlite.py`.

## Rest of `services/`, session 2 of 3 (2026-11-05): daily risk ledger, health, config loading, journals, stages

**Scope and method**
- Read in full:
  - `services/risk/risk_daily.py`, `services/risk/system_health.py`;
  - `services/admin/master_read_only.py`, `services/config_loader.py`;
  - `storage/trade_journal_sqlite.py`, `storage/position_state_sqlite.py`.
- Read in part:
  - `services/admin/config_editor.py` (`load_user_yaml`);
  - `services/journal/fill_sink.py` lines 100-170;
  - `services/control/deployment_stage.py` (loading, promotion, `action_allowed`, allocation);
  - `services/analytics/paper_sim_monitor.py` lines 320-345.
- Caller searches for each module. Nothing run; read only.
- **Earlier work searched:** this file; `fill_sink_loss_lock_review_20261005.md`; `patch_inventory_20261031/`;
  `REMAINING_TASKS.md` (risk-daily finite-write slice of 2026-07-14, promotion path); `r01_reachability_map_20261004.md`.

| ID | Finding | Owner | Evidence | Severity | Disposition |
|---|---|---|---|---|---|
| BA-28 | **Known and still present: a failed daily-loss write counts as success.** `apply_fill_once` returns `False` both for "already applied" and for any other failure (non-finite input, locked database), and `fill_sink.py` (147-152) ignores the return value. The loss is then missing from the live daily-loss figure, and the `risk_sink_failed` lock is never set. This was found on 2026-10-05 (`fill_sink_loss_lock_review_20261005.md`, P2), and the fix is in October patches 0059 and 0076, which were never applied (U-09). `risk_daily_apply_not_recorded` appears nowhere in the code. | Codex | SHOWN (code, search) | HIGH before live; not new | Part of the 72-patch decision (U-09) |
| BA-29 | **The health check reports healthy when the daily-ledger table is missing.** `_check_accounting_invariant` treats "no such table" as a first run and returns no problem, even when `canonical_fills` holds fills that were never applied (`system_health.py` 70-72). `place_order` reads this health state. | Codex | SHOWN (code) | LOW (needs a missing table) | Treat a missing `risk_daily_fills` as healthy only when `canonical_fills` is empty or absent |
| BA-30 | **Known design: trade and notional counts can be lost silently.** `record_order_attempt` runs after the order is submitted and swallows every error (`risk_daily.py` 333-366), so a failed write loses the trade and notional increments that the daily trade-count and notional limits rely on. `REMAINING_TASKS.md` (2026-07-14) records this as the intended best-effort contract. | Codex | SHOWN (code) | LOW to MEDIUM before live; known | Owner or Codex to confirm the contract, or log the lost count to the risk-sink flag |
| BA-31 | **The simulation monitor can miss a quiet coin's last fill.** `paper_sim_monitor.py` 332 looks for a coin's latest journal fill only among the newest 1,000 fills of all coins. With 9 or more accounts over the simulation, a coin that trades rarely can show no fill. The file is changed in Codex's working tree (item 2). | Codex (item 2) | SHOWN (code) | LOW (reporting) | Query by coin and window instead of a global limit |
| BA-32 | **Deployment stages do not gate the default bot.** `action_allowed` (`deployment_stage.py` 288-295) has no callers. The stages (paper, shadow, capped live, scaled live) are read only by the ES daily-trend kernel, `evidence_logger.py`, the allocator and `scripts/compat/run_strategy_runner.py`. The default runner, the paper engine and `place_order` never consult them; live arming rests on `place_order`'s own checks (LP-08). A corrupt stage file loads as paper, including for a strategy in safe-degraded. | Codex | SHOWN (code, search) | LOW (context for LP-08) | Note only |

**Checked and found sound:**
- Config loading: `master_read_only.py` loads strictly and treats an unreadable configuration as read-only, so the paper
  engine and router refuse orders (BA-04).
- The daily ledger: `risk_daily.snapshot` flags non-finite fields and `place_order` blocks on them;
  `apply_fill_once` deduplicates fills.

The market-quality guard's non-strict loading (a corrupt `user.yaml` gives the fail-open defaults) is already covered by
deferred item 29 and BA-26.

**Status:** session 2 of 3 done. Self-checked; Codex to verify. Next (session 3):
- `services/alerts/` (17 modules; Codex's R3 owns the new Group A alert path, so only the older dispatcher chain);
- the non-default strategies reachable through the registry;
- `services/control/` promotion and evidence qualification;
- `services/admin/state_report.py`.

## Rest of `services/`, session 3 of 3 (2026-11-05): selection, promotion evidence, alerts; budget reached

**Scope and method**
- Pattern scan, then reading the flagged code, in:
  - `services/strategies/strategy_selector.py` and its call in `strategy_runner.py` (1377-1405);
  - `services/control/paper_promotion_policy.py`, `paper_evidence_qualification.py`, `paper_promotion_progress.py`,
    `retirement_checker.py` and `promotion_thresholds.py`;
  - `services/alerts/email_notifier.py` and `strategy_decision_events.py`;
  - `services/signals/candidate_advisor.py` and `candidate_store.py` (patterns only);
  - `services/admin/state_report.py` (patterns only).
- Python's STARTTLS default was checked in the Linux shell (Python 3.10.12). The Mac's Python was not checked.
- **Earlier work searched:** `docs/research/signal_discovery_classification.md`; `REMAINING_TASKS.md` (SMTP, selector,
  candidate advisor); this file.

| ID | Finding | Owner | Evidence | Severity | Disposition |
|---|---|---|---|---|---|
| BA-33 | **Email alerts do not verify the mail server's certificate.** `email_notifier.py` 46 calls `starttls()` without an SSL context. Python then uses `ssl._create_stdlib_context()`, which does not verify certificates (shown in the Linux shell: `CERT_NONE`, `check_hostname=False`). Anyone able to intercept the connection could read the SMTP login sent next. It applies only if the email channel is configured through the `CBP_SMTP_*` variables (values not read). The owner chose Slack for alerts (rev57). No earlier mention found. | Codex | SHOWN (code; standard-library behavior shown on Python 3.10) | LOW now; MEDIUM if email is used | Pass `ssl.create_default_context()` to `starttls`; no change without approval |

**Checked and found sound:**
- The runner calls `select_strategy` every loop, but ignores its output and trades the configured strategy (1381-1384),
  as `signal_discovery_classification.md` requires. The candidate advisor stays behind `CBP_USE_CANDIDATE_ADVISOR`.
- Promotion evidence counts a fill only with explicit non-sample provenance; a missing flag excludes it.
- The promotion floors cannot be configured below the code minimums.

**Budget reached: research item 1 stops here (POP: report what is done and what remains).**
- **Done:**
  - all six entry points mapped (`rest_of_services_reachability_20261105.csv`);
  - 34 of the 103 gap modules read or pattern-scanned (5,054 of 16,693 lines);
  - 11 findings, BA-23 to BA-33. One of them, BA-28, is known and still present; the rest are new or add detail to
    known deferred items.
  - Runtime configuration was checked for the relevant whitelisted keys on this Mac only.
- **Not covered** (69 modules, 11,639 lines):
  - `services/strategies/` (18, the non-default strategies and helpers, including `presets.py`);
  - `services/backtest/` (7: the research engines `parity_engine`, `walk_forward`, `evidence_cycle` and others; their
    behavior was examined in the exit-parity and integrity audits, not read line by line);
  - `services/analytics/` (5), `storage/crypto_edge_store_sqlite.py` and `market_store_sqlite.py`;
  - `services/markets/` (9), the Coinbase account helpers from Codex's fix 1 (5, GATE-reviewed);
  - `services/ai_engine/` (3; known: off, never trained, fail-open fix 0056 unapplied);
  - smaller journals and helpers.
- **Not checked:** the server's runtime configuration.

## Dated independent correction, 2026-11-05T18:45:50Z (Codex)

Bot relation: BOT_RULES; runtime configuration not checked by this review.
The complete owner-supplied handoff and BA-23..39 source claims were checked in
`docs/research/claude_handoff_audit_20261105/README.md`; 17 synthetic probes passed.
Original findings above are retained as history, not silently rewritten.

- **BA-23 / O-106:** the unconditional default-pyramiding conclusion is incorrect.
  `strategy_runner._cfg` defaults `position_aware` to true; the actual shared
  `select_exit_decision` guard refuses held-position buys before scaling. The
  scaling issues remain conditional on disabling that guard. Do not require a
  simulation entry-policy change without establishing the intended configuration.
- **BA-35:** archive normalization rejects non-finite values, not all invalid
  prices: finite zero and negative closes survive. Same-close execution is an
  idealization; its bias is not established as merely slight. No results rerun.
- **Coverage:** the CSV still labels 103 modules gap_unaudited and does not mark
  the reported 61 by session. `storage/trade_journal_sqlite.py` is one such row
  and is imported by `paper_runner.py`; remaining-off-path assurances are not
  established. Static reachability is not runtime coverage or complete review.
- **ES:** an October 29 last evidence file is not proof of current stoppage or
  its cause. No process, service, server configuration or owner restart intent
  was inspected by this independent review.
- **BA-28:** the ignored daily-loss failure reproduced through the real fill
  sink and a disposable database: result `ok=True`, no loss row, no failure flag.
  This remains a live-money concern, not a repaired behavior.
- **BA-37 / BA-39:** NaN permits unpenalized base allocation, not necessarily
  full-account allocation; summary net-realized expenses open-lot buy fees and
  must not be confused with the sum of closed-trade net P&L or account NAV.

This corrects conclusions, not code or operations. O-107..109 record the material
omissions. Whole-bot coverage and runtime objectives remain INCOMPLETE.

What do I know that could change the owner's decision that I have not yet said?
The reported default-adds decision was based on a missing upstream guard; the
daily-loss write failure, by contrast, is now independently reproduced.
- **Owner decision:** extend the item (suggested: 1 session for `presets.py` and the non-default strategies, 1 for the
  research engines), cut it here, or park the remainder.

## Rest of `services/`, sessions 4 and 5 (2026-11-05, extension approved by the owner): strategies, presets, research engines

**Task card:** work log, 2026-11-05T13:00:12Z. Budget 2 sessions. Read only; nothing run.

**Scope and method**
- Session 4 (strategies):
  - `presets.py` in full;
  - `strategy_registry.py` (names and `trade_enabled` gate);
  - RSI and history guards in `momentum.py`, `pullback_recovery.py` and `impl_mean_reversion_rsi.py` (default);
  - a pattern scan of `volatility_reversal.py`, `gap_fill.py`, `breakout_volume.py`, `funding_extreme.py` and `composite_hybrid.py`;
  - `evidence_logger.py` (write path and sample stamping, with its callers).
- Session 5 (research engines):
  - `parity_engine.py` (`run_parity_backtest`);
  - `walk_forward.py` (window plan and segment metrics);
  - `ohlcv_archive.py` (row normalisation);
  - a pattern scan of `evidence_cycle.py`, `leaderboard.py`, `scorecard.py` and `regimes.py`;
  - `services/markets/fetch_coinbase_ccxt.py`, `cache_sqlite.py` and `prereq.py`.
- **Earlier work searched:** `exit_parity_audit_20261031/` (engines model signal exits only; code-default runner exits),
  `overlooked_sweep_20261031/` OV-04 (preset risk not applied), `signal_discovery_classification.md`, LP session 2
  (market rules in `place_order.py` 679-700).

| ID | Finding | Owner | Evidence | Severity | Disposition |
|---|---|---|---|---|---|
| BA-34 | **Two non-default strategies read a flat market as overbought.** The RSI helpers in `momentum.py` (32-33) and `pullback_recovery.py` (31-32) return 100 when there were no losses, including a window with no price change at all. The default `impl_mean_reversion_rsi.py` returns 50 for a flat window. These strategies are not in the simulation. | Codex | SHOWN (code) | LOW (not used) | Return 50 when gains and losses are both zero, if these strategies are ever used |
| BA-35 | **The research backtest fills at the signal bar's own close and charts a missing close as zero.** `run_parity_backtest` computes the signal on a window that includes the current bar and fills at that bar's close, with no one-bar delay. It models signal exits only (known from the exit-parity audit). A row with a missing close becomes price 0 (`_fnum(row[4], 0.0)`): no trade happens, but the equity curve values the position at 0 for that bar, so the maximum drawdown can be overstated. `ohlcv_archive.py` drops non-finite rows and keeps the last duplicate per timestamp, so archived data should not hit this; other inputs could. | Codex (research) | SHOWN (code) | LOW | Note for result interpretation; no change proposed |

**Context for BA-23, not a new finding:** every preset sets scaling to on, at most 2 adds and a 0.5 size multiplier.
The runner does not apply preset risk blocks (OV-04), so these values never reach it; the runner's code defaults
(the same values) apply. The presets set no exits for the three default strategies, so the runner uses code-default
exits (3% stop, 6% take-profit, 2% trailing stop, 60-bar hold), as the exit-parity audit found.

**Checked and found sound:**
- The registry honours `trade_enabled`, and `open_interest_shift` is off.
- Non-default strategies check history length and guard their divisions.
- `breakout_volume` uses the previous bar's channel, avoiding look-ahead.
- `evidence_logger` stamps sample provenance from `CBP_USE_SAMPLE_OHLCV`, and the paper engine uses it only per order
  and fill.
- `walk_forward.py` evaluates one fixed configuration over expanding windows. It selects no parameters, so selection
  cannot leak.
- `ohlcv_archive.py` rejects non-finite rows.
- Market rules: `place_order` checks the per-symbol rules after a cache-freshness prerequisite (LP session 2).

**Budget reached: research item 1 stops here.**
- **Covered:** 51 of the 103 gap modules (10,077 of 16,693 lines) read or pattern-scanned; findings BA-23 to BA-35.
- **Not covered** (52 modules, 6,616 lines):
  - `services/strategies/es_daily_trend.py` (ES campaign, not the simulation) and strategy helpers
    (`config_tools`, `crypto_edge_context`, `hypotheses`, `validation`, `campaign_summary`, execution identity and
    market-context capture, the last three Codex's and GATE-reviewed);
  - `services/analytics/` (5) and the stores `crypto_edge_store_sqlite`, `market_store_sqlite` and
    `ops_signal_store_sqlite`;
  - the remaining `services/markets/` helpers (6) and the Coinbase account helpers from Codex's fix 1 (5, GATE-reviewed);
  - `services/ai_engine/` (3, known);
  - `services/control/kernel.py`, `allocator.py` and `cognitive_budget.py` (used by the ES campaign);
  - journals, OS helpers and governance stubs.
- None of these is on the default simulation order path except the market and account helpers, which were reviewed
  elsewhere.
- **Not checked:** the server's runtime configuration.
- **Owner decision:** close research item 1 with this coverage, or extend for the ES campaign and analytics code.

## Rest of `services/`, sessions 6 and 7 (2026-11-05, second extension): ES campaign path, analytics and stores

**Task card:** work log, 2026-11-05T13:03:49Z. Budget 2 sessions. Read only; nothing run.

**Scope and method**
- Session 6 (ES campaign path):
  - `services/strategies/es_daily_trend.py` (signal adapter, `decide`, sizing) and its callers;
  - `services/control/kernel.py` (`evaluate`), `allocator.py` (`compute_allocation`), `cognitive_budget.py`;
  - `scripts/check_promotion_gates.py` (capped-live gates) and the ES runner script's kernel call;
  - the ES evidence files under `.cbp_state/data/evidence/es_daily_trend_v1/` (sizes and line counts only).
- Session 7 (analytics and stores):
  - `storage/ops_signal_store_sqlite.py` and its use in `place_order.py` (482-524);
  - `services/analytics/journal_analytics.py` and `strategy_feedback.py`, plus their use in `evidence_paper.py` and
    `evidence_cycle.py`;
  - pattern scans of `storage/crypto_edge_store_sqlite.py`, `services/strategies/crypto_edge_context.py` and
    `services/analytics/paper_evidence_artifacts.py`.
- **Earlier work searched:** `capped_live_gate_scope_review_20261005.md`, `breakout_paper_fill_baseline_2026_09_23.md`,
  `fill_sink_loss_lock_review_20261005.md`, `capital_protection_audit_20261031/`, `REMAINING_TASKS.md` (ops gate, ES).

| ID | Finding | Owner | Evidence | Severity | Disposition |
|---|---|---|---|---|---|
| BA-36 | **Known, with new detail: the capped-live gate "Position size at 25% of intended" always passes.** `check_promotion_gates.py` (1094-1096) hard-codes it as passed, citing a cap in `es_daily_trend.decide()` ("capped_live: max 1 contract"). Known since 2026-10-05 (`capped_live_gate_scope_review_20261005.md`, "Not changed"). New detail: `decide()` is called by no runner or order path (only a research script), so neither the gate nor the cap it cites applies to any order. | Codex | SHOWN (code, search) | MEDIUM before any capped-live promotion; LOW now | Make the gate check actual live position size, or report it as not checked |
| BA-37 | **The control kernel treats measured failures as healthy.** `kernel.py` reads `fill_rate` and `regime_stability` with `or 1.0`, so a measured fill rate of 0 or a regime stability of 0 becomes 1.0 (perfect) and triggers no halt. Missing metrics count as safe by design, and the ES runner calls `evaluate({})`. An unreadable cognitive-budget file means no alerts (`cognitive_budget.py` 49-56). A NaN stability gives full allocation (`allocator.py`: `min(1.0, nan)` is 1.0). All of this applies only at the capped-live and scaled-live stages; paper and shadow return "allow" before any check. | Codex | SHOWN (code) | LOW now; MEDIUM before ES capped live | Use explicit `None` checks instead of `or`, and treat missing or NaN metrics as failing at the live stages |
| BA-38 | **The optional ops risk gate never checks how old its signal is.** When `CBP_OPS_RISK_GATE_ENFORCE` is on, `place_order` uses the latest stored gate state with no age check, so an "allow" written before the ops service stopped keeps allowing orders. Unless `CBP_OPS_RISK_GATE_FAIL_CLOSED` is also on, a missing gate allows orders too. Off by default. No earlier audit row mentions it. | Codex | SHOWN (code) | LOW (opt-in) | Add a maximum age to the gate check when the gate is enforced |
| BA-39 | **Partly known: the research tools' "win rate" is before fees.** In `journal_analytics.fifo_pnl_from_fills`, win rate, wins, losses and average win/loss use gross P&L. `evidence_paper.py` (160) and `evidence_cycle.py` (401) copy this into paper-history rows as `win_rate`, and `evidence_cycle.py` (608-626) flags strategies by it. Its `net_realized_pnl` also subtracts the buy fees of positions still open. Known since 2026-09-23 (`breakout_paper_fill_baseline_2026_09_23.md`): only the feedback text was corrected, and `strategy_feedback.py` computes net win rate correctly. | Codex (research) | SHOWN (code) | LOW to MEDIUM for research reporting | Label it gross or switch it to net; research item 7's descriptive report must use net win rate and profit factor |

**ES campaign facts**
- The ES signal evidence files hold 62 records a day and stop after `signal_2026-10-29.jsonl` (SHOWN, file listing).
  2026-10-29 is the day the laptop restarted.
- `PROJECT_STATE.md` does not say whether the ES campaign should still be running. Its prospective trial ended on
  2026-10-16 with zero trades (`docs/checkpoints/es_prospective_endpoint_result_2026_10_16.md`).
- `decide()` sizes from an assumed $100,000 of capital by default. It is unused by any order path.

**Checked and found sound:**
- The crypto-edge store rejects non-finite values on write.
- The funding context checks the capture time against a maximum age before use.
- Paper and shadow stages get no allocation from the allocator.

**Budget reached: research item 1 stops here.**
- **Covered:** 61 of the 103 gap modules read or scanned (the ES path, `journal_analytics`, `strategy_feedback`,
  `paper_evidence_artifacts`, the ops and crypto-edge stores and `crypto_edge_context` added this time). Findings run
  BA-23 to BA-39.
- **Not read:**
  - `services/analytics/funding_observations.py` and `crypto_edges.py` (research scripts only);
  - `storage/market_store_sqlite.py`;
  - the remaining markets helpers;
  - `services/ai_engine/` (known);
  - journals, OS helpers and governance stubs.
- **Not checked:** the server's runtime configuration.
