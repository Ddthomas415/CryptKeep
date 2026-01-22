from __future__ import annotations
import time
from services.execution.retry_policy import is_retryable_exception, backoff_sleep
def _norm_status(s: str | None) -> str:
    return str(s or "").lower().strip()
def wait_for_order_final(
    *,
    ex,
    symbol: str,
    order_id: str,
    timeout_sec: int = 30,
    poll_sec: float = 2.0,
) -> dict:
    t0 = time.time()
    last = None
    attempts = 0
    while (time.time() - t0) <= float(timeout_sec):
        attempts += 1
        try:
            o = ex.fetch_order(order_id, symbol)
            last = o
            st = _norm_status(o.get("status"))
            if st in ("closed", "canceled"):
                return {"ok": True, "final": True, "order": o, "attempts": attempts}
        except Exception as e:
            if is_retryable_exception(e):
                backoff_sleep(attempt=max(0, attempts-1), base_delay_sec=0.2, max_delay_sec=2.0)
            else:
                return {"ok": False, "final": False, "error": f"{type(e).__name__}:{e}", "attempts": attempts, "order": last}
        time.sleep(float(poll_sec))
    return {"ok": True, "final": False, "timeout": True, "attempts": attempts, "order": last}
