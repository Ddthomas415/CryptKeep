from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_COPILOT_DIR = ROOT / "services" / "ai_copilot"
PROVIDER_BOUNDARY = AI_COPILOT_DIR / "providers.py"

EXTERNAL_SDK_IMPORT_RE = re.compile(
    r"^\s*(?:"
    r"import\s+anthropic\b|"
    r"from\s+anthropic\b|"
    r"import\s+openai\b|"
    r"from\s+openai\b|"
    r"from\s+google\s+import\s+genai\b|"
    r"from\s+google\.genai\b"
    r")",
    re.MULTILINE,
)

EXTERNAL_PROVIDER_CALL_TOKENS = (
    "Anthropic(",
    "OpenAI(",
    "genai.Client(",
    ".messages.create(",
    ".responses.create(",
    ".models.generate_content(",
)

PROVIDER_SECRET_ENV_TOKENS = (
    "CBP_ANTHROPIC_API_KEY",
    "ANTHROPIC_API_KEY",
    "CBP_OPENAI_API_KEY",
    "OPENAI_API_KEY",
    "CBP_GOOGLE_API_KEY",
    "GOOGLE_API_KEY",
)


def _ai_copilot_python_files() -> list[Path]:
    return sorted(AI_COPILOT_DIR.glob("*.py"))


def test_external_provider_sdk_boundary_is_centralized():
    offenders: list[str] = []
    for path in _ai_copilot_python_files():
        if path == PROVIDER_BOUNDARY:
            continue
        text = path.read_text(encoding="utf-8")
        if EXTERNAL_SDK_IMPORT_RE.search(text):
            offenders.append(f"{path.relative_to(ROOT)} imports an external provider SDK")
        for token in EXTERNAL_PROVIDER_CALL_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} calls external provider token {token}")

    assert offenders == []


def test_external_provider_api_key_reads_stay_in_provider_boundary():
    offenders: list[str] = []
    for path in _ai_copilot_python_files():
        if path == PROVIDER_BOUNDARY:
            continue
        text = path.read_text(encoding="utf-8")
        for token in PROVIDER_SECRET_ENV_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} reads provider secret env {token}")

    assert offenders == []


def test_active_copilot_provider_callers_use_call_llm_boundary():
    call_sites: list[str] = []
    for path in _ai_copilot_python_files():
        if path == PROVIDER_BOUNDARY:
            continue
        text = path.read_text(encoding="utf-8")
        if "call_llm(" in text:
            rel = str(path.relative_to(ROOT))
            assert "from services.ai_copilot.providers import call_llm" in text, rel
            call_sites.append(rel)

    assert sorted(call_sites) == [
        "services/ai_copilot/incident_analyst.py",
        "services/ai_copilot/operator_oversight.py",
        "services/ai_copilot/pr_reviewer.py",
    ]
