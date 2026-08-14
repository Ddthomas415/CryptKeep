# Clock/Venue-Time Host Proof - 2026-08-13

Status: read-only host proof recorded.

Command was run from `/Users/baitus/Downloads/crypto-bot-pro` against the
Hetzner host over the accepted Tailscale SSH path. No service was restarted and
no runtime state was mutated.

## Command

```bash
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_clock_sanity.py --json coinbase okx'
```

Note: on the deployed host version, `--json` is not a recognized flag for this
script and was reported as `venue=--json status=unknown_venue`; the Coinbase
and OKX checks still ran and returned explicit venue measurements.

## Result

- SHOWN: `host_utc=2026-08-13T23:56:27.797371+00:00`.
- SHOWN: `ntp_status=timedatectl: yes`.
- SHOWN: `threshold_ms=5000`.
- SHOWN: `venue=coinbase status=OK skew_ms=-409 rtt_ms=190`.
- SHOWN: `venue=okx status=OK skew_ms=42 rtt_ms=326`.

## Boundary

This closes a read-only host/venue-time evidence refresh for the checked
Coinbase and OKX venues at the recorded timestamp. Future launch packets should
refresh this proof close to any shadow/capped-live transition.

This proof does not authorize live trading, live routing, strategy promotion,
credential deployment, or service restarts.
