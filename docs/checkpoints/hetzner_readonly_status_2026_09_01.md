# Hetzner Read-Only Status - 2026-09-01

Status: host paper campaign and crypto-edge runtime are healthy; release-policy
vulnerability audit remains blocked by missing `pip-audit`.

## Scope

- SHOWN: commands were run over regular SSH to the Tailscale IP after the
  Tailscale browser check cleared.
- SHOWN: no service restart, deployment, package install, config edit,
  campaign start/stop, gate change, live routing, or execution action was run.
- SHOWN: Hetzner checkout is clean on `master` at
  `c7bd305287792993d0a63e01e9bdc5ad3cfacf6e`.

## Commands

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/check_supply_chain.py --audit --json'
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && ./.venv/bin/python scripts/report_supervised_soak_status.py --config configs/paper_evidence_campaigns.hetzner.example.json --json'
ssh -o BatchMode=yes -o ConnectTimeout=15 cryptkeep@100.86.128.9 'systemctl --user --no-pager --plain status cbp-crypto-edge-collector.service cbp-edge-cadence.timer 2>/dev/null || systemctl --no-pager --plain status cbp-crypto-edge-collector.service cbp-edge-cadence.timer 2>/dev/null || true'
```

## Result

Supply-chain:

- SHOWN: `pin_integrity.ok=true`, `pin_count=83`.
- SHOWN: `environment.ok=true`, `checked=83`, `mismatches=[]`,
  `not_installed=[]`.
- SHOWN: `vulnerability_audit.ran=false`,
  `vulnerability_audit.reason=pip_audit_unavailable`.

Paper campaign:

- SHOWN: Hetzner paper status reported `all_running=true`,
  `running_count=1`, `campaign_count=1`.
- SHOWN: `ema_cross_default` is idle with reason `waiting_for_next_day`.
- SHOWN: latest completed day is `2026-09-01`.
- SHOWN: totals are `fills_total=16`, `closed_trades_total=8`,
  `net_realized_pnl_total=-2.3182583698061814`.

Crypto-edge runtime:

- SHOWN: `CBP_STATE_DIR=/var/lib/cbp` edge cadence returned `ok=true`,
  `missing=[]`, and `stale=[]`.
- SHOWN: OKX funding, open-interest, and basis snapshots were fresh at
  `2026-09-01T04:05:10+00:00`.
- SHOWN: `cbp-crypto-edge-collector.service` is active and running.
- SHOWN: `cbp-edge-cadence.timer` is active and waiting.

Transport note:

- SHOWN: the repo status wrapper path that invokes Tailscale SSH reported a
  strict host-key failure for `100.86.128.9`.
- SHOWN: regular SSH over the same Tailscale IP succeeded in batch mode after
  the Tailscale browser approval completed.

## Remaining Risk

- LOW: read-only host status checkpoint. No host state was changed.
- Release-policy proof remains open until `pip-audit` is installed/enabled on
  the host or the vulnerability-audit requirement is explicitly waived.
- Local master contains newer commits than the host checkout after PR #563; no
  host sync was attempted in this checkpoint.
- Acceptance state: `ACCEPTED`.
