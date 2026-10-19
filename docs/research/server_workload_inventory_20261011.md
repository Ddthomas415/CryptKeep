# E3 server workload inventory

Date: 2026-10-11. Active role: AUDITOR. Read-only host observations:
22:29:50-22:30:53 UTC. No service, schedule, configuration, credential or
campaign changes; no restarts, tests, migration or cancellation performed.

Acceptance: ACCEPTED_WITH_RISK for this bounded inventory. The E3 infrastructure
decision remains INCOMPLETE. This report establishes workload presence, not
profitability, full host coverage, continuous health or execution readiness.

## Findings first

1. SHOWN: Hetzner is not idle. Four project collector processes were observed:
   crypto-edge context, corrected ES prospective paper, Gate.io daily paper and
   Binance daily paper. The latter two are detached processes despite inactive
   same-named user services. Do not infer inactivity from systemd alone.
2. SHOWN: the context archive contains substantial July-October history and a
   current running collector report. Its research role extends beyond ES.
   Cancelling the server as an ES-only cost would omit this workload.
3. SHOWN: only two backup-related files were visible under the documented user's
   backup directory, last modified June 20. UNVERIFIED: current archive/campaign
   backup coverage, off-host copies, integrity and restore success. This does
   not establish absence of other backups, but does not support safe removal.
4. SHOWN: all 12 observed companion Docker containers are on the laptop's local
   Docker socket. Hetzner has no Docker CLI in the inspected account's PATH;
   its observed project workloads are Python processes. Do not allocate the
   laptop stack's workload to Hetzner.
5. UNVERIFIED: migration time, laptop unattended uptime, new recurring costs,
   provider snapshots, root cron and two inaccessible Python process roles.
   These limits prevent a completed KEEP/DOWNSIZE/PAUSE decision, not inventory.

## Access and evidence boundary

The existing documented target is `cryptkeep@100.86.128.9`; observed hostname
was `ubuntu-4gb-nbg1-3`, user `cryptkeep`, checkout `/srv/cryptkeep/app`, revision
`580ca31e`. Connection used ordinary SSH with `BatchMode=yes`, a 10-second
connection timeout, strict existing host-key checks, host-key updates disabled
and connection multiplexing disabled. No login prompt or new credential used.

Initial sandboxed connection returned exit 255, `Operation not permitted`.
The authorized network-enabled read-only retry succeeded. VERIFIED_ENV for
this observed host and these inspection commands; not general deployment proof.
Only selected non-secret status fields, process script/module identifiers,
state-directory values and service metadata were emitted. No credential values,
full environment, raw command lines or market prices were printed.

Service/timer/process inspection, directory sizes, counts and timestamp bounds
are current SHOWN observations. SQLite was opened with `mode=ro&immutable=1`
and query-only enabled to avoid database/sidecar writes. These are main-file
counts, not transactionally certified live totals: the context DB had a
107,152-byte WAL, excluded by this method, and immutable reads of an actively
changing file are not a consistent backup or complete current snapshot.
Other inspected SQLite WAL sizes were zero at discovery, not a durable guarantee.

## Actual Hetzner workload map

Classification is provisional purpose/portability assessment, not authorization
to stop or move a workload. Needed does not by itself justify keeping this host.

