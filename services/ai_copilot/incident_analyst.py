from __future__ import annotations

import logging
import os
from typing import Any, Dict

from services.ai_copilot.context_collector import collect_incident_context
from services.ai_copilot.policy import COPILOT_MODEL, MAX_TOKENS

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
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CBP_ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "ANTHROPIC_API_KEY not set. Add it to .env as CBP_ANTHROPIC_API_KEY.",
            "analysis": None,
        }

    context = collect_incident_context(extra_notes=extra_notes)
    user_message = f"Operator question: {question}\n\n{context}" if question else context

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=COPILOT_MODEL,
            max_tokens=MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        analysis = message.content[0].text if message.content else "(no response)"
        return {
            "ok": True,
            "analysis": analysis,
            "error": None,
            "model": COPILOT_MODEL,
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
