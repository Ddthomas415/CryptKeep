# Supply-Chain Local Remediation - 2026-08-23

## Scope

Local project virtualenv remediation for the `pip` vulnerability recorded in
`docs/checkpoints/supply_chain_status_2026_08_23.md`.

No repo dependency pins, host packages, SBOM policy, CI policy, runtime code,
campaigns, gates, risk logic, live/shadow execution behavior, or Hetzner state
were changed by this checkpoint.

## Remediation

Command:

```bash
./.venv/bin/python -m pip install --upgrade pip==26.2
```

Result:

- Previous local `pip`: `26.1.2`
- Remediated local `pip`: `26.2`
- Reason: local `pip-audit` reported `PYSEC-2026-3721` /
  `CVE-2026-13346` against `pip 26.1.2`; audit metadata listed `26.2` as the
  fixed version.

## Verification

Command:

```bash
./.venv/bin/python -m pip --version
```

Result:

- `pip 26.2` from the project virtualenv.

Command:

```bash
./.venv/bin/python scripts/check_supply_chain.py --audit --json
```

Result:

- Git SHA: `a4a555d539ae0d4634443f7c81a798063a2fed69`
- Git dirty: `false`
- Pin integrity: `ok=true`, `pin_count=83`
- Environment match: `ok=true`, `checked=83`, no mismatches
- Vulnerability audit: `ran=true`, `vulnerable_count=0`, `findings=[]`

Audited evidence artifact:

- `.cbp_state/data/supply_chain/supply-chain-evidence-20260824T011230Z.json`

## Remaining Boundary

- Hetzner still requires environment alignment against the current pins.
- Host vulnerability audit remains unrun because it may disclose host package
  inventory externally; it needs explicit operator approval or a documented
  waiver.
- Hash-locked install and SBOM requirements remain release-policy decisions.
