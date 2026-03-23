from __future__ import annotations

import html as html_lib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Response, Header, HTTPException
from pydantic import BaseModel

from shared.answer_metadata import fallback_answer_metadata, normalize_answer_metadata
from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.llm_client import OpenAIResponsesClient
from shared.logging import configure_logging
from shared.prompting import CHAT_COPILOT_INSTRUCTIONS
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "gateway", settings.log_level)
llm_client = OpenAIResponsesClient(settings)

app = FastAPI(title="gateway", version="0.2.0")


def _require_service_token(authorization: str | None) -> None:
    expected = str(getattr(settings, "service_token", "") or "")
    if not expected:
        raise HTTPException(status_code=503, detail="service_auth_not_configured")
    supplied = str(authorization or "").strip()
    prefix = "Bearer "
    if not supplied.startswith(prefix):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = supplied[len(prefix):].strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="unauthorized")



class ChatRequest(BaseModel):
    asset: str
    question: str
    lookback_minutes: int = 60


def _format_reasoning_provider(value: Any) -> str:
    provider = str(value or "").strip().lower()
    if not provider:
        return "Unknown"
    if provider == "openai":
        return "OpenAI"
    if provider == "backend_api":
        return "Backend API"
    if provider == "phase1_copilot":
        return "Phase 1 Copilot"
    if provider == "gateway_fallback":
        return "Gateway Fallback"
    if provider == "fallback":
        return "Fallback"
    return provider.replace("_", " ").title()


def _format_status_summary(label: str, status: dict[str, Any] | None) -> str:
    payload = status if isinstance(status, dict) else {}
    provider = _format_reasoning_provider(payload.get("provider"))
    model = str(payload.get("model") or "").strip()
    parts = [provider]
    if model:
        parts.append(model)
    if bool(payload.get("fallback")):
        parts.append("fallback")
    if bool(payload.get("upstream_fallback")):
        upstream_reason = str(payload.get("upstream_reason") or "").strip()
        parts.append(f"upstream {upstream_reason}" if upstream_reason else "upstream fallback")
    return f"{label}: {' | '.join(parts)}"


def _build_reasoning_summary(
    explain_status: dict[str, Any] | None,
    chat_status: dict[str, Any] | None,
) -> str:
    return "\n".join(
        [
            _format_status_summary("Explain", explain_status),
            _format_status_summary("Chat", chat_status),
        ]
    )


def _structural_badge_class(severity: str) -> str:
    value = str(severity or "ok").strip().lower()
    if value in {"critical", "danger", "error"}:
        return "badge-danger"
    if value in {"warn", "warning"}:
        return "badge-accent"
    return "badge-success"


def _load_structural_edge_shell_state() -> dict[str, Any]:
    try:
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from dashboard.services.crypto_edge_research import load_crypto_edge_staleness_digest

        payload = load_crypto_edge_staleness_digest()
        if isinstance(payload, dict) and payload:
            severity = str(payload.get("severity") or "ok")
            headline = str(payload.get("headline") or "Structural-edge data status")
            summary = str(payload.get("while_away_summary") or payload.get("summary_text") or "").strip()
            return {
                "severity": severity,
                "headline": headline,
                "summary": summary or "Structural-edge freshness summary is available in the dashboard research workspace.",
                "badge_label": "Needs Attention" if bool(payload.get("needs_attention")) else "Current",
            }
    except Exception as exc:
        logger.warning(
            "gateway_structural_shell_state_failed",
            extra={"context": {"error_type": type(exc).__name__}},
        )
    return {
        "severity": "warn",
        "headline": "Structural-edge digest unavailable",
        "summary": "Structural-edge freshness could not be loaded for the copilot shell. Check the dashboard research workspace if you need current provenance and freshness details.",
        "badge_label": "Unavailable",
    }


