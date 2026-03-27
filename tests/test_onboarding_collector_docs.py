from pathlib import Path


def test_onboarding_docs_use_real_collector_entrypoint() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    handoff = Path("docs/HANDOFF.md").read_text(encoding="utf-8")
    data_plane = Path("docs/DATA_PLANE.md").read_text(encoding="utf-8")
    install = Path("docs/INSTALL.md").read_text(encoding="utf-8")

    for text in (readme, handoff, data_plane):
        assert "run_collector.sh" not in text
        assert "run_collector.ps1" not in text

    assert "./.venv/bin/python -m services.data_collector.main" in readme
    assert ".\\.venv\\Scripts\\python.exe -m services.data_collector.main" in readme
    assert "./.venv/bin/python -m services.data_collector.main" in handoff
    assert ".\\.venv\\Scripts\\python.exe -m services.data_collector.main" in handoff
    assert "./.venv/bin/python -m services.data_collector.main" in data_plane
    assert ".\\.venv\\Scripts\\python.exe -m services.data_collector.main" in data_plane
    assert "root repo Python platform only" in readme
    assert "root repo Python platform only" in install
    assert "crypto-trading-ai/" in install
