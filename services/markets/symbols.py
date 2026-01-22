from __future__ import annotations
import re
from typing import Tuple

def canonicalize(sym: str) -> str:
    s = (sym or "").strip().upper()
    s = s.replace("/", "-").replace("_", "-")
    s = re.sub(r"-{2,}", "-", s)
    return s

def split(sym: str) -> Tuple[str,str]:
    s = canonicalize(sym)
    if "-" not in s:
        return s, ""
    a,b = s.split("-", 1)
    return a,b

def binance_native(canonical: str) -> str:
    a,b = split(canonical); return f"{a}{b}" if b else a

def gate_native(canonical: str) -> str:
    a,b = split(canonical); return f"{a}_{b}" if b else a

def coinbase_native(canonical: str) -> str:
    return canonicalize(canonical)