def _fallback_explain_response(req: ChatRequest, *, reason: str) -> dict[str, Any]:
    asset = str(req.asset or "").upper().strip() or "ASSET"
    current_cause = (
        f"Live explain reasoning is temporarily unavailable for {asset}. "
        "The gateway is returning a research-only fallback summary."
    )
    past_precedent = (
        f"No trusted historical precedent for {asset} is available because the explain service could not be reached."
    )
    future_catalyst = (
        f"No fresh forward catalyst for {asset} can be confirmed until the explain service is reachable again."
    )
    return {
        "ok": True,
        "asset": asset,
        "question": req.question,
        "current_cause": current_cause,
        "past_precedent": past_precedent,
        "relevant_past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "confidence": 0.25,
        "confidence_score": 0.25,
        "risk_note": "Research only. Execution disabled.",
        "execution_disabled": True,
        "evidence": [],
        "evidence_bundle": {"market_snapshot": {}, "recent_news": [], "past_context": [], "future_context": []},
        "answer_metadata": fallback_answer_metadata(reason=f"Explain service unavailable ({reason})."),
        "risk_posture": {
            "execution_mode": "DISABLED",
            "gate": "NO_TRADING",
            "allow_trading": False,
            "reason": "Gateway fallback mode",
        },
        "execution": {"enabled": False, "reason": "Phase 1 research copilot only"},
        "assistant_status": {
            "provider": "gateway_fallback",
            "model": None,
            "fallback": True,
            "message": f"Explain service unavailable; gateway fallback used ({reason}).",
        },
    }


def _fallback_chat_response(payload: dict[str, Any]) -> str:
    asset = str(payload.get("asset") or "asset")
    current = str(payload.get("current_cause") or "No current cause available.")
    future = str(payload.get("future_catalyst") or "No catalyst available.")
    risk_note = str(payload.get("risk_note") or "Research only. Execution disabled.")
    return f"{asset}: {current}\n\nNext catalyst: {future}\n\nRisk note: {risk_note}"


async def _generate_chat_response(explain_payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not llm_client.enabled:
        return _fallback_chat_response(explain_payload), {
            "provider": "fallback",
            "model": None,
            "fallback": True,
            "message": "OpenAI chat phrasing unavailable; deterministic formatter used.",
        }

    try:
        response = await llm_client.create_response(
            model=settings.openai_model,
            instructions=CHAT_COPILOT_INSTRUCTIONS,
            input=json.dumps(
                {
                    "asset": explain_payload.get("asset"),
                    "question": explain_payload.get("question"),
                    "current_cause": explain_payload.get("current_cause"),
                    "past_precedent": explain_payload.get("past_precedent")
                    or explain_payload.get("relevant_past_precedent"),
                    "future_catalyst": explain_payload.get("future_catalyst"),
                    "confidence": explain_payload.get("confidence")
                    or explain_payload.get("confidence_score"),
                    "risk_note": explain_payload.get("risk_note"),
                    "execution_disabled": explain_payload.get("execution_disabled", True),
                },
                ensure_ascii=True,
            ),
            metadata={
                "mode": "chat_copilot",
                "asset": str(explain_payload.get("asset") or ""),
            },
        )
        text = OpenAIResponsesClient.output_text(response).strip()
        if text:
            return text, {
                "provider": "openai",
                "model": settings.openai_model,
                "fallback": False,
            }
        raise RuntimeError("empty_chat_output")
    except Exception as exc:
        logger.warning(
            "chat_generation_fallback",
            extra={"context": {"asset": explain_payload.get("asset"), "error_type": type(exc).__name__}},
        )
        return _fallback_chat_response(explain_payload), {
            "provider": "fallback",
            "model": None,
            "fallback": True,
            "message": f"OpenAI chat phrasing unavailable; deterministic formatter used ({type(exc).__name__}).",
        }


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "gateway", "ok": True, "ui": True, "openai_enabled": llm_client.enabled}


