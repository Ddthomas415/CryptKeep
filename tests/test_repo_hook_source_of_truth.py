from pathlib import Path


def test_root_pre_commit_config_documents_nested_hook_source() -> None:
    text = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "repos: []" in text
    assert "crypto-trading-ai/.githooks/pre-commit" in text
    assert "scripts/validate.py --quick" in text
