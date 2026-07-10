#!/usr/bin/env python3
"""
Operator clock-sanity report (launch-evidence artifact).

Prints host UTC time, best-effort NTP sync status, and measured clock skew
against each requested venue's server time, with a verdict against
CBP_MAX_CLOCK_SKEW_MS.

Exit codes: 0 = all measured venues within threshold; 1 = at least one
venue exceeded the threshold; 2 = no venue could be measured.

Usage: python3 scripts/check_clock_sanity.py [venue ...]   (default: coinbase)
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.execution.clock_sanity import max_clock_skew_ms, measure_venue_skew  # noqa: E402


def _ntp_status() -> str:
    """Best-effort host NTP sync status; degrades to 'unavailable'."""
    probes = (
        ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
        ["chronyc", "-c", "tracking"],
    )
    for cmd in probes:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if out.returncode == 0 and out.stdout.strip():
                return f"{cmd[0]}: {out.stdout.strip().splitlines()[0]}"
        except Exception:
            continue
    return "unavailable"


def main(argv: list[str]) -> int:
    venues = [v.strip().lower() for v in argv[1:] if v.strip()] or ["coinbase"]
    threshold = max_clock_skew_ms()

    print(f"host_utc: {datetime.now(timezone.utc).isoformat()}")
    print(f"ntp_status: {_ntp_status()}")
    print(f"threshold_ms: {threshold:.0f}")

    exceeded = 0
    measured = 0
    for venue in venues:
        try:
            import ccxt

            ex_cls = getattr(ccxt, venue, None)
            if ex_cls is None:
                print(f"venue={venue} status=unknown_venue")
                continue
            ex = ex_cls()
            try:
                m = measure_venue_skew(ex)
            finally:
                try:
                    if hasattr(ex, "close"):
                        ex.close()
                except Exception:
                    pass
        except Exception as exc:
            print(f"venue={venue} status=probe_error reason={type(exc).__name__}:{exc}")
            continue

        if not m.get("supported"):
            print(f"venue={venue} status=limitation reason={m.get('reason')}")
        elif not m.get("measured"):
            print(f"venue={venue} status=unmeasured reason={m.get('reason')}")
        else:
            measured += 1
            skew = float(m["skew_ms"])
            rtt = float(m["rtt_ms"])
            verdict = "OK" if abs(skew) <= threshold else "EXCEEDED"
            if verdict == "EXCEEDED":
                exceeded += 1
            print(f"venue={venue} status={verdict} skew_ms={skew:.0f} rtt_ms={rtt:.0f}")

    if exceeded:
        return 1
    if measured == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
