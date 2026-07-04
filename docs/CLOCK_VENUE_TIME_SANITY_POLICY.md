# CryptKeep Clock and Venue-Time Sanity Policy

Status: `POLICY_DOCUMENTED`

## Purpose

Define the timestamp and clock-sanity proof required before relying on
timestamp-sensitive shadow or capped-live evidence.

## Why This Matters

Funding age, candle boundaries, order timestamps, reconciliation windows,
slippage measurement, and daily evidence windows all assume UTC clock
correctness. A healthy strategy can produce misleading evidence if host time or
venue time is materially wrong.

## Current Boundary

SHOWN:

- Paper campaigns record one evidence window per UTC day.
- Hetzner host docs already require UTC/NTP synchronization in the server
  health packet.
- Several strategy/evidence paths use UTC timestamps in stored artifacts.

UNVERIFIED:

- No general host-to-venue skew check is a required launch gate.
- No operator-visible clock status artifact is required before shadow/live.
- No proof packet shows funding, candle, order, and reconciliation timestamps
  checked against the same clock source.

## Required Checks Before Shadow Cost Evidence

Before treating shadow slippage/cost evidence as decision-grade:

- host clock is synchronized to UTC/NTP;
- venue server time is queried when the venue exposes it;
- observed host-to-venue skew is recorded;
- quote/fill/signal records carry timezone-aware timestamps;
- stale-data thresholds are evaluated against monotonic or UTC-safe sources;
- evidence reports include the clock-check timestamp.

## Required Checks Before Capped Live

Before capped-live approval, add a launch-packet proof showing:

- host UTC/NTP status;
- venue time query result or documented venue limitation;
- max allowed skew threshold and observed value;
- behavior when skew exceeds threshold;
- reconciliation window sanity using real or sandbox venue timestamps;
- operator-visible status command output.

Until that proof exists, timestamp-sensitive live/shadow evidence remains
incomplete.

