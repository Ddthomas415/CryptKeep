from __future__ import annotations

import logging
import os
from typing import Any, Dict

from services.ai_copilot.context_collector import collect_incident_context
from services.ai_copilot.providers import call_llm

_LOG = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the CryptKeep AI Copilot — a read-only analyst for a live cryptocurrency trading system.

Your role:
- Analyze system state, logs, and events provided to you
- Identify likely root causes of issues
- Suggest specific next steps for the operator
- Flag risks before they become incidents

Your constraints:
- Never suggest arming live trading, disarming the kill switch, or submitting orders
- Never suggest modifying the database directly
- Never suggest merging or deploying code without human review
- All suggestions must be framed as recommendations for a human operator

Format your response as:
1. **Status Summary**
2. **Issues Found**
3. **Likely Cause**
4. **Recommended Actions**
"""


def analyze_incident(question: str = "", extra_notes: str = "") -> Dict[str, Any]:
    context = collect_incident_context(extra_notes=extra_notes)
    user_message = f"Operator question: {question}\n\n{context}" if question else context

    try:
        result = call_llm(system=_SYSTEM_PROMPT, user=user_message)
        if not result.get("ok"):
            return {
                "ok": False,
                "error": result.get("error"),
                "analysis": None,
            }

        return {
            "ok": True,
            "analysis": result.get("text") or "(no response)",
            "error": None,
            "model": result.get("model"),
            "provider": result.get("provider"),
            "context_chars": len(context),
        }
    except Exception as exc:
        _LOG.exception("ai_copilot.incident_analyst failed")
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "analysis": None,
        }


def quick_health_check() -> Dict[str, Any]:
    return analyze_incident(
        question="Give me a brief health check of the trading system. Is anything wrong or worth monitoring?"
    )
