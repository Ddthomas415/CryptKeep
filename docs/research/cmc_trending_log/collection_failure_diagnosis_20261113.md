# CMC scheduled collection: read-only failure diagnosis

Bot relation: STANDALONE public research collection; runtime trading configuration not checked.

Checked **2026-11-13T19:01:45Z**. Active role AUDITOR. Self-checked local-file and visible-UI evidence, not independent operational certification. Read-only investigation complete at the boundary below; collection restoration remains INCOMPLETE.

## Answer

**SHOWN:** today's existing CMC task has a history entry at08:52NewYork/13:52UTC marked "Ran on schedule". Its chat shows "No matching tools found", not a successful computer command. The task is active, requires this Mac and already has access to the correct repo folder.

**CLAIMED by that run, visibly recorded:** computer-command connection failed before the logger started, with `remote-devices (503)` and `CLIENT_HTTP_NOT_IMPLEMENTED`. This is a failure at the task-to-computer-tool discovery/connection boundary, not demonstrated failure of CMC, Coinbase, certificate validation or the logger's publisher.

**UNVERIFIED:** the underlying reason for that connection failure. The displayed error is in the run's assistant summary; the raw SDK/HTTP backend trace is not exposed by the inspected view. There is no basis here for diagnosing expired sign-in, absent folder permission, a particular proxy, application-version incompatibility, a vendor outage or sleep as today's cause. Current "Connected" state does not prove state at13:52UTC.

**No code repair, re-login, permission expansion, task replacement or new collector is justified by this evidence.** No such action was performed.