| Workload | Current SHOWN evidence | Classification and dependency |
| --- | --- | --- |
| Crypto-edge context collector | System `cbp-crypto-edge-collector.service` enabled, active/running; PID 1585033; active since October 1 06:03:13 UTC. Status at 22:28:36 UTC: running, 2,946 writes, 2,946 loops, zero reported errors. | Needed for ongoing context collection; technically movable candidate, not migration-ready. Public venues, Python environment, plan and continuous uptime required. |
| Context cadence monitor | System `cbp-edge-cadence.timer` enabled/active/waiting; last 22:09:50 UTC, next 23:09:50 UTC; hourly. Associated oneshot service inactive with success, not a failed continuous daemon. | Needed companion to collector; movable with collector, archive paths and alert configuration. Alert delivery not exercised. |
| Corrected ES prospective trial | User `cbp-es-corrected-prospective.service` active/running, PID 1553065, active since September 21 01:27:11 UTC; process state path `.../.cbp_state_challengers/es_corrected_prospective_v1`. | Needed to preserve the current registered trial through its endpoint; technically movable but moving now adds continuity/identity risk. No trial modification proposed. |
| ES endpoint job | User deadline timer active/waiting for October 13 00:00:00 UTC; activates prospective-stop service. | Needed existing endpoint control. Endpoint execution and post-stop collection are not yet observed. |
| Gate.io daily paper collector | PID 1541537 running `run_paper_strategy_evidence_collector.py`, state path `.../ema_cross_gateio_btcusdt_daily`; user observation service inactive. Latest inspected equity timestamp October 11 00:15:35 UTC. | Movable candidate; active process, not idle. Current operator need/economic value UNVERIFIED. Preserve state and clarify ownership before any stop. |
| Binance daily paper collector | PID 1541539 running the same collector script, state path `.../ema_cross_binance_btcusdt_daily`; user observation service inactive. Latest equity timestamp October 11 00:19:40 UTC. | Movable candidate; active process, not idle. Current operator need/economic value UNVERIFIED. Same preservation requirement. |
| Coinbase EMA campaign | Actual host manifest has `ema_cross_default`, enabled=false; retained state; stored engine/runner stopped September 12. No matching live collector found in visible process map. | Idle retained research state, not deletion-ready; historical evidence still needs preservation. |
| Gate.io/Binance 24-hour trial states | Retained separate state directories; latest equity September 15; stored engines/runners stopped. | Idle retained evidence; no matching live trial collector found. Not interchangeable with active daily collectors. |
| System execution/dashboard surfaces | `cbp-collector`, dashboard, intent-consumer, reconciler services inactive/disabled. Dead-man timer inactive/disabled; dead-man service inactive/static. | Idle installed surfaces. No activation proposed and no proof of live execution inferred. |
| Host support | Tailscale, fail2ban, logging, network/time services, cron, atd and OS maintenance running. | Needed host support while host remains in use; not independent research justification. |

The context collector uses `sample_data/crypto_edges/live_collector_plan.json`,
300-second interval, `live_public` source, and `/var/lib/cbp` state. Deployed
system services reference `/etc/cbp/cbp.env` and `/srv/cryptkeep/app`; secret
contents were not read. Repository systemd templates use `/opt/crypto-bot-pro`,
so copying them unchanged would not preserve the observed deployed paths.
Paper collectors also depend on their isolated state, Python dependencies,
public OHLCV sources, campaign parameters and daily-loop scheduling.

## Schedules and coverage limits

SHOWN: 16 system timers listed, including cadence and OS maintenance; two user
timers listed, the ES deadline and launchpadlib cache cleanup. System maintenance
includes package updates, log rotation, filesystem trimming, sysstat and dpkg
database backup. A dpkg backup is not a CryptKeep research-data backup.

SHOWN: `cryptkeep` has no crontab; its `atq` output was empty. Visible standard
cron directory filenames were OS-maintenance entries. Root crontab and spool
ownership inspection via `sudo -n` was refused because a password is required;
no prompt or retry with credentials was attempted. Root/other-user jobs remain
UNVERIFIED. Daily collectors can self-schedule without cron/systemd timers.

Two Python processes, PIDs 879 and 1585061, could not have their environment/cwd
read due to permissions. Their roles remain UNVERIFIED; no raw arguments were
printed. This is a bounded accessible-account inventory, not an exhaustive host
or cloud-account audit.

## Data usage and counts

SHOWN: root filesystem 38 GiB, 4.5 GiB used, 32 GiB available, 13% used.
Directory allocated usage: `/var/lib/cbp` 48,632 KiB; checkout `.cbp_state`
180 KiB; `.cbp_state_challengers` 106,288 KiB. These selected directories do not
explain all filesystem usage or measure provider backup storage/billing.

| Store/table | Main-file rows observed | Timestamp coverage |
| --- | ---: | --- |
| Context funding | 22,869 | July 18 20:25:49 to October 11 22:23:23 UTC |
| Context basis | 22,869 | Same bounds |
| Context quotes | 46,953 | Same bounds; venues aggregated |
| Context open interest | 22,860 | July 18 21:16:48 to October 11 22:23:23 UTC |
| Context order books | 23,469 | Same bounds as open interest |
| `/var/lib/cbp/data/market_raw.sqlite` OHLCV / tickers | 1,096 / 0 | Timestamp bounds not obtained |
| Corrected ES paper equity / fills / orders / intents | 712 / 0 / 0 / 0 | Equity latest October 11 00:01:46 UTC |
| Gate.io daily equity / fills / intents | 34,737 / 0 / 4 | Equity latest October 11 00:15:35 UTC |
| Binance daily equity / fills / intents | 36,572 / 2 / 3 | Equity latest October 11 00:19:40 UTC |
| Retained Coinbase EMA equity / fills / intents | 86,456 / 20 / 22 | Equity latest September 12 |
| Retained Gate.io 24-hour equity / fills | 84,821 / 0 | Equity latest September 15 |
| Retained Binance 24-hour equity / fills | 84,804 / 0 | Equity latest September 15 |

