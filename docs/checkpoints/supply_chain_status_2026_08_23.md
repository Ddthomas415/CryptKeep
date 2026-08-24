# Supply-Chain Status - 2026-08-23

## Scope

Read-only supply-chain status check for the local checkout and Hetzner host.
No dependencies were installed, upgraded, removed, or pinned by this checkpoint.

## Local Supply-Chain Audit

Command:

```bash
./.venv/bin/python scripts/check_supply_chain.py --audit --json
```

Result:

- Git SHA: `cc6c69f0588252c1838161d48c94ed553be713ac`
- Git dirty: `false`
- Pin integrity: `ok=true`, `pin_count=83`
- Environment match: `ok=true`, `checked=83`, no mismatches
- Vulnerability audit: `ran=true`, `vulnerable_count=1`

Finding:

- Package: `pip`
- Installed version: `26.1.2`
- Vulnerability: `PYSEC-2026-3721`
- Alias: `CVE-2026-13346`
- Fixed version: `26.2`
- Summary: the reported vulnerability involves mishandling doubly encoded
  package URLs from package indexes; the audit description states malicious
  package index interaction is required.

## Hetzner Supply-Chain Check Without Vulnerability Audit

Command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 cryptkeep@100.86.128.9 \
  'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --json'
```

Result:

- Git SHA: `a10aca01fc37de181cc32d17a30e5d677050f901`
- Git dirty: `false`
- Pin integrity: `ok=true`, `pin_count=83`
- Environment match: `ok=false`, `checked=83`
- Vulnerability audit: `ran=false`, `reason=not_requested`

Installed-version drift against current pins:

- `aiohttp`: installed `3.13.5`, pinned `3.14.3`
- `click`: installed `8.3.2`, pinned `8.3.3`
- `cryptography`: installed `46.0.7`, pinned `50.0.0`
- `gitpython`: installed `3.1.46`, pinned `3.1.58`
- `idna`: installed `3.11`, pinned `3.15`
- `pillow`: installed `12.2.0`, pinned `12.3.0`
- `setuptools`: installed `82.0.1`, pinned `83.0.0`
- `starlette`: installed `1.0.0`, pinned `1.3.1`
- `tornado`: installed `6.5.5`, pinned `6.5.7`
- `urllib3`: installed `2.6.3`, pinned `2.7.0`

## Host Vulnerability Audit Boundary

Attempting to run the host with `--audit --json` was not performed. The action
was rejected because a vulnerability audit may disclose the Hetzner environment
package inventory to an external vulnerability service. That needs explicit
operator approval or a documented waiver before it is run on the host.

## Interpretation

- Local supply-chain state is environment-aligned with pins, but has one
  actionable vulnerability in `pip`.
- Hetzner supply-chain state is not aligned with current pins, even before
  considering vulnerability audit results.
- The capped-live supply-chain proof remains open until the final deployed SHA
  has an aligned environment, reviewed vulnerability audit or waiver, and any
  accepted SBOM/hash-locked install decision.
