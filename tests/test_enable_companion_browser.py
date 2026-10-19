from pathlib import Path


def test_credential_artifacts_excluded_from_build():
    root = Path(__file__).parents[1]
    assert ".browser*" in (root / "phase1_research_copilot/.dockerignore").read_text().splitlines()


def test_deployment_and_rollback_preserve_gateway_boundary():
    source = (Path(__file__).parents[1] / "scripts/research/enable_companion_browser.py").read_text()
    assert 'configuration(gateway["Image"], dict(old, BROWSER_CHAT_TOKEN=' in source
    assert 'v.replace("$", "$$")' in source
    assert 'service.pop("env_file", None)' in source
    assert 'deployed_env != dict(old, BROWSER_CHAT_TOKEN=token)' in source
    assert '"up", "-d", "--no-deps", "gateway"' in source
    assert 'data.get("chat_status", {}).get("upstream_fallback")' in source
    assert 'page_response.raise_for_status()' in source
    assert 'os.O_EXCL, 0o600' in source
