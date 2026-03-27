from pathlib import Path


def test_root_pre_commit_config_documents_nested_hook_source() -> None:
    text = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    install = Path("docs/INSTALL.md").read_text(encoding="utf-8")

    assert "repos: []" in text
    assert "crypto-trading-ai/.githooks/pre-commit" in text
    assert "crypto-trading-ai/scripts/install_git_hooks.sh" in text
    assert "scripts/validate.py --quick" in text
    assert "bash crypto-trading-ai/scripts/install_git_hooks.sh" in readme
    assert "bash crypto-trading-ai/scripts/install_git_hooks.sh" in install
