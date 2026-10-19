"""Guard corrected instructions, not a claim of agent behavioral compliance."""
from pathlib import Path


def test_auth_guidance_does_not_promise_permanence_or_require_unauthorized_writes():
    text = Path("docs/CODEX_REMEDIATION_PROMPTS.md").read_text()
    assert "Never call authentication permanently resolved" in text
    assert "Do not publish merely to test authentication" in text
    assert "If publishing is authorized" in text
    assert 'Do not call GitHub auth "permanently resolved" unless' not in text
    assert "If push works, create the PR" not in text


def test_continuation_requires_outcome_and_evidence_boundaries():
    text = Path("runtime_prompt.md").read_text()
    assert "latest\n  relevant work-log resolution" in text
    assert "equate a mocked boundary with real integration" in text
    assert "compare the delivered result to the accepted" in text
