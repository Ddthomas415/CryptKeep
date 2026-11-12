# Docker identity diagnosis after the stopped R3 attempt

Bot relation: BOT_RULES; runtime configuration not checked.

Role: AUDITOR. Local evidence captured 2026-11-05T18:57:28Z; queue/work log and HEAD
`82b5f216e` checked before inspection. This closes the bounded read-only identity
inspection, not R3 or an operational repair. Native validation remains INCOMPLETE.

## Findings

- **SHOWN:** the app's local Info.plist now reports Docker Desktop **4.98.0**, build
  **245422**, bundle ID `com.docker.docker`. The reviewed proposal recorded 4.97.0.
  This is installed metadata, not independently authenticated release provenance.
- **SHOWN:** CLI SHA256 is stable before/after this inspection:
  `e6bb967adc3e97c9a9027aa7a1b83691789630cb26a4bbcddd2e8353a8a89ea4`.
  File size is 43,052,752 bytes, mode 0755, not a symlink. This differs from the
  earlier reviewed digest, not from the immediately preceding stopped attempt.
- **SHOWN:** four bounded `/usr/bin/codesign` calls were made: display and strict
  verification for the CLI, then display and strict verification for Docker.app.
  Both displays returned 0; both verifications returned 1, reporting
  `invalid signature (code or signature have been modified)` for arm64.
  Displayed TeamIdentifier is `9BNSXJN65R`, with `Authority=(unavailable)`.
  Display metadata alone is not a successful signature/trust verification.
- **UNVERIFIED:** the cause of the version/digest change and verification errors.
  An update is plausible but not demonstrated; neither tampering nor a broken
  installation is established. These checks occurred in this agent's restricted
  execution environment, without an independent outside-environment control or
  comparison to an authenticated installer. No notarization check was performed.
- **UNVERIFIED:** daemon health, running containers, cached clean-image availability,
  complete installation integrity and the seven Linux fixture results.

Machine-readable evidence: `cli_identity_20261105T185651Z.json`. The capture took
0.145 seconds; no output was truncated. Each codesign call had a 10-second timeout
within a 60-second inspection target. No timed-out call or automatic retry occurred.

## Disposition and smallest next step

Do not silently accept the new digest as a trusted baseline or bypass the failed
verification by executing Docker anyway. First independently confirm the local
signature result in the normal host environment. If it passes there, qualify the
restricted-environment finding rather than declaring the installation damaged.
If it also fails, establish official installer provenance and a data-preserving
repair plan before requesting permission to replace/restart the application.
This document authorizes none of those operational actions or another Linux run.

Docker's official documentation warns that uninstalling deletes local containers,
images and volumes. Do not run its uninstaller, factory reset, prune, or delete its
data directories as a shortcut. [Docker uninstall warning](https://docs.docker.com/desktop/uninstall/)

For a whole-VM backup, Docker says Desktop must be fully stopped; the documented
default Mac disk is `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`,
but a configured location can differ. Neither location nor backup state was checked
here, and no disk contents were read/copied. A live copy is not established as a
consistent backup. [Docker backup and restore](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/)

Docker also describes interrupted/non-atomic app copying as one cause of a damaged-app
error. That is a documented possibility, **not a diagnosis of this Mac**. Its guidance
distinguishes replacing/upgrading the application from destructive uninstallation.
[Docker Mac troubleshooting](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/)

## Scope preserved

No Docker CLI, daemon, account or credential access; no app/service startup, stop,
replacement, download, backup, container change, alert send, server access or trading.
Only local public executable/bundle metadata and signatures were inspected; receipt,
this note, PROJECT_STATE and work-log writes preserve the findings. Original attempt
receipt and reviewed packet remain unchanged. No production-source tests were needed
or run for this observational task.

What could change the conclusion: independent host verification, authenticated release
comparison, or dated update evidence. A publisher TeamIdentifier string or newer version
number alone does not resolve failed validation.

What do I know that could change the owner's decision that I have not yet said?
The version metadata changed as well as the hash, so an ordinary update is plausible;
the signature failures still need independent confirmation. Reinstallation is not yet
justified as an established fix, and uninstalling would endanger existing Docker data.

## Dated correction, 2026-11-05T20:57:28Z

Host strict signature verification passed for both Docker targets and an Apple
system control. The CLI digest matched this restricted-environment receipt before
and after the host pass. The earlier failure did not reproduce; it is not grounds
for repair. See [host confirmation](cli_host_confirmation_20261105.md). This is not
daemon, Linux-process or deployment proof, and the stopped attempt is not reset.

What do I know that could change the owner's decision that I have not yet said?
The same executable passed verification on the host; a repair is not needed on
the basis of the earlier restricted check.