@app.get("/", response_class=Response)
async def chat_ui() -> Response:
    dashboard_url = os.getenv("CK_DASHBOARD_URL", "http://localhost:8502").strip().rstrip("/")
    structural_state = _load_structural_edge_shell_state()
    html = """
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>CryptKeep Copilot</title>
  <style>
    :root {
      --bg: #050914;
      --bg-soft: rgba(8, 13, 25, 0.94);
      --surface: linear-gradient(180deg, rgba(13, 20, 34, 0.98) 0%, rgba(9, 15, 28, 0.96) 100%);
      --surface-soft: rgba(11, 18, 32, 0.9);
      --border: rgba(92, 118, 167, 0.18);
      --border-strong: rgba(87, 165, 255, 0.24);
      --text: #f4f7fb;
      --muted: #98a8c7;
      --accent: #57a5ff;
      --accent-soft: rgba(87, 165, 255, 0.14);
      --danger: #ff6b7b;
      --danger-soft: rgba(255, 107, 123, 0.14);
      --success: #37d67a;
      --success-soft: rgba(55, 214, 122, 0.12);
      --shadow: 0 20px 45px rgba(0, 0, 0, 0.35);
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(46, 91, 255, 0.18), transparent 30%),
        radial-gradient(circle at top right, rgba(9, 94, 61, 0.14), transparent 26%),
        var(--bg);
      color: var(--text);
    }
    .wrap { max-width: 1220px; margin: 0 auto; padding: 28px 22px 40px; }
    .shell {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: 22px;
      align-items: start;
    }
    .sidebar,
    .panel,
    .card {
      border: 1px solid var(--border);
      border-radius: 22px;
      background: var(--surface);
      box-shadow: var(--shadow);
    }
    .sidebar { padding: 20px 18px; position: sticky; top: 20px; }
    .brand { display: grid; gap: 10px; margin-bottom: 20px; }
    .brand-mark {
      width: 44px;
      height: 44px;
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(87, 165, 255, 0.28), rgba(87, 165, 255, 0.1));
      border: 1px solid var(--border-strong);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      letter-spacing: 0.08em;
    }
    .brand-title { font-size: 1.28rem; font-weight: 700; letter-spacing: -0.03em; }
    .brand-copy { color: var(--muted); font-size: 0.92rem; line-height: 1.55; }
    .badge-row,
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.55rem; }
    .badge,
    .chip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(11, 18, 32, 0.74);
      color: var(--muted);
      padding: 0.42rem 0.78rem;
      font-size: 0.8rem;
      line-height: 1;
      white-space: nowrap;
    }
    .badge-accent,
    .chip:hover {
      background: var(--accent-soft);
      border-color: var(--border-strong);
      color: #dceaff;
    }
    .badge-success {
      background: var(--success-soft);
      border-color: rgba(55, 214, 122, 0.24);
      color: #caf9df;
    }
    .badge-danger {
      background: var(--danger-soft);
      border-color: rgba(255, 107, 123, 0.24);
      color: #ffd5db;
    }
    .chip {
      background: transparent;
      cursor: pointer;
      transition: border-color 120ms ease, transform 120ms ease, background 120ms ease;
    }
    .chip:hover { transform: translateY(-1px); }
    .nav-label {
      margin: 20px 0 8px;
      font-size: 0.74rem;
      letter-spacing: 0.12em;
      color: var(--muted);
      text-transform: uppercase;
    }
    .nav-list { display: grid; gap: 6px; }
    .nav-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-radius: 14px;
      padding: 0.75rem 0.9rem;
      color: var(--muted);
      background: transparent;
      border: 1px solid transparent;
    }
    .nav-item-link {
      text-decoration: none;
      transition: transform 120ms ease, border-color 120ms ease, background 120ms ease, color 120ms ease;
    }
    .nav-item-link:hover {
      transform: translateY(-1px);
      background: rgba(87, 165, 255, 0.08);
      border-color: rgba(87, 165, 255, 0.14);
      color: var(--text);
    }
    .nav-item.active {
      background: rgba(87, 165, 255, 0.12);
      border-color: rgba(87, 165, 255, 0.2);
      color: var(--text);
    }
    .sidebar-note {
      margin-top: 18px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: var(--surface-soft);
      padding: 14px 15px;
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.55;
    }
    .main { display: grid; gap: 18px; }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.8fr);
      gap: 18px;
      padding: 24px;
    }
    .hero-eyebrow {
      font-size: 0.76rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
    }
    .hero-title {
      margin-top: 12px;
      font-size: 2.7rem;
      line-height: 0.98;
      letter-spacing: -0.06em;
      font-weight: 760;
      max-width: 12ch;
    }
    .hero-copy {
      margin: 14px 0 0;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.7;
      max-width: 42rem;
    }
    .hero-metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }
    .metric {
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(11, 18, 32, 0.76);
      padding: 14px 15px;
      min-height: 102px;
    }
    .metric-label { font-size: 0.74rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
    .metric-value { margin-top: 10px; font-size: 1.5rem; font-weight: 700; letter-spacing: -0.03em; }
    .metric-delta { margin-top: 9px; color: var(--muted); font-size: 0.88rem; }
    .note-card {
      border: 1px solid rgba(87, 165, 255, 0.16);
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(10, 17, 30, 0.98), rgba(7, 12, 22, 0.94));
      padding: 18px;
      height: 100%;
    }
    .note-title {
      font-size: 0.76rem;
      letter-spacing: 0.12em;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
      margin-bottom: 12px;
    }
    .note-list { margin: 0; padding-left: 1rem; display: grid; gap: 0.7rem; color: var(--muted); }
    .content-grid {
      display: grid;
      grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
      gap: 18px;
    }
    .panel { padding: 20px; }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 1rem;
      margin-bottom: 14px;
    }
    .section-title { font-size: 1.12rem; font-weight: 700; letter-spacing: -0.03em; }
    .section-copy { margin-top: 4px; color: var(--muted); font-size: 0.9rem; line-height: 1.55; }
    .meta { color: var(--muted); font-size: 0.82rem; }
    .form-grid { display: grid; gap: 12px; }
    .row { display: grid; grid-template-columns: 168px minmax(0, 1fr); gap: 12px; align-items: start; margin-bottom: 12px; }
    label { color: var(--muted); font-size: 0.9rem; padding-top: 10px; }
    input, textarea, button {
      width: 100%;
      box-sizing: border-box;
      border-radius: 14px;
      border: 1px solid var(--border);
      padding: 12px 13px;
      background: rgba(11, 18, 32, 0.9);
      color: var(--text);
      font-size: 0.95rem;
    }
    textarea { min-height: 96px; resize: vertical; }
    button.primary {
      background: linear-gradient(180deg, rgba(255, 107, 123, 0.92), rgba(244, 86, 102, 0.88));
      border-color: rgba(255, 107, 123, 0.3);
      font-weight: 650;
      cursor: pointer;
      margin-top: 12px;
    }
    .hint {
      margin-top: 10px;
      padding: 13px 14px;
      border-radius: 16px;
      border: 1px solid rgba(87, 165, 255, 0.14);
      background: rgba(87, 165, 255, 0.08);
      color: #d9e9ff;
      font-size: 0.9rem;
      line-height: 1.55;
    }
    .provenance-strip {
      display: grid;
      gap: 10px;
      margin-bottom: 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid rgba(87, 165, 255, 0.16);
      background: rgba(11, 18, 32, 0.78);
    }
    .provenance-copy {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.55;
    }
    .answer-card,
    .raw-card {
      padding: 20px;
    }
    .answer {
      white-space: pre-wrap;
      color: var(--text);
      line-height: 1.7;
      font-size: 0.96rem;
    }
    details {
      border-top: 1px solid var(--border);
      margin-top: 14px;
      padding-top: 14px;
    }
    summary { cursor: pointer; color: var(--muted); }
    pre {
      white-space: pre-wrap;
      background: rgba(7, 12, 22, 0.92);
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 16px;
      color: #d6e2f6;
      overflow-x: auto;
    }
    @media (max-width: 1024px) {
      .shell,
      .hero,
      .content-grid,
      .hero-metrics {
        grid-template-columns: 1fr;
      }
      .sidebar { position: static; }
      .row { grid-template-columns: 1fr; }
      label { padding-top: 0; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"shell\">
      <aside class=\"sidebar\">
        <div class=\"brand\">
          <div class=\"brand-mark\">CK</div>
          <div class=\"brand-title\">CryptKeep Copilot</div>
          <div class=\"brand-copy\">Research-only assistant for signal review, market context, and operator summaries.</div>
        </div>
        <div class=\"badge-row\">
          <span class=\"badge badge-accent\">Phase 1</span>
          <span class=\"badge badge-success\">Execution Disabled</span>
          <span class=\"badge badge-danger\">Research Only</span>
        </div>
        <div class=\"nav-label\">Copilot workflow</div>
        <div class=\"nav-list\">
          <div class=\"nav-item active\"><span>Ask about an asset</span><span>Live</span></div>
          <div class=\"nav-item\"><span>Explain a signal</span><span>Queue</span></div>
          <div class=\"nav-item\"><span>Summarize while away</span><span>Digest</span></div>
        </div>
        <div class=\"nav-label\">Dashboard workflow</div>
        <div class=\"nav-list\">
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/\" target=\"_blank\" rel=\"noreferrer\"><span>Overview</span><span>Open</span></a>
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/Markets\" target=\"_blank\" rel=\"noreferrer\"><span>Markets</span><span>Asset desk</span></a>
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/Signals\" target=\"_blank\" rel=\"noreferrer\"><span>Signals</span><span>AI queue</span></a>
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/Research\" target=\"_blank\" rel=\"noreferrer\"><span>Research</span><span>Edge lab</span></a>
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/Operations\" target=\"_blank\" rel=\"noreferrer\"><span>Operations</span><span>Operator</span></a>
          <a class=\"nav-item nav-item-link\" href=\"__DASHBOARD_URL__/Settings\" target=\"_blank\" rel=\"noreferrer\"><span>Settings</span><span>Config</span></a>
        </div>
        <div class=\"nav-label\">Quick prompts</div>
        <div class=\"chip-row\">
          <button class=\"chip\" type=\"button\" onclick=\"preset('BTC', 'Why is BTC moving right now?')\">Why is BTC moving?</button>
          <button class=\"chip\" type=\"button\" onclick=\"preset('ETH', 'Explain the current ETH signal and risks.')\">Explain ETH signal</button>
          <button class=\"chip\" type=\"button\" onclick=\"preset('SOL', 'What changed while I was away on SOL?')\">What changed?</button>
          <button class=\"chip\" type=\"button\" onclick=\"preset('BTC', 'Summarize the latest live structural edge snapshot.')\">Latest live edge snapshot</button>
        </div>
        <div class=\"sidebar-note\">Keep the same reasoning model across dashboard detail cards and this page so the assistant feels native to the product rather than like a sidecar tool.</div>
      </aside>
      <main class=\"main\">
        <section class=\"card hero\">
          <div>
            <div class=\"hero-eyebrow\">Embedded Copilot</div>
            <div class=\"hero-title\">Research and explain from the same platform context.</div>
            <p class=\"hero-copy\">Ask about an asset, a signal, or what changed while away. The assistant stays inside the same research-only safety boundary used by the dashboard.</p>
            <div class=\"hero-metrics\">
              <div class=\"metric\">
                <div class=\"metric-label\">Mode</div>
                <div class=\"metric-value\">Research</div>
                <div class=\"metric-delta\">execution disabled</div>
              </div>
              <div class=\"metric\">
                <div class=\"metric-label\">Scope</div>
                <div class=\"metric-value\">Asset + Signal</div>
                <div class=\"metric-delta\">market context ready</div>
              </div>
              <div class=\"metric\">
                <div class=\"metric-label\">Evidence</div>
                <div class=\"metric-value\">Structured</div>
                <div class=\"metric-delta\">assistant metadata included</div>
              </div>
              <div class=\"metric\">
                <div class=\"metric-label\">Output</div>
                <div class=\"metric-value\">Copilot answer</div>
                <div class=\"metric-delta\">raw details available</div>
              </div>
            </div>
          </div>
          <div class=\"note-card\">
            <div class=\"note-title\">Structural edge status</div>
            <div class=\"badge-row\">
              <span class=\"badge __STRUCTURAL_BADGE_CLASS__\">__STRUCTURAL_BADGE_LABEL__</span>
            </div>
            <p class=\"hero-copy\" style=\"margin-top:12px; max-width:none;\">
              <strong>__STRUCTURAL_HEADLINE__</strong><br/>
              __STRUCTURAL_SUMMARY__
            </p>
            <div class=\"note-title\" style=\"margin-top:18px;\">Suggested asks</div>
            <ul class=\"note-list\">
              <li>Ask why an asset is moving and what catalyst matters next.</li>
              <li>Ask what changed while away using the same explain path as the dashboard.</li>
              <li>Ask for the latest live structural edge snapshot to separate collected venue data from sample bundles.</li>
              <li>Keep the assistant focused on research, evidence, and risk framing.</li>
            </ul>
          </div>
        </section>
        <div class=\"content-grid\">
          <section class=\"panel\">
            <div class=\"section-head\">
              <div>
                <div class=\"section-title\">Copilot Request</div>
                <div class=\"section-copy\">Use the same asset + question flow as the dashboard explain path, but present it with a cleaner native shell.</div>
              </div>
              <div class=\"meta\">research only</div>
            </div>
            <div class=\"form-grid\">
              <div class=\"row\"><label for=\"asset\">Asset</label><input id=\"asset\" value=\"SOL\"/></div>
              <div class=\"row\"><label for=\"question\">Question</label><textarea id=\"question\">Why is SOL moving?</textarea></div>
              <div class=\"row\"><label for=\"lookback\">Lookback (min)</label><input id=\"lookback\" value=\"60\"/></div>
            </div>
            <button class=\"primary\" onclick=\"ask()\">Ask Copilot</button>
            <div class=\"hint\" id=\"reasoning\">Execution remains disabled. The assistant can explain and summarize, but it will not route orders.</div>
          </section>
          <section class=\"panel answer-card\">
            <div class=\"section-head\">
              <div>
                <div class=\"section-title\">Assistant Response</div>
                <div class=\"section-copy\">Reasoning summary first, then the formatted answer, then raw detail when needed.</div>
              </div>
              <div class=\"meta\">live output</div>
            </div>
            <div class=\"provenance-strip\" id=\"answer-metadata\">
              <div class=\"badge-row\">
                <span class=\"badge\">Answer Trust</span>
                <span class=\"badge\">Missing</span>
              </div>
              <div class=\"provenance-copy\">Source basis, freshness, confidence, and caveats will appear here after each query.</div>
            </div>
            <div class=\"answer\" id=\"answer\">Waiting for query...</div>
            <details>
              <summary>Show raw response</summary>
              <pre id=\"out\">Waiting for query...</pre>
            </details>
          </section>
        </div>
      </main>
    </div>
  </div>
<script>
function preset(asset, question) {
  document.getElementById('asset').value = asset;
  document.getElementById('question').value = question;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('\"', '&quot;')
    .replaceAll(\"'\", '&#39;');
}

function trustBadgeClass(state) {
  const value = String(state || '').toLowerCase();
  if (value === 'stale' || value === 'critical' || value === 'low') return 'badge-danger';
  if (value === 'aging' || value === 'warn' || value === 'partial' || value === 'medium') return 'badge-accent';
  if (value === 'fresh' || value === 'ok' || value === 'enabled' || value === 'high') return 'badge-success';
  return '';
}

function renderAnswerMetadata(metadata) {
  const container = document.getElementById('answer-metadata');
  const payload = metadata && typeof metadata === 'object' ? metadata : {};
  const sourceName = payload.source_name || 'Unknown';
  const sourceFamily = payload.source_family || 'unknown';
  const freshnessStatus = payload.freshness_status || 'missing';
  const confidenceLabel = payload.confidence_label || 'Unknown';
  const provenanceLabel = payload.partial_provenance ? 'Partial' : 'Complete';
  const timestamp = payload.data_timestamp || payload.as_of || '-';
  const caveat = payload.caveat || 'Research only. Execution disabled.';
  const missingReason = payload.missing_provenance_reason || '';
  const badges = [
    ['Basis', sourceName, trustBadgeClass(payload.metadata_status)],
    ['Family', sourceFamily, trustBadgeClass(payload.metadata_status)],
    ['Freshness', freshnessStatus, trustBadgeClass(freshnessStatus)],
    ['Confidence', confidenceLabel, trustBadgeClass(String(confidenceLabel).toLowerCase())],
    ['Provenance', provenanceLabel, trustBadgeClass(payload.partial_provenance ? 'warn' : 'ok')],
    ['As Of', timestamp, ''],
  ];
  const badgeHtml = badges.map(([label, value, badgeClass]) =>
    `<span class=\"badge ${badgeClass}\">${escapeHtml(label)}: ${escapeHtml(value)}</span>`
  ).join('');
  const detail = missingReason ? `<br/>${escapeHtml(missingReason)}` : '';
  container.innerHTML = `
    <div class=\"badge-row\">
      <span class=\"badge badge-accent\">Answer Trust</span>
      ${badgeHtml}
    </div>
    <div class=\"provenance-copy\"><strong>${escapeHtml(sourceName)} metadata</strong><br/>${escapeHtml(caveat)}${detail}</div>
  `;
}

async function ask() {
  const body = {
    asset: document.getElementById('asset').value,
    question: document.getElementById('question').value,
    lookback_minutes: parseInt(document.getElementById('lookback').value || '60', 10),
  };
  const out = document.getElementById('out');
  const answer = document.getElementById('answer');
  const reasoning = document.getElementById('reasoning');
  const provenance = document.getElementById('answer-metadata');
  answer.textContent = 'Loading...';
  out.textContent = 'Loading...';
  provenance.querySelector('.provenance-copy').textContent = 'Loading answer metadata...';
  const res = await fetch('/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.assistant_response) {
    const summary = data.reasoning_summary ? data.reasoning_summary + '\\n\\n' : '';
    const fallback = data.assistant_status && data.assistant_status.message ? ' ' + data.assistant_status.message : '';
    reasoning.textContent = summary.trim() || 'Execution remains disabled. Research-only response.';
    answer.textContent = data.assistant_response;
    renderAnswerMetadata(data.answer_metadata);
    out.textContent = JSON.stringify(data, null, 2);
    if (fallback.trim()) {
      reasoning.textContent = reasoning.textContent + fallback;
    }
    return;
  }
  reasoning.textContent = 'Copilot returned raw data only.';
  answer.textContent = 'No assistant response returned.';
  renderAnswerMetadata(data.answer_metadata);
  out.textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>
"""
    html = html.replace("__DASHBOARD_URL__", dashboard_url)
    html = html.replace("__STRUCTURAL_BADGE_CLASS__", _structural_badge_class(structural_state.get("severity") or "ok"))
    html = html.replace("__STRUCTURAL_BADGE_LABEL__", html_lib.escape(str(structural_state.get("badge_label") or "Current")))
    html = html.replace("__STRUCTURAL_HEADLINE__", html_lib.escape(str(structural_state.get("headline") or "Structural-edge data status")))
    html = html.replace("__STRUCTURAL_SUMMARY__", html_lib.escape(str(structural_state.get("summary") or "")))
    return Response(content=html, media_type="text/html")


