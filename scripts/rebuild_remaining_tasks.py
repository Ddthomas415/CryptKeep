#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Row:
    symbol: str
    label: str
    text: str
    line_no: int


SYMBOLS = {
    "🔄": "In progress",
    "🟡": "Partial",
    "⏳": "Not started",
    "⚠️": "Constraint / Note",
}


def _parse_rows(lines: list[str]) -> list[Row]:
    rows: list[Row] = []
    for idx, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line.startswith("- "):
            continue
        matched = False
        for symbol, label in SYMBOLS.items():
            token = f"- {symbol} "
            if line.startswith(token):
                rows.append(
                    Row(
                        symbol=symbol,
                        label=label,
                        text=line[len(token) :].rstrip(),
                        line_no=idx,
                    )
                )
                matched = True
                break
        if matched:
            continue
    return rows


def _render(rows: list[Row]) -> str:
    in_progress = [r for r in rows if r.symbol == "🔄"]
    partial = [r for r in rows if r.symbol == "🟡"]
    not_started = [r for r in rows if r.symbol == "⏳"]
    notes = [r for r in rows if r.symbol == "⚠️"]
    total = len(rows)

    def _section(title: str, icon: str, items: list[Row]) -> list[str]:
        out = [f"## {icon} {title} ({len(items)})", ""]
        for r in items:
            out.append(f"- {r.text}")
            out.append(f"  Source: `CHECKPOINTS.md:{r.line_no}`")
        out.append("")
        return out

    lines: list[str] = []
    lines.append("# Remaining Tasks")
    lines.append("")
    lines.append("Source: `CHECKPOINTS.md`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total non-✅ items: {total}")
    lines.append(f"- 🔄 In progress: {len(in_progress)}")
    lines.append(f"- 🟡 Partial: {len(partial)}")
    lines.append(f"- ⏳ Not started: {len(not_started)}")
    lines.append(f"- ⚠️ Constraint/note: {len(notes)}")
    lines.append("")
    lines.extend(_section("In Progress", "🔄", in_progress))
    lines.extend(_section("Partial", "🟡", partial))
    lines.extend(_section("Not Started", "⏳", not_started))
    lines.extend(_section("Constraint / Note", "⚠️", notes))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checkpoints = root / "CHECKPOINTS.md"
    remaining = root / "REMAINING_TASKS.md"

    lines = checkpoints.read_text(encoding="utf-8").splitlines()
    rows = _parse_rows(lines)
    remaining.write_text(_render(rows), encoding="utf-8")
    print(
        {
            "ok": True,
            "checkpoints": str(checkpoints),
            "remaining": str(remaining),
            "total_non_done": len(rows),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
