# Restore Existing Research Collector

ENGINEER operational plan,2026-10-29. HIGH risk. User's latest continuation
answers the explicit question to restore the existing research-only300s loop,
continuing archive/PID/status writes, with no scheduled job or trading changes.
It does not authorize accounts, credentials, new collectors or unrelated work.

Reuse the accepted CLI/source and full-family paired settings from the accepted
single-cycle record. Copy plan/options to a new timestamped diagnostic folder;
do not modify active sample config or any existing job. Source live_public,
original local research archive, poll300, raw1row/4MiB and the same funding2GET/
30s/10s/1MiB options. The sole behavioral launch change is max-loops0 to keep
the existing loop running. Additional public SDK calls remain outside funding
limits. The ongoing loop deliberately continues collection on future cycles;
there is no automatic re-launch after startup failure, sleep or reboot.

Before launch, verify accepted source inputs, inspect exact savedPID/script/
archive handles, require no current collector/stopflag and preserve a coherent
fresh pre-start SQLite backup via a mode=ro source and SQLite backup to a NEW
file. Record counts/maxIDs and control hashes. Unknown ownership means no start.

One exclusive launch marker. Start the existing CLI with Python subprocess
Popen(start_new_session=True, stdin/stdout/stderr=DEVNULL), matching the existing
background-launch mechanism in dashboard/services/operator.py. Explicit clean
environment PATH/PYTHONDONTWRITEBYTECODE/CBP_STATE_DIR only. No API key, secret,
proxy, token or private account is supplied. This is not a new launchd/systemd
job or deployment. Retain the Popen handle while checking startup.

Wait at most180s for the new ownedPID's status to show its first completed
cycle; poll existing local JSON every2s rather than issuing repeated network
requests. Require errors0/last_ok, paired capture1/0failed, sixsuccessful checks,
expected counts0legacy/1raw/1OI/1basis/2quotes/1book and execution disabled in
that collection result. Read-only persisted IDs/source/identity/raw validation,
all-family cadence and unchanged prior row prefixes must also pass before the
process is deliberately left running. Take a sealed readback snapshot for
separate review. Do not score strategies or claim financial qualification.

On failure/cancellation before acceptance, call the already-reviewed
okx_full_cycle_20261029/bounded_cycle.py stop_owned helper on ONLY the retained
Popen handle: TERM/5s then KILL/5s if still active. Do not kill an unowned PID,
set a global stop flag, clear/reset another process's files, restore a DB,
delete rows or re-launch. Partial writes/control files may persist; preserve
receipts and state. This startup observation window is not a hard overall
deadline on process creation, hashing, SQLite/verification or final writes.
After successful verification, leave the child running and perform a separate
scoped host PID/script check after the launching tool process has exited.

No source implementation change is proposed. Existing source and one-shot
helper acceptances, tests and runtime evidence remain separate from this
recurring operational acceptance. Binary signature trust, sustained freshness,
historical funding semantics and financial edge remain UNVERIFIED. One successful
startup cycle is not proof that later cycles, reboot recovery or scheduled
monitoring will work. No monitor job or new automation is installed here.
