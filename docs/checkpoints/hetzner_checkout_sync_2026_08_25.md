# Hetzner Checkout Sync - 2026-08-25

## Scope

Sync `/srv/cryptkeep/app` on Hetzner to current `origin/master` without
restarting services, installing packages, changing configs, or starting/stopping
campaigns.

## Pre-Sync Evidence

Read-only dependency alignment status reported:

- remote branch: `master`
- remote head before sync: `a10aca01fc37de181cc32d17a30e5d677050f901`
- expected/current master: `eb2749a280062f561ae619723d9c6f37d4efc768`
- remote git state: clean
- package alignment: blocked by 10 pinned-package mismatches

Read-only runtime checks before sync:

- Hetzner paper campaign: `1/1` running, `ema_cross_default` idle with
  `waiting_for_next_day`
- Hetzner crypto-edge runtime: ready, `blocking_checks=0`

## Commands

No-restart checkout sync:

```bash
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app fetch origin master
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app merge --ff-only origin/master
```

Post-sync verification:

```bash
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app rev-parse HEAD
tailscale ssh cryptkeep@100.86.128.9 git -C /srv/cryptkeep/app status --short --branch
make status-hetzner-dependency-alignment-json
make status-paper-hetzner
make status-hetzner-edge-runtime
```

## Results

Checkout sync:

- `git fetch origin master` exited `0`.
- `git merge --ff-only origin/master` exited `0`.
- Hetzner `/srv/cryptkeep/app` fast-forwarded from `a10aca01` to
  `eb2749a28`.
- No service restart, package install, config edit, or campaign start/stop was
  invoked.

Post-sync git verification:

- `HEAD`: `eb2749a280062f561ae619723d9c6f37d4efc768`
- status: `## master...origin/master`

Post-sync runtime verification:

- Hetzner paper campaign: `1/1` running.
- `ema_cross_default`: idle, `waiting_for_next_day`, `fills=15`, `closed=7`,
  `pnl=-2.3016`, latest fill `2026-08-24T00:01:55.857611+00:00`.
- Hetzner crypto-edge runtime: ready, `remote_head=eb2749a280062f561ae619723d9c6f37d4efc768`,
  `blocking_checks=0`.

Post-sync dependency status:

- Checkout branch and commit now match current master.
- Remote git state is clean.
- Pin integrity is OK.
- Environment alignment remains blocked by 10 package mismatches:
  `aiohttp`, `click`, `cryptography`, `GitPython`, `idna`, `pillow`,
  `setuptools`, `starlette`, `tornado`, and `urllib3`.
- `pip install --dry-run -r requirements-pinned.txt` would install the pinned
  versions for those 10 packages.
- No dependency install was performed.

## Remaining

Hetzner dependency alignment remains open and requires the approval text in
`docs/checkpoints/hetzner_dependency_alignment_runbook_2026_08_24.md` before
mutating the host virtualenv. Host vulnerability audit still requires separate
approval or waiver.
