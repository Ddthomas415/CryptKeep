from __future__ import annotations
import random, time

def _exc_name(e: Exception) -> str:
    return type(e).__name__

def is_retryable_exception(e: Exception) -> bool:
    name = _exc_name(e).lower()
    msg = str(e).lower()
    hard_no = [
        "insufficientfunds","invalidorder","badrequest","authenticationerror",
        "permissiondenied","account","ordernotfound","invalidnonce","argumentsrequired"
    ]
    if any(x in name for x in hard_no) or any(x in msg for x in hard_no):
        return False
    yes = [
        "ratelimitexceeded","requesttimeout","networkerror","exchangeerror",
        "exchangeunavailable","ddosprotection","temporary","timed out","timeout",
        "too many requests","429","503","502","504","connection reset","connection aborted"
    ]
    return any(x in name for x in yes) or any(x in msg for x in yes)

def backoff_sleep(attempt: int, base_delay_sec: float, max_delay_sec: float) -> float:
    a = max(0,int(attempt))
    base = max(0.05,float(base_delay_sec))
    cap = max(base,float(max_delay_sec))
    delay = min(cap, base*(2**a))
    jitter = random.uniform(0.0,min(0.25,delay*0.15))
    sleep_for = delay + jitter
    time.sleep(sleep_for)
    return float(sleep_for)
