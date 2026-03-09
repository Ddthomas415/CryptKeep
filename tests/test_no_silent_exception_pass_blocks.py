from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_FILES = [
    ROOT / "services" / "admin" / "journal_exchange_reconcile.py",
    ROOT / "services" / "execution" / "exchange_client.py",
    ROOT / "services" / "execution" / "execution_throttle.py",
    ROOT / "services" / "execution" / "orderbook_sanity.py",
]
SILENT_EXCEPT_RE = re.compile(r"except(?:\s+Exception)?\s*:\s*pass\b")


def test_no_silent_exception_pass_blocks_in_hardened_modules():
    offenders: list[str] = []
    for path in CHECK_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in SILENT_EXCEPT_RE.finditer(text):
            lineno = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{path.relative_to(ROOT)}:{lineno}")
    assert not offenders, "Silent exception pass blocks detected:\n" + "\n".join(offenders)
