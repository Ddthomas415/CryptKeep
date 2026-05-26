from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from services.os.app_paths import data_dir, ensure_dirs

from storage.repair_runbook_store_sqlite import SQLiteRepairRunbookStore


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_markdown(plan: dict, events: list[dict]) -> str:
    lines = []
    lines.append(f"# Repair Runbook Export")
    lines.append("")
    lines.append(f"- Exported: {utc_now()}")
    lines.append(f"- Plan ID: `{plan.get('plan_id')}`")
    lines.append(f"- Exchange: `{plan.get('exchange')}`")
    lines.append(f"- Status: `{plan.get('status')}`")
    lines.append(f"- Plan Hash: `{plan.get('plan_hash')}`")
    lines.append(f"- Created: `{plan.get('created_ts')}`")
    lines.append(f"- Approved: `{plan.get('approved_ts')}`")
    lines.append(f"- Executed: `{plan.get('executed_ts')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("```json")
    lines.append(json.dumps(plan.get("summary") or {}, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Actions")
    lines.append("```json")
    lines.append(json.dumps(plan.get("actions") or [], indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Audit Events")
    for e in events:
        lines.append(f"- **{e.get('ts')}** [{e.get('event_type')}] {e.get('message')}")
    lines.append("")
    lines.append("### Event Details (JSON)")
    lines.append("```json")
    lines.append(json.dumps(events, indent=2, sort_keys=True))
    lines.append("```")
    return "\n".join(lines) + "\n"


def try_write_pdf(md_text: str, pdf_path: Path) -> bool:
    # Optional PDF export if reportlab is installed
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except Exception:
        return False

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=LETTER)
    width, height = LETTER
    x = 36
    y = height - 36
    line_h = 12

    for raw in md_text.splitlines():
        line = raw.replace("\t", "    ")
        if y < 36:
            c.showPage()
            y = height - 36
        # truncate long lines safely
        if len(line) > 130:
            line = line[:127] + "..."
        c.drawString(x, y, line)
        y -= line_h

    c.save()
    return True


def main() -> int:
    ensure_dirs()
    droot = data_dir()
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan-id", required=True)
    ap.add_argument("--out-dir", default=str(droot / "runbook_exports"))
    args = ap.parse_args()

    store = SQLiteRepairRunbookStore(path=droot / "repair_runbooks.sqlite")
    plan = store.get_plan_sync(args.plan_id)
    if not plan:
        raise SystemExit("Plan not found.")
    events = store.list_events_sync(args.plan_id)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = args.plan_id.replace(":", "_")
    md_path = out_dir / f"{base}.md"
    json_path = out_dir / f"{base}.json"
    pdf_path = out_dir / f"{base}.pdf"

    md = to_markdown(plan, events)
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps({"plan": plan, "events": events}, indent=2, sort_keys=True), encoding="utf-8")

    pdf_ok = try_write_pdf(md, pdf_path)

    print(str(md_path))
    print(str(json_path))
    if pdf_ok:
        print(str(pdf_path))
    else:
        print("PDF_SKIPPED (reportlab not installed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
