# Research scout (scheduled task, three times daily)

Purpose: an exhaustive, repeatable internet search for leads that could help CryptKeep find a real edge
or avoid a false one. The scout PROPOSES leads; it never tests, implements or adopts them.
Set up 2026-10-19 by the operator (Damian). Operator decides what, if anything, is pursued.

Files:
- TOPICS.md: 12 topic areas; each run covers one: the topic after the newest report's topic (T11 wraps to T00).
  Until 2026-10-20 the rule was (day of year mod 12).
- SEEN.csv: every lead already reported (append-only; used to avoid repeats).
- reports/YYYY-MM-DD_HHMMZ_<topic-id>.md: one report per run (run start time, UTC). Reports before 2026-10-21
  are named YYYY-MM-DD_<topic-id>.md.

Status words: every lead is UNTESTED. Facts from a source are CLAIMED until checked against a primary
source. Nothing here is evidence of an edge.

## Scheduler verification, 2026-10-19T00:10:57Z

SHOWN by read-only desktop UI inspection of the existing task
`trig_01Fk8zgs7vEVp9y54bQnziaj`: schedule active, daily at 07:43 in the displayed
local time, Require this computer on and connected, Permissions Auto, completion
notifications on with push and email selected. History says "No runs yet".
The reports folder is empty and SEEN.csv has only its header. Configured
notifications are not delivered-notification proof. A fixed UTC schedule across
daylight-saving changes has not been established.

The task's Local folder was **None**. The operator explicitly approved attaching
only `/Users/baitus/Downloads/crypto-bot-pro`, with persistent read/write access
and possible processing on Anthropic's servers. Approval covered the folder
only, not a manual run or schedule/instruction changes.

Attachment remains INCOMPLETE: native UI automation populated the exact folder
path but could not confirm the folder picker. No Save changes action occurred.
The picker is left at that path for manual confirmation, followed by Open and
Save changes. Do not request the same permission again or create a replacement
task. Reopen the existing task after saving to verify the folder, then use its
first scheduled report/run history as the execution check. No run was started.

## Folder attachment verified, 2026-10-19T00:16:23Z

This supersedes only the incomplete attachment status above. The operator
authorized resuming control of Claude to finish the already-approved setting.
The native picker selected the exact result with URL
`file:///Users/baitus/Downloads/crypto-bot-pro`, not a similarly named checkout.
After the folder permission prompt, the UI reported the existing scout updated.
Reopening Edit shows **Local folder crypto-bot-pro**, with Save changes disabled
because there are no pending edits. The saved attachment is SHOWN.

Reinspection also shows the same instructions, model Opus 5.5, daily 07:43
displayed local schedule, Auto mode, Require this computer on, and push/email
notifications enabled. No duplicate task or manual run was created. History
still says "No runs yet". First unattended execution, mounted-folder usability
inside that run and actual notification delivery remain UNVERIFIED.

## Topic focus added, 2026-10-19 (Claude Cowork, operator-requested)

A "Standing focus" paragraph was added at the top of TOPICS.md: within each topic, prefer lower-value top-100
coins and new or prospective top-100 entrants over BTC/ETH-only material, and do not propose re-running the
ENTR-CB-1 historical test (STOP). The 12 numbered topics, the day-of-year rotation, the scheduled task's
instructions, schedule and permissions are unchanged.

## Every 4 hours, 2026-10-20 (Claude Cowork, operator-requested)

The operator asked for more frequent runs and chose every 4 hours with a message after each run. The existing
task (same id, same folder, permissions and notifications) now runs at 03:43, 07:43, 11:43, 15:43, 19:43 and
23:43 UTC. Its instructions changed in four ways only: the topic is the one after the newest report's topic;
report names include the run start time; a run skips itself (writes nothing, sends one line) if the newest
report is less than 2 hours old, so a late run cannot be duplicated; and blocked sites may not be read through
mirrors or third-party front-ends (the 2026-10-20 T05 report disclosed one such read by a sub-scout). The
work-log entry must be a single append because other agents write to that file.

## Every 12 hours, 2026-10-22 (Claude Cowork, operator-requested)
The first full pass through all 12 topics finished with T03 (2026-10-22 11:44 UTC). At the operator's request
("please take care of the schedule bits") the scheduled task now runs every 12 hours, at 11:43 and 23:43 UTC
(cron `43 11,23 * * *`; first run on the new schedule 2026-10-22 23:43 UTC, topic T04). Reason: topics now repeat;
4 of the 9 reports from T04 to T00 changed nothing in the plan, and the estimated cost is 400-700k tokens a run
(UNVERIFIED). Every 12 hours rather than every 24, because the operator had asked for more frequent runs. The topic
rule, skip check, report naming and bookkeeping are unchanged. The task's prompt still says "It runs every 4 hours";
that line is descriptive only and was left as is, because changing a computer-bound task's prompt needs a separate
approval on the computer.

## Three times daily, 2026-10-28 (Claude Cowork, operator-requested)
The operator asked: "let the research scout run 3 times daily". The scheduled task (trig_01Fk8zgs7vEVp9y54bQnziaj)
now runs every 8 hours, at 03:43, 11:43 and 19:43 UTC (cron "43 3,11,19 * * *"); its name and its prompt's first
line say so, and the prompt was re-signed by the operator's desktop app. Earlier on 2026-10-27 the prompt's stale
"every 4 hours" text was corrected and the blocked-pages rule began naming release aggregators and paper-summary
sites as front-ends. Topic rule, skip check (2 hours), report naming and bookkeeping are unchanged. At three runs a
day the 12 topics cycle in 4 days, and up to 30 new leads a day need sorting.

## Weekly, 2026-10-30
- Operator approved the POP approach (AGENTS.md "Primary Objective Protection"). Scheduled task trig_01Fk8zgs7vEVp9y54bQnziaj
  changed from "43 3,11,19 * * *" to "43 11 * * 1" (Mondays 11:43 UTC) and renamed "CryptKeep research scout (weekly)".
  First weekly run 2026-11-02T11:43Z. The prompt's first line still says "three times a day"; it was not changed,
  because a prompt change needs re-approval on the operator's computer. Topic rotation is unchanged.
- Scout leads are parked information under POP: nothing in a report starts work unless the owner moves it into a queue.
