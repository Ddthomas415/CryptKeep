# Hetzner Prospective Launch Package

## Independent Review Correction

Human acceptance on 2026-09-09: user explicitly accepted correction a188e800f.
Acceptance state: ACCEPTED (human, seed-check correction). Prior implementation
status below is historical. Host validation and shutdown rehearsal are still
separate, unverified steps; no launch follows from this acceptance alone.

Reviewer found that the in-memory config test could pass even if the seed was
never installed. The package now includes a second ExecCondition requiring the
exact generated seed SHA256 at
/srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1/runtime/config/user.yaml.
The loose package user.yaml must be placed at precisely that destination in
new state; absence, unreadability, symlink or changed bytes refuse startup.
Real file-loader test exercises configuration resolution and missing/mismatched
seed refusal. Targeted suite: 32 passed. Host deadline rehearsal remains pending
Tailscale SSH authentication; no remote changes have been performed.
This correction is READY_FOR_INDEPENDENT_REVIEW, not covered by the earlier
acceptance of f841608e2.

## Human Acceptance

2026-09-09: user explicitly accepted implementation f841608e2 with
INDEPENDENT REVIEW ACCEPTED. Acceptance state: ACCEPTED (human, package only).
This does not claim completed subagent review or host validation. Implementation
history below is preserved. No installation or launch is authorized by this
acceptance record; host unit verification and shutdown rehearsal remain next.

Active role: ENGINEER. HIGH risk. Uninstalled, no campaign launch.

scripts/research/build_es_trial_package.py renders files into a new output
directory only; no systemctl, SSH, deployment, enable or start operation occurs.
Caller chooses next UTC midnight as evaluation start; stop timestamp is fixed
30 days later. Regeneration is a new review artifact, not permission to extend
an existing trial. The recorded start is provisional until actual launch proof.

Generated user service runs collector foreground in the dedicated challenger
state. Requires persistent absolute-calendar stop timer, Restart=no,
KillMode=control-group, 30-second stop timeout with SIGKILL. An ExecCondition
refuses starts at/after expiry; restarting does not reset the absolute timer.
RuntimeMaxSec=31d is secondary containment, not the evaluation endpoint.
Deadline is a stop request with timer scheduling tolerance and shutdown grace,
not an assertion of instantaneous termination. None of the units has [Install].

Proposed state-local user.yaml (JSON syntax accepted by YAML loader) explicitly
sets SMA200/ATR20, four zero runner exit controls, .001 BTC order quantity,
10000 USDT starting cash, 7.5 bps fee and 5 bps slippage. These numeric cost/size
values match local effective config inspection; they are NOT verified Hetzner
settings. Only a new empty state may receive this seed. Never replace existing
state or copy a credential-bearing user config. No explicit override environment
may silently replace these values: inspect the actual child before launch.

Tests use both real config resolvers against generated config, absolute-deadline
boundary tests, invalid-start refusal and unit contract assertions. Targeted
package/manifest/recovery run: 31 passed. No real systemd timeout proof yet.

## Required Host Review Before Installation

- Verify exact accepted commit on host and run systemd-analyze --user verify on
  a temporary rendered package, not installed units.
- Run a short dummy process-tree deadline rehearsal; prove group termination
  and expired-start refusal, without touching current campaign services.
- Verify designated state is absent, actual child environment/config including
  size/cost/identity, read-only public-source reachability and no live route.
- Confirm launch before the specified midnight; otherwise discard/review a new
  package. Record UTC start/end, effective hashes and seven-day inspection.
- Installation/start remains a separate authorized operation. Do not register
  this through the generic --detach campaign restore path: it bypasses these
  unit controls. No canonical campaign, cohort or evidence changes are included.

Full-system proof remains UNVERIFIED. Acceptance state:
READY_FOR_INDEPENDENT_REVIEW.