**Material coverage qualification, found2026-11-13T19:03:55Z:** the separate [registered timing amendment](primary_analysis_schedule_20261010.md#coverage-and-refusal) requires valid observations throughout the fixed November10-February7 primary entry window, not only30preceding days for later entrants. On the inspected evidence, the absent November10/11 observations make the registered primary study **INCOMPLETE** unless genuine contemporaneously captured evidence for those dates can be located elsewhere. The later December eligibility dates below describe the30-day rule only; they do not salvage this fixed-window primary study. This source correction narrows the earlier work-log/cohort-only summaries, including my18:54audit and the first version of this note. A late retrieval, manual current-day observation, extra56days or silent window shift cannot repair the registered coverage requirement. No outcomes were scored and no study was restarted.

## Task and execution evidence

- Existing task: [CryptKeep daily CMC trending log](https://claude.ai/scheduled-task/trig_012ybaBYn3NNN3cqx38BTRjV).
- Task detail UI showed Active, enable switch on, Requires this computer (MacBook Pro), Connected, Daily08:52NewYork and next run tomorrow08:52. The folder is `~/Downloads/crypto-bot-pro`, with "Allowed for this task on this computer". These are current settings, not proof of future dispatch.
- [November13 run](https://claude.ai/chat/1c3b11a4-21c6-806e-aec0-c0b37f3c0b6e): "Ran on schedule"; "No matching tools found"; assistant reports the redacted503/CLIENT_HTTP_NOT_IMPLEMENTED failure and says no files were read/changed. UI also displays "Sent notification"; recipient delivery/read is not verified. No successful computer-command receipt is shown.
- [November12 run](https://claude.ai/chat/c9508786-2e18-89e3-a562-d5364ca27486): inspected the actual saved command and response, not just its summary. It invoked the existing v3 logger via the connected Linux folder, then a second saved command inspected the output and returned `3 OBSERVED 0`. These are historical tool receipts viewed read-only; neither command was rerun.
- Its executed command was `cd "$HOME/mnt/crypto-bot-pro" && python3 -B docs/research/cmc_trending_log/cmc_trending_logger_v3.py --out docs/research/cmc_trending_log/snapshots --identity-map docs/research/cmc_trending_log/identity_map_contract_v1.json --capture-level1`. This is the task sandbox's path/runtime, not a suggested command for the Mac host.
- The task history has no visible November10/11 scheduled08:52 entries. A November11 23:43NewYork entry corresponds to November12 UTC and cannot be relabeled as either missed UTC day. The original cause of those earlier missing slots remains UNVERIFIED; today's connector failure does not retrospectively explain them.

Read-only UI navigation opened this existing task/run history and its prior tool receipts, then restored the owner's original handoff chat and closed the activity panel. No prompt was sent, Run now/Retry was not clicked, no task or permissions were edited. Reading a prior unread run may update its UI unread marker; this is not a collection or schedule change.

## Local output and publisher checks

**SHOWN:** there is no filename-dated November13 snapshot and no newer local file metadata in the snapshot directory. The latest retained payload is November12 13:52UTC, matching the successful run's exact filename. Both November12 payloads locally parse as schema3, OBSERVED, source_errors count0:

| File | SHA256 |
| --- | --- |
| `v2_2026-11-12_044427_751878Z_e9649ebfbbca45ceb899017023e9a363.json` | `20cbe813de1fd9fb7d0b7e0a38005505dab3d567edcefb713889a73a96429dd0` |
| `v2_2026-11-12_135247_863505Z_00c1d10f78234391bd85c957fd0577c1.json` | `75eb44392abf86b76996ce95f466709d2232875365ac5256466f82ea7eb1f0dc` |

November12's actual command response warns that cleanup of `.pending_gitu701v` was denied. Its completed snapshot exists, and the v2 publisher catches PermissionError only for temporary-file cleanup after its immutable publication attempt. That warning did not prevent the demonstrated success and is not evidence for today's pre-command failure. No temporary files were deleted or permissions changed.

Inspected v3's collect/main, its verified-request/TLS repair contract and v2's save path. This source evidence does not prove that today's task imported Python, acquired the lock, contacted a market endpoint or attempted publication; no such execution was observed. No new tests were run because no source changed, and another test suite could not reproduce an unavailable task connector's historical backend state.

Source identities read for preservation, not fresh runtime acceptance:

```text
cmc_trending_logger_v3.py
1ecd91cb88b85ecb5bb0ba76a0ead88561e18f7e02979a61ea4e14afbb3f8198
cmc_trending_logger_v2.py
4c10d5262c790a91051801ef73eeeca3f8d6a4ab8a9a5cb41da0884d51bcc200
identity_map_contract_v1.json
f13333a8bfb4eecd6b3e5bf03eaec922d17f4726933b5e6aa1dfd9396ac4ab22
```

## Minimum next action and data consequence

The current evidence is enough to avoid repairing the wrong component; it does not prove the connector has recovered.

1. **Immediate continuity proposal, not executed:** authorize one bounded foreground capture with the existing reviewed logger from Codex's Mac environment, preserving its actual current UTC timestamp and original rules. This bypasses the failed Claude task connection for one observation; it does not repair or prove the unattended task. No source, schedule, folder, permission or system-trust change is required merely to propose this route. It still needs explicit public-data execution scope and a time/request limit justified from the existing collector, not the unrelated E1 ten-GET budget.
2. **Scheduler recovery remains separate:** if needed, authorize a connection-only check in the actual task environment or obtain sanitized vendor/runtime diagnostics of the503 boundary before further intervention. Do not run repeated captures, create duplicates or replace a task that demonstrably dispatched. Current app/folder Connected indicators alone are insufficient acceptance proof; a future scheduled command and valid output must be observed.
3. **Preserve the gaps:** do not download today's list and label it November10/11, reconstruct missed observations as contemporaneous, score results early or change the primary window. A manual current-day snapshot is evidence only for its real observation time.

Under the [adopted30-day coverage rule](cohort_coverage_decision_20261009.md), November10/11 gaps already affect primary eligibility. November13 is currently absent but its UTC day has not yet ended. **If it ends without a valid observation**, the earliest calendar day with30complete preceding days becomes **December14** assuming valid observations every day November14-December13. This leaves56possible entry dates before the registered February8exclusive cutoff, not56guaranteed entries or a sufficient statistical sample. A valid actual November13 observation could avoid this additional delay, but cannot repair November10/11 or guarantee any coin's identity/cohort qualification.

Cause class: supported operational tool-discovery/connection failure, with lower-level causation insufficiently evidenced; earlier missing dispatch slots remain insufficient evidence. No ineffective-signal, execution-cost or strategy-profit conclusion follows.

## Acceptance and limits

**DONE:** local source/output/history/settings inspection, last-success comparison, supported failure stage and minimal non-destructive proposal.
**NOT DONE:** raw backend trace, actual current task-executor connection check, run/repair, recovery/unattended proof, prior missing-slot causation, endpoint/data validation beyond existing payload metadata, new observation, cohort scoring or profitability assessment.

No app restart, power/network/settings change, credential/account access, services/servers, schedule/task/source/config change, capture, trading, install, commit or push occurred. Only this report and required work-log/current-state bookkeeping are written. The frozen BTC/ETH criteria remain unchanged; a CMC failure does not invalidate that separate tracker automatically.

What do I know that could change the owner's decision that I have not yet said?

Today's task did start; the failure was reported before it could obtain the tool needed to run the logger. Starting another scheduler would not address that evidence. There is still a limited current-day opportunity for a genuine manually dated observation, but even a successful manual capture would not establish that tomorrow's unattended run is reliable.

## Dated correction to the minimum-action recommendation

2026-11-13T19:04:49Z: preservation-first interpretation after reading the full primary timing amendment. The manual-capture proposal above is for optional ongoing diagnostic continuity only; **it is not a rescue of the registered primary result and should not be prioritized under that mistaken premise**. Current task remains read-only. First determine whether valid contemporaneous November10/11 records exist outside the inspected archive. A filename search of `docs/research` found no matching November10/11 JSON names; this is not an exhaustive search of unmounted backups, external storage or unnamed archives. No backup tool was run or cloud account accessed. If contemporaneous coverage cannot be established, retain the original primary study as INCOMPLETE; any replacement future window requires a separately approved prospective amendment. Existing snapshots/collector are preserved; no automatic shutdown, rewrite or new schedule follows.

What do I know that could change the owner's decision that I have not yet said?

Repairing collection reliability does not restore this primary study's missing historical days. Continued diagnostic collection may still be useful, but it must not be sold as repairing confirmatory evidence or as a reason to keep building without an owner decision on the study's future.

## Final verification and bounded independent coverage review

Read-only payload-date check read all43local JSON snapshots: none has snapshot_utc, hidden-list request-start or received date November10,11or13, and none references a history-source filename on those dates. This is stronger than a filename-only check, but still does not establish absence from uninspected external archives. No snapshot was written or modified.

Separate Nash GATE `01a1cee8-b4ec-7343-9992-b771df07aba1`, checked **2026-11-13T19:06:28Z**, returned **ACCEPTED_WITH_RISK for coverage interpretation only; no blocking overstatement in the qualified claim**. Reviewer read the actual timing amendment and coverage rule, inspected local filename absence and checked the conditional calendar math. Confirmed current fixed-window primary INCOMPLETE on inspected evidence unless contemporaneous records are found elsewhere;30-day eligibility does not rescue it. Reviewer did not inspect Claude UI/tool availability or independently certify the reported503cause. No tests, network, edits, UI actions, scoring or collection.

What do I know that could change the owner's decision that I have not yet said?

There are two separate outstanding decisions: recover reliable collection, and determine this registered study's disposition from contemporaneous evidence. Solving the former cannot silently substitute a new experiment for the latter. The BTC/ETH forward tracker is a different study and remains governed by its own frozen criteria.
