from __future__ import annotations

import logging
from typing import Any, Dict

from services.ai_copilot.context_collector import collect_incident_context
from services.ai_copilot.providers import call_llm

_LOG = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the CryptKeep AI Copilot — a read-only analyst for a live crypto trading system.

Your role: analyze system state, identify issues, suggest next steps for the operator.

Hard constraints:
- Never suggest arming live trading, disarming the kill switch, or submitting orders
- Never suggest modifying the database directly
- All suggestions must be for a human operator to execute

Format:
1. **Status Summary** — current system state in one paragraph
2. **Issues Found** — bullet list of specific problems
3. **Likely Cause** — your best assessment
4. **Recommended Actions** — numbered steps for the operator

Be direct. Reference exact field names and values. If the system looks healthy, say so."""


def analyze_incident(question: str = "", extra_notes: str = "") -> Dict[str, Any]:
    context = collect_incident_context(extra_notes=extra_notes)
    user_message = f"Operator question: {question}\n\n{context}" if question else context

    try:
        response = call_llm(
            system=_SYSTEM_PROMPT,
            user=user_message,
        )
        if not response.get("ok"):
            return {
                "ok": False,
                "error": str(response.get("error") or "unknown copilot error"),
                "analysis": None,
                "provider": response.get("provider"),
                "model": response.get("model"),
                "context_chars": len(context),
            }
        analysis = str(response.get("text") or "").strip() or "(no response)"
        return {
            "ok": True,
            "analysis": analysis,
            "error": None,
            "provider": response.get("provider"),
            "model": response.get("model"),
            "context_chars": len(context),
        }
    except Exception as exc:
        _LOG.exception("ai_copilot.incident_analyst failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "analysis": None}


def quick_health_check() -> Dict[str, Any]:
    return analyze_incident(question="Give me a brief health check. Is anything wrong or worth monitoring?")