@app.post("/v1/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    _require_service_token(authorization)
    endpoint = f"{settings.orchestrator_url.rstrip('/')}/v1/explain"

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(
                endpoint,
                json={
                    "asset": req.asset,
                    "question": req.question,
                    "lookback_minutes": req.lookback_minutes,
                },
            )
            res.raise_for_status()
            return res.json()

    explain_fallback_reason: str | None = None
    try:
        response = await retry_async(_call, retries=2, base_delay=0.3)
    except Exception as exc:
        explain_fallback_reason = type(exc).__name__
        response = _fallback_explain_response(req, reason=explain_fallback_reason)
        logger.warning(
            "orchestrator_chat_fallback",
            extra={"context": {"asset": req.asset, "question": req.question, "error_type": type(exc).__name__}},
        )

    assistant_response, assistant_status = await _generate_chat_response(response)
    if explain_fallback_reason:
        assistant_status = {
            **assistant_status,
            "upstream_fallback": True,
            "upstream_reason": explain_fallback_reason,
        }
    response["assistant_response"] = assistant_response
    response["chat_status"] = assistant_status
    response["answer_metadata"] = normalize_answer_metadata(
        response.get("answer_metadata") if isinstance(response, dict) else None
    )
    response["reasoning_summary"] = _build_reasoning_summary(
        response.get("assistant_status") if isinstance(response.get("assistant_status"), dict) else None,
        assistant_status,
    )

    await emit_audit_event(
        "gateway",
        "chat",
        payload={
            "asset": req.asset,
            "question": req.question,
            "lookback_minutes": req.lookback_minutes,
            "chat_provider": assistant_status.get("provider"),
            "chat_model": assistant_status.get("model"),
            "fallback": bool(assistant_status.get("fallback")),
        },
    )
    logger.info(
        "chat_completed",
        extra={
            "context": {
                "asset": req.asset,
                "question": req.question,
                "chat_provider": assistant_status.get("provider"),
            }
        },
    )
    return response
