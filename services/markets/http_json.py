from __future__ import annotations
import json, ssl, urllib.request
from typing import Any, Dict, Optional

def get_json(url: str, timeout_s: float = 10.0, headers: Optional[Dict[str,str]] = None) -> Any:
    req = urllib.request.Request(url, headers=headers or {})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=float(timeout_s), context=ctx) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="replace"))