Context SQLite main-file size: 48,386,048 bytes. Checkout `.cbp_state` contains
a separate empty context SQLite database; it is not the system collector's
archive. Snapshot count is not independent sample count, fill proof or alpha.
No market outcomes, returns or trade values were analyzed for this inventory.

SHOWN backup metadata: `/srv/cryptkeep/backups` contains two files, 582,312 total
bytes, one `.gz` and one `.manifest`; newest modification June 20 20:11:43 UTC.
Contents/checksums/restoration and provider snapshots were not inspected.

## Laptop versus server

SHOWN on the laptop's existing local Docker socket: gateway, orchestrator,
memory, parser, news, archive, market, risk-stub, audit-log, timescaledb, qdrant
and minio containers running. Ten report healthy; qdrant/minio report Up without
a health annotation. The count is 12, not 12 Hetzner services. Health annotations
are not end-to-end correctness or long-term uptime proof.

The prior local persistent companion checkpoint documents 55 database documents
and 55 raw-object references; these are historical observations, UNVERIFIED now
and not Hetzner row counts. E2 weekly, CMC logging and confirmation work are
documented research activities; this inspection found no proof they depend on
Hetzner. Their current scheduler status was not checked or changed.

## Portability and $60 decision boundary

CLAIMED planning cost from the operator: about $20/month, approximately $60 over
90 days and $240/year. This estimate is sufficient to begin E3; an invoice is
not a blocker. Total platform cost is not automatically incremental ES cost.

| Needed/candidate workload | Move option | One-off / recurring cost evidence | Potential loss |
| --- | --- | --- | --- |
| Context collector + cadence + archive | Laptop or smaller always-on host | UNVERIFIED: transfer, dependency/path setup, backup verification and monitoring time; replacement hosting/power cost not measured. | Laptop sleep/network outages may interrupt five-minute coverage; historical archive must survive. |
| Corrected ES trial + endpoint | Laptop or alternate host after separately reviewed continuity plan | UNVERIFIED effort; no estimate presented as fact. Existing endpoint is near, so migration adds avoidable identity/timing risk. | Registration continuity, isolated ledger ownership and endpoint behavior. |
| Daily venue challengers | Laptop, cheaper host, or operator-approved on-demand design | UNVERIFIED current need, scheduler conversion time and ongoing costs. | Daily unattended cadence and ledger continuity; on-demand is not equivalent without a scope decision. |
| Retained idle evidence | Verified off-host archive | UNVERIFIED backup/restore effort and storage coverage. | Irrecoverable historical evidence if deleted before verified preservation. |

Current memory accounting: context service 154,468,352 bytes, ES service
89,964,544 bytes at inspection. These are selected service readings, not peak
requirements or total-host utilization; cumulative CPU counters do not establish
current utilization. No supported downsizing capacity claim follows.

Chosen audit conclusion: preserve the current operating scope while E3's decision
facts are completed; do not count active detached collectors as idle or treat
the local companion stack as server load. No permanent KEEP, cancellation,
pause or migration is approved or completed. The highest-leverage next action
is a bounded preservation/portability assessment: identify a current off-host
backup with restore proof, then measure move effort and unattended uptime needs
against the approximately $60 window cost. Root-job coverage and the two unknown
process roles also need resolution before claiming exhaustive inventory.

## Sources and verification

- `docs/checkpoints/hetzner_context_coverage_2026_10_08.md`: historical system
  collector/cadence and seven-day coverage; historical facts remain UNVERIFIED
  unless refreshed above. This turn did not rerun the gap analysis.
- `docs/HETZNER_PAPER_HOST.md` and
  `scripts/report_hetzner_paper_campaign_status.py`: documented target, paths,
  non-interactive transport and status contract, inspected before connecting.
- `packaging/systemd/cbp-crypto-edge-collector.service`, cadence service/timer:
  repository dependency templates, distinguished from deployed paths.
- `docs/research/research_budget_90d_20261011.md`: E3 decision criteria; latest
  user instruction permits the working cost estimate without invoice delay.
- `docs/research/companion_persistent_check_20261011.md`: historical local
  companion evidence only; current laptop container names refreshed separately.
- Current commands: bounded SSH hostname/time, system and user service/timer
  metadata, sanitized `/proc` identifiers/state paths, `df`, `du`, read-only
  immutable SQLite aggregate counts, non-interactive cron/at inspection,
  backup metadata and local Docker container-name/status listing. SSH observations
  completed successfully; privilege-limited checks explicitly noted above.

No broad tests applicable to this documentation-only read-only inventory.
Only this new report was written; work-log entry is returned to the operator
instead of modifying the shared work log, as explicitly requested.
