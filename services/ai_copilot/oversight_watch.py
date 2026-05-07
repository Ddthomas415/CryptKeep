from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.admin.health import list_health
from services.ai_copilot.policy import MAX_CONTEXT_CHARS, report_root
from services.ai_copilot.providers import call_llm
from services.os.app_paths import code_root
from services.process.bot_runtime_truth import canonical_bot_status, canonical_service_status, read_heartbeat
from services.risk.system_health import get_system_health

_SYSTEM_PROMPT = """You are the CryptKeep Repo Oversight Watch.

Your role:
- monitor runtime truth
- answer repo-wide operator questions using visible code, docs, tests, config, and runtime state
- stay read-only and operationally conservative

Hard constraints:
- never suggest enabling live trading, disarming the kill switch, or submitting/canceling orders
- never claim code behavior without pointing to repo evidence or runtime fields
- when uncertain, say what file or runtime surface should be checked next

Format:
1. Status Summary
2. Repo Answer
3. Evidence
4. Next Checks

Be direct. Reference exact file paths, status fields, and runtime values."""

_WATCH_SCOPE = (
    "services",
    "scripts",
    "docs",
    "tests",
    "dashboard",
    "config",
    "AGENTS.md",
    "REMAINING_TASKS.md",
    "CHECKPOINTS.md",
)

_CORE_DOCS = (
    "AGENTS.md",
    "REMAINING_TASKS.md",
    "docs/checkpoints/launch_blockers_root_runtime.md",
    "docs/LAUNCH_CHECKLIST.md",
    "docs/CURRENT_RUNTIME_TRUTH.md",
)

_SEARCH_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".txt"}

_TOKEN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "what",
    "when",
    "where",
    "which",
    "from",
    "into",
    "about",
    "need",
    "needs",
    "repo",
    "full",
    "fully",
    "connected",
    "copilot",
    "watch",
    "monitor",
    "answer",
    "answers",
    "question",
    "questions",
    "all",
    "aspects",
}


def _root() -> Path:
    return code_root()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(rel_path: str, *, max_chars: int = 2_000) -> str:
    path = _root() / rel_path
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def _excerpt(rel_path: str, *, max_lines: int = 16, max_chars: int = 1_200) -> str:
    text = _read_text(rel_path, max_chars=max_chars)
    if not text:
        return ""
    return "\n".join(text.splitlines()[:max_lines]).strip()


