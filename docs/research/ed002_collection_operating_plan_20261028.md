# ED-002: local collection host and bounded operating plan

2026-10-28. Active role DIRECTOR. Risk HIGH (background collection and evidence).
Plan READY_FOR_INDEPENDENT_REVIEW. Operations/study/statistics INCOMPLETE.
No job installed, process started, power setting changed or market data fetched.

## Recommendation And Cost Fit

Use the existing Mac for a bounded direct-CLI collection pilot, not an AI task
per observation and not a new server or infrastructure service. The proposed
mechanism is one user LaunchAgent invoking a small reviewed wrapper around the
existing public capture CLI. It would be a NEW ED-002 research job; approval of
the twice-hourly design did not install or authorize that job.

This is the lowest-change locally demonstrated route: the existing venv and
public transport have completed three foreground captures here. No additional
paid host/data service or AI invocation budget is proposed. Electricity, storage
growth and operator availability are not claimed to be free. A foreground success
does not prove unattended operation, permissions or 182-day continuity.

Retain the existing systemd deployment path as an alternative if the Mac pilot
cannot maintain receipts. The checked repo units run a different crypto-edge
collector; they are not an ED-002 deployment. No remote host or access was checked,
and no existing research/trading unit should be repurposed or enabled wholesale.

## SHOWN Local Inventory, With Limits

- Darwin arm64, current user UID 501. Repo:
  `/Users/baitus/Downloads/crypto-bot-pro`; interpreter `.venv/bin/python`.
- `df -Pk` reported 404,000,000 available 1,024-byte blocks, 57% capacity used.
  This is a point-in-time APFS report, not reserved study space.
- `pmset -g custom` AC settings: idle system sleep 0, display sleep 10 minutes.
  No claim about closed lid, manual sleep, logout, reboot, power or Wi-Fi uptime.
- Six user LaunchAgent filenames were listed; none is named for CryptKeep or
  ED-002. A separately approved read returned 557 loaded user job labels, no
  CryptKeep/crypto-bot/ED-002 label match. Labels do not reveal every script.
- A separately approved current-user crontab read returned exit 1 with the
  no-crontab message. The initial unprivileged read was denied, not silently
  treated as absence. No cron entry was added.
- The two local Codex automation records have no ED-002 prompt reference:
  BTC/ETH weekly tracker ACTIVE; gainers/sleeper watch PAUSED. Neither was edited.
  No Claude task, system/root schedule, other-user job or remote host was inspected.

Evidence: `ed002_collection_host_inventory_20261028.json` and
`ed002_collection_launchd_read_20261028.json`. This is a scoped duplicate check,
not an assertion that no unseen scheduler exists. Recheck the exact proposed
label/path and known current-user locations immediately before any installation.

## Proposed Native Job And Pilot Bound

Target user-session label: `com.cryptkeep.ed002.public-inputs`. Target an eventual
reviewed wrapper, not the unbounded shell/profile or a model conversation.
Use absolute interpreter/repo paths, a clean environment and stdin disabled.
No account/service-token environment, shell profile, inherited proxies or private
Coinbase access. Restrict writes to the public ED-002 namespace and reviewed logs.

Keep adopted :05/:35 minute opportunities; timestamp slot identity in UTC. Propose
`StartCalendarInterval` with Minute 5 and Minute 35; no Hour/Day restriction.
Propose RunAtLoad=false and KeepAlive=false: do not start immediately at login or
restart failed invocations as an implicit retry. No StartInterval, WatchPaths,
socket activation, forced wake, power-policy edit or app-dependent agent task.

Propose an initial authorization lasting at most 24 elapsed hours and 48 slots,
not automatic 182-day operation. An operator-approved future pilot start/expiry, input hashes
and namespace must exist before enabling anything. Expiry stops data calls even
if the job remains loaded. No pilot dates are assigned here.

Each on-time slot gets at most one existing two-completed-hour capture, at most
27 public GETs and the existing socket/cooperative/worker/cleanup/payload caps.
This implies at most 1,296 GETs in the 48-slot pilot, with no retry or automatic
extension. A later slot is a distinct planned observation, not a reset of a
failed one. Existing 182-day capacity arithmetic is not a long-term grant.

## Missing Wrapper Behavior: Implement Offline Before Enabling

No wrapper or installer is claimed to exist. Keep this a small adapter, not a
new daemon, collector engine, database, AI loop or financial model:

1. Verify the reviewed source/plan/universe hashes before importing capture code;
   refuse drift and record only sanitized metadata. The existing worker's own
   current-source check is not a substitute for this frozen outer pin.
2. Derive one UTC slot, enforce the approved pilot start/expiry and remaining slot
   cap, and propose a maximum 120-second dispatch lateness. Outside that window,
   record missed/skipped evidence and perform no acquisition. This lateness cap
   is a NEW proposal, not silently adopted by the earlier cadence decision.
3. Use a nonblocking single-run lock and exclusive deterministic slot directory.
   A repeated/overlapping invocation must never make a second request or reset a
   partial slot. A process failure releases the lock without erasing its evidence.
4. Invoke the existing bounded CLI once in a clean environment; preserve its raw
   bodies, intent/receipt files and actual timestamps. No catch-up loop, historical
   permission repair, candle interpolation, automatic extension or strategy call.
5. Preserve an append-only slot result even on refusal/failure. Log hashes,
   counters, clocks and sanitized stages, not credentials, response bodies or
   arbitrary exception messages. Detect disk/permission failure before requests;
   never delete old evidence or add disk-cleanup authority to this job.

Synthetic tests must cover minute/UTC/DST behavior, expiry, lateness, duplicate
slot, lock contention/process failure, source drift, output collisions, clean
environment, refusal before transport, partial failure and bounded worker cleanup.
Static plist parsing must verify no extra triggers/restart paths. Real launchd
timing, Downloads-folder permissions and network behavior need separate pilot
evidence; fake tests cannot establish them.

## Pilot Acceptance And Visible Failure

Do not freeze A/E/B based on a loaded job or successful exit. Inspect every
expected pilot slot, including misses, metadata status/expiry, receipt clocks,
raw hashes and per-symbol completed-candle coverage. Preserve all 25 symbols and
current exclusions/unknowns. A usable boundary needs the preceding permission
record and a completed candle actually received by the adopted E deadline.

Report missing opportunities separately from hours lacking usable evidence:
two slots/hour provide redundancy, not a guarantee. Accept no unexplained input
gap as continuous evidence. Any delayed/restarted capture remains new knowledge.
The pilot makes no signal, return, portfolio, profitability or statistical claim.

Local receipts/logs are diagnostic visibility, not a delivered external alert.
No credentialed alert channel or new notification automation is configured here.
A known failed pilot must be reported honestly; do not assume existing alert
delivery or add unattended retention/deletion rules. Pilot expiry bounds exposure
to otherwise silent failures while later monitoring is assessed separately.

## Installation, Recovery And Authorization Boundary

After wrapper/tests and the exact job artifact are reviewed, obtain explicit
authorization for the single job installation and bounded pilot. Recheck scope
and duplicates; preserve any pre-existing conflicting artifact rather than
overwriting it. Install only this user job, not system daemons or other apps.
No immediate kickstart unless that exact additional capture is authorized.

Recovery must identify ownership: unload only this pilot's job if it was newly
installed; stop only its demonstrably owned active worker under the reviewed
cleanup bound; preserve raw evidence and receipts. No pkill, broad process cleanup,
volume/account mutation or unrelated scheduler changes. Unloading is not proof
an active descendant stopped; verify owned-worker disposition. Do not delete
capture data to claim rollback. An inability to stop must be recorded, not hidden.

A successful pilot still does not authorize indefinite operation or freeze study
dates. If this Mac cannot support the collection path, present evidence and a
separately authorized existing-host alternative, preserving all captured data and
the 25-symbol mandate. No framework or failed backtest needs to be restarted.

## Primary Documentation And Next Action

Apple documents timed launchd jobs and deferred execution after sleep in its
[Scheduling Timed Jobs guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html).
Apple's [launchd.plist manual source](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5)
describes calendar arrays, minute wildcards and coalescing of missed events.
Both were opened for this plan. They are archived/source documentation, not
proof of timing on this installed OS; test the actual path in the bounded pilot.

Next: offline implementation and review of only this wrapper/job artifact, with
the new pilot/lateness proposals explicit. No job installation, acquisition,
server, Docker, account/credential, power, strategy/risk/capital or trading change
is authorized by preparing this plan. Current study/statistics INCOMPLETE;
plan READY_FOR_INDEPENDENT_REVIEW. No whole-repo readiness or income claim.
