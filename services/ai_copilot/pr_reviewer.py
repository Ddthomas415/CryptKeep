from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.ai_copilot.policy import (
    PROTECTED_PATH_PREFIXES,
    is_protected_path,
    report_root,
    requires_human_approval,
)
from services.ai_copilot.providers import call_llm

_LLM_SYSTEM_PROMPT = """You are the CryptKeep Repo Copilot reviewer.

You review repo changes and produce a concise engineering note.

Hard constraints:
- Never recommend bypassing live guards, reconciliation, or operator approval
- Never suggest direct database edits or production hotfixes without review
- Call out when human approval is required

Return:
1. One-paragraph risk summary
2. 2-5 focused recommendations
3. One sentence on missing proof if evidence is thin
"""


def _normalize_paths(paths: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized = {
        str(path or "").replace("\\", "/").lstrip("./")
        for path in (paths or [])
        if str(path or "").strip()
    }
    return sorted(normalized)


def _risk_tier(changed_files: list[str]) -> str:
    if any(is_protected_path(path) for path in changed_files):
        return "red"
    if any(path.startswith(("dashboard/", "docs/", "docker/", "phase1_research_copilot/", "services/ai_copilot/")) for path in changed_files):
        return "yellow"
    return "green"


def _recommendations(changed_files: list[str], risk_tier: str) -> list[str]:
    recs: list[str] = []
    if risk_tier == "red":
        recs.append("Run targeted verification for every changed live, risk, or admin surface before review.")
        recs.append("Require human approval before merging because protected paths were touched.")
    elif risk_tier == "yellow":
        recs.append("Add narrow tests or compile/runtime checks for the touched UI or copilot surfaces.")
    else:
        recs.append("Keep the scope narrow and verify behavior with the smallest targeted test slice.")

    if any(path.startswith("services/ai_copilot/") for path in changed_files):
        recs.append("Verify provider defaults, forbidden actions, and report output paths stay coherent.")
    if any(path.startswith("dashboard/") for path in changed_files):
        recs.append("Keep dashboard changes visibly labeled if any surface is fallback, synthetic, or sample-backed.")
    if any(path.startswith("docs/") for path in changed_files):
        recs.append("Update the matching operator or safety docs for any workflow or authority change.")
    return recs


def build_review_packet(
    *,
    changed_files: list[str] | tuple[str, ...] | None,
    verification: list[str] | tuple[str, ...] | None = None,
    extra_notes: str = "",
) -> dict[str, Any]:
    files = _normalize_paths(changed_files)
    checks = [str(item).strip() for item in (verification or []) if str(item).strip()]
    risk_tier = _risk_tier(files)
    protected = [path for path in files if is_protected_path(path)]
    approval_required = any(requires_human_approval(path) for path in files)

    summary = (
        "Protected paths touched; review as production-affecting work."
        if risk_tier == "red"
        else "Non-core surfaces touched; review for workflow, UI, and docs coherence."
        if risk_tier == "yellow"
        else "Low-risk repo slice with no protected paths touched."
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "risk_tier": risk_tier,
        "approval_required": approval_required,
        "changed_files": files,
        "protected_files": protected,
        "protected_prefixes": list(PROTECTED_PATH_PREFIXES),
        "verification": checks,
        "summary": summary,
        "recommendations": _recommendations(files, risk_tier),
        "extra_notes": str(extra_notes or "").strip() or None,
    }


def maybe_generate_llm_summary(packet: dict[str, Any]) -> dict[str, Any] | None:
    response = call_llm(
        system=_LLM_SYSTEM_PROMPT,
        user=json.dumps(packet, indent=2, sort_keys=True),
    )
    if not response.get("ok"):
        return None
    return {
        "provider": response.get("provider"),
        "model": response.get("model"),
        "text": str(response.get("text") or "").strip(),
    }


def render_review_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# CryptKeep Repo Review",
        "",
        f"- Generated: {packet.get('generated_at')}",
        f"- Risk tier: {packet.get('risk_tier')}",
        f"- Approval required: {bool(packet.get('approval_required'))}",
        "",
        "## Summary",
        str(packet.get("summary") or ""),
        "",
        "## Changed Files",
    ]
    changed_files = list(packet.get("changed_files") or [])
    if changed_files:
        lines.extend(f"- `{path}`" for path in changed_files)
    else:
        lines.append("- `(none)`")

    lines.extend(["", "## Recommendations"])
    recommendations = list(packet.get("recommendations") or [])
    if recommendations:
        lines.extend(f"- {item}" for item in recommendations)
    else:
        lines.append("- `(none)`")

    verification = list(packet.get("verification") or [])
    lines.extend(["", "## Verification"])
    if verification:
        lines.extend(f"- `{item}`" for item in verification)
    else:
        lines.append("- `(not supplied)`")

    llm_summary = packet.get("llm_summary")
    if isinstance(llm_summary, dict) and str(llm_summary.get("text") or "").strip():
        lines.extend(
            [
                "",
                "## Copilot Summary",
                str(llm_summary.get("text") or "").strip(),
                "",
                f"_Provider: {llm_summary.get('provider')} · Model: {llm_summary.get('model')}_",
            ]
        )

    return "\n".join(lines) + "\n"


def write_review_report(packet: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_stem = str(stem or f"repo_review_{ts}").strip().replace(" ", "_")
    json_path = root / f"{safe_stem}.json"
    md_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_review_markdown(packet), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(md_path)}