def _git_capture(*args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(_root()),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return str(proc.stdout or "").strip()


def _repo_state() -> dict[str, Any]:
    dirty_lines = [line for line in _git_capture("status", "--short").splitlines() if line.strip()]
    return {
        "root": str(_root()),
        "head": _git_capture("rev-parse", "--short", "HEAD") or "unknown",
        "branch": _git_capture("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "dirty": bool(dirty_lines),
        "dirty_file_count": len(dirty_lines),
        "dirty_files_sample": dirty_lines[:12],
    }


def _runtime_state() -> dict[str, Any]:
    services = canonical_service_status()
    running = sorted(name for name, row in services.items() if bool((row or {}).get("running")))
    stopped = sorted(name for name, row in services.items() if not bool((row or {}).get("running")))
    return {
        "bot_status": canonical_bot_status(),
        "heartbeat": read_heartbeat(),
        "system_health": get_system_health(),
        "operations_snapshot": _operations_snapshot(services),
        "canonical_services": services,
        "running_services": running,
        "stopped_services": stopped,
    }


def _operations_snapshot(services: dict[str, Any]) -> dict[str, Any]:
    latest_by_service: dict[str, dict[str, Any]] = {}
    for row in list_health():
        if not isinstance(row, dict):
            continue
        service = str(row.get("service") or "").strip()
        if not service:
            continue
        current_ts = str(row.get("ts") or "")
        previous = latest_by_service.get(service) or {}
        if current_ts >= str(previous.get("ts") or ""):
            latest_by_service[service] = row

    running_statuses = {"RUNNING", "OK", "HEALTHY", "STARTING"}
    attention_statuses = {"ERROR", "FAILED", "UNHEALTHY", "DEGRADED", "STOPPED"}
    tracked_names = sorted(set(services) | set(latest_by_service))
    healthy = 0
    attention = 0
    unknown = 0
    last_health_ts = ""
    for name in tracked_names:
        row = latest_by_service.get(name)
        if not isinstance(row, dict):
            unknown += 1
            continue
        status = str(row.get("status") or "").strip().upper()
        ts = str(row.get("ts") or "").strip()
        if ts and ts > last_health_ts:
            last_health_ts = ts
        if status in running_statuses:
            healthy += 1
        elif status in attention_statuses:
            attention += 1
        else:
            unknown += 1
    return {
        "services": tracked_names,
        "tracked_services": len(tracked_names),
        "healthy_services": healthy,
        "attention_services": attention,
        "unknown_services": unknown,
        "last_health_ts": last_health_ts,
    }


def _core_doc_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for rel_path in _CORE_DOCS:
        excerpt = _excerpt(rel_path)
        if excerpt:
            entries.append({"path": rel_path, "excerpt": excerpt})
    return entries


def _question_tokens(question: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z0-9_./-]+", str(question or "").lower())
    tokens: list[str] = []
    for token in raw:
        if len(token) < 3:
            continue
        if token in _TOKEN_STOPWORDS:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens[:8]


def _rg_repo_hits(question: str, *, limit: int = 8) -> list[dict[str, Any]]:
    tokens = _question_tokens(question)
    if not tokens:
        return []
    pattern = "|".join(re.escape(token) for token in tokens)
    cmd = [
        "rg",
        "-n",
        "-i",
        "--max-count",
        "2",
        "--glob",
        "!*.sqlite",
        "--glob",
        "!*.jsonl",
        pattern,
        *_WATCH_SCOPE,
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(_root()),
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except Exception:
        return []
    if proc.returncode not in (0, 1):
        return []

    hits: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for raw_line in str(proc.stdout or "").splitlines():
        parts = raw_line.split(":", 2)
        if len(parts) != 3:
            continue
        rel_path, line_no, snippet = parts
        if rel_path in seen_paths:
            continue
        try:
            line_value = int(line_no)
        except Exception:
            line_value = 0
        hits.append(
            {
                "path": rel_path,
                "line": line_value,
                "snippet": snippet.strip()[:220],
            }
        )
        seen_paths.add(rel_path)
        if len(hits) >= int(limit):
            break
    return hits


def _fallback_repo_hits(question: str, *, limit: int = 8) -> list[dict[str, Any]]:
    tokens = _question_tokens(question)
    if not tokens:
        return []
    hits: list[dict[str, Any]] = []
    for rel_path in _CORE_DOCS:
        text = _read_text(rel_path, max_chars=4_000).lower()
        if not text:
            continue
        if any(token in rel_path.lower() or token in text for token in tokens):
            hits.append({"path": rel_path, "line": 1, "snippet": _excerpt(rel_path, max_lines=8, max_chars=400)})
        if len(hits) >= int(limit):
            break
    return hits


def _repo_hits(question: str, *, limit: int = 8) -> list[dict[str, Any]]:
    tokens = _question_tokens(question)
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()

    for hit in _path_repo_hits(tokens, limit=limit):
        hits.append(hit)
        seen.add(str(hit.get("path")))

    for hit in _rg_repo_hits(question, limit=limit):
        path = str(hit.get("path"))
        if path in seen:
            continue
        hits.append(hit)
        seen.add(path)
        if len(hits) >= int(limit):
            return hits

    if hits:
        return hits[: int(limit)]
    return _fallback_repo_hits(question, limit=limit)


def _candidate_paths() -> list[str]:
    out: list[str] = []
    root = _root()
    for scope in _WATCH_SCOPE:
        path = root / scope
        if path.is_file():
            out.append(scope)
            continue
        if not path.exists() or not path.is_dir():
            continue
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in _SEARCH_SUFFIXES:
                continue
            out.append(str(file_path.relative_to(root)))
    return out


def _file_snippet(rel_path: str, tokens: list[str]) -> tuple[int, str]:
    path = _root() / rel_path
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return 1, ""
    lower_tokens = [token.lower() for token in tokens]
    for idx, line in enumerate(lines, start=1):
        lowered = line.lower()
        if any(token in lowered for token in lower_tokens):
            return idx, line.strip()[:220]
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped:
            return idx, stripped[:220]
    return 1, ""


def _path_repo_hits(tokens: list[str], *, limit: int = 8) -> list[dict[str, Any]]:
    if not tokens:
        return []
    scored: list[tuple[int, str]] = []
    for rel_path in _candidate_paths():
        lowered = rel_path.lower()
        score = 0
        for token in tokens:
            if token in lowered:
                score += 5
            stem = Path(rel_path).stem.lower()
            if token == stem:
                score += 5
        if score <= 0:
            continue
        scored.append((score, rel_path))
    scored.sort(key=lambda item: (-item[0], item[1]))

    hits: list[dict[str, Any]] = []
    for _, rel_path in scored[: int(limit)]:
        line_no, snippet = _file_snippet(rel_path, tokens)
        hits.append({"path": rel_path, "line": line_no, "snippet": snippet})
    return hits


def build_oversight_snapshot(*, question: str = "", extra_notes: str = "") -> dict[str, Any]:
    return {
        "generated_at": _now_iso(),
        "question": str(question or "").strip(),
        "extra_notes": str(extra_notes or "").strip(),
        "watch_scope": list(_WATCH_SCOPE),
        "repo": _repo_state(),
        "runtime": _runtime_state(),
        "core_docs": _core_doc_entries(),
        "relevant_files": _repo_hits(question),
    }


def render_oversight_context(snapshot: dict[str, Any]) -> str:
    parts = [
        "=== CryptKeep Repo Oversight Watch ===",
        f"Collected: {snapshot.get('generated_at')}",
        f"Question: {snapshot.get('question') or '(monitoring summary)'}",
        "\n--- Watch Scope ---",
        json.dumps(snapshot.get("watch_scope"), indent=2),
        "\n--- Repo State ---",
        json.dumps(snapshot.get("repo"), indent=2, sort_keys=True),
        "\n--- Runtime State ---",
        json.dumps(snapshot.get("runtime"), indent=2, sort_keys=True),
        "\n--- Core Docs ---",
    ]
    for entry in snapshot.get("core_docs") or []:
        parts.append(f"[{entry.get('path')}]\n{entry.get('excerpt')}")
    parts.append("\n--- Relevant File Hits ---")
    for hit in snapshot.get("relevant_files") or []:
        parts.append(f"{hit.get('path')}:{hit.get('line')} {hit.get('snippet')}")
    if snapshot.get("extra_notes"):
        parts.append(f"\n--- Operator Notes ---\n{snapshot.get('extra_notes')}")
    return "\n".join(parts)[:MAX_CONTEXT_CHARS]


def _fallback_analysis(*, snapshot: dict[str, Any], provider_error: str) -> str:
    runtime = snapshot.get("runtime") if isinstance(snapshot.get("runtime"), dict) else {}
    system_health = runtime.get("system_health") if isinstance(runtime.get("system_health"), dict) else {}
    repo = snapshot.get("repo") if isinstance(snapshot.get("repo"), dict) else {}
    relevant_files = snapshot.get("relevant_files") if isinstance(snapshot.get("relevant_files"), list) else []
    running = runtime.get("running_services") if isinstance(runtime.get("running_services"), list) else []
    stopped = runtime.get("stopped_services") if isinstance(runtime.get("stopped_services"), list) else []

    lines = [
        "Status Summary",
        f"Repo oversight context collected without LLM response. System health is `{system_health.get('state', 'UNKNOWN')}`. Running services: {', '.join(running) or '(none)'}."
        f" Stopped services: {', '.join(stopped) or '(none)'}."
        f" Repo HEAD is `{repo.get('head', 'unknown')}` on branch `{repo.get('branch', 'unknown')}`.",
        "",
        "Repo Answer",
        "The oversight watch is connected to runtime truth, launch blockers, config, docs, tests, and code search. Use the matched files below as the first evidence surfaces for this question.",
        "",
        "Evidence",
    ]
    if relevant_files:
        for hit in relevant_files[:6]:
            lines.append(f"- `{hit.get('path')}:{hit.get('line')}` — {hit.get('snippet')}")
    else:
        lines.append("- No direct file hit was found for the current question; inspect the core docs and runtime sections in the context bundle.")
    lines.extend(
        [
            "",
            "Next Checks",
            f"1. Resolve LLM provider access if narrative answers are required (`{provider_error}`).",
            "2. Inspect the matched files and runtime fields surfaced in this snapshot.",
            "3. Re-run the oversight watch with a narrower question if you need tighter file targeting.",
        ]
    )
    return "\n".join(lines)


def answer_repo_question(*, question: str, extra_notes: str = "") -> dict[str, Any]:
    snapshot = build_oversight_snapshot(question=question, extra_notes=extra_notes)
    context = render_oversight_context(snapshot)
    user_message = f"Operator question: {question}\n\n{context}" if question else context
    response = call_llm(system=_SYSTEM_PROMPT, user=user_message)
    if response.get("ok"):
        analysis = str(response.get("text") or "").strip() or "(no response)"
        return {
            "ok": True,
            "mode": "llm",
            "analysis": analysis,
            "provider": response.get("provider"),
            "model": response.get("model"),
            "warning": None,
            "context_chars": len(context),
            "snapshot": snapshot,
        }
    warning = str(response.get("error") or "unknown copilot error")
    return {
        "ok": True,
        "mode": "heuristic_fallback",
        "analysis": _fallback_analysis(snapshot=snapshot, provider_error=warning),
        "provider": response.get("provider"),
        "model": response.get("model"),
        "warning": warning,
        "context_chars": len(context),
        "snapshot": snapshot,
    }


def quick_repo_watch() -> dict[str, Any]:
    return answer_repo_question(
        question="Give me a repo-wide oversight summary. What is healthy, what is degraded, and what files matter most right now?"
    )


def render_oversight_markdown(payload: dict[str, Any]) -> str:
    snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
    runtime = snapshot.get("runtime") if isinstance(snapshot.get("runtime"), dict) else {}
    repo = snapshot.get("repo") if isinstance(snapshot.get("repo"), dict) else {}
    relevant_files = snapshot.get("relevant_files") if isinstance(snapshot.get("relevant_files"), list) else []
    lines = [
        "# CryptKeep Repo Oversight Watch",
        "",
        f"- Generated: {snapshot.get('generated_at')}",
        f"- Mode: {payload.get('mode')}",
        f"- Question: {snapshot.get('question') or '(monitoring summary)'}",
        f"- Repo HEAD: {repo.get('head')}",
        f"- Branch: {repo.get('branch')}",
        f"- System health: {((runtime.get('system_health') or {}).get('state') if isinstance(runtime.get('system_health'), dict) else 'UNKNOWN')}",
        "",
        "## Analysis",
        "",
        str(payload.get("analysis") or "(no analysis)"),
        "",
        "## Relevant Files",
    ]
    if relevant_files:
        for hit in relevant_files:
            lines.append(f"- `{hit.get('path')}:{hit.get('line')}` — {hit.get('snippet')}")
    else:
        lines.append("- (none)")
    return "\n".join(lines).strip() + "\n"


def write_oversight_report(payload: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    safe_stem = stem or "repo_oversight_watch"
    json_path = root / f"{safe_stem}.json"
    markdown_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_oversight_markdown(payload), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}
