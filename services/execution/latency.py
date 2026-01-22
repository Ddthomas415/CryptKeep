from __future__ import annotations
import random
import time
from typing import Tuple
from services.config_loader import load_user_config

def load_latency_ms() -> Tuple[int, int]:
    cfg = load_user_config()
    ex = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    lat = ex.get("paper_latency_ms", [0, 0])
    try:
        a = int(lat[0]); b = int(lat[1])
        if a < 0: a = 0
        if b < a: b = a
        return a, b
    except Exception:
        return 0, 0

def sleep_paper_latency() -> int:
    a, b = load_latency_ms()
    if a == 0 and b == 0:
        return 0
    ms = random.randint(a, b)
    time.sleep(ms / 1000.0)
    return ms
