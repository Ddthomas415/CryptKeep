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
