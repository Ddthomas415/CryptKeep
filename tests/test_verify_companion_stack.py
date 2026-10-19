import importlib.util
from pathlib import Path
import pytest


def load_module():
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location("stack_proof", root / "scripts/research/verify_companion_stack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_output_is_exclusive_and_restricted(tmp_path):
    module = load_module()
    root = tmp_path / "phase1_research_copilot"
    root.mkdir()
    destination = tmp_path / "docs/research/proof.json"
    with module.reserve_output(root, destination) as file:
        file.write("original")
    with pytest.raises(FileExistsError):
        module.reserve_output(root, destination)
    assert destination.read_text() == "original"
    with pytest.raises(ValueError):
        module.reserve_output(root, tmp_path / "source.py")


def test_docker_is_pinned_to_local_socket():
    command = load_module().local_docker_command("fixture")
    assert command[:2] == ["docker", "--host"]
    assert command[2] == "unix://" + str(Path.home() / ".docker/run/docker.sock")


@pytest.mark.parametrize("valid", [True, False])
def test_dashboard_uses_repo_client_and_checks_proof(tmp_path, monkeypatch, valid):
    import json
    from types import SimpleNamespace
    module = load_module()
    environment = {"CK_PHASE1_SERVICE_TOKEN": "ephemeral-fixture"}
    def execute(command, **kwargs):
        assert command[0] == str(tmp_path / ".venv/bin/python")
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"] == environment
        assert kwargs["timeout"] == 90
        return SimpleNamespace(returncode=0, stdout=json.dumps({"source_cited": valid,
            "execution_disabled": True, "provider": "fallback"}))
    monkeypatch.setattr(module.subprocess, "run", execute)
    if valid:
        assert module.dashboard_request(tmp_path, environment, "fixture")["source_cited"]
    else:
        with pytest.raises(RuntimeError, match="invalid_proof"):
            module.dashboard_request(tmp_path, environment, "fixture")


def test_build_failure_still_cleans_owned_project(tmp_path, monkeypatch):
    from types import SimpleNamespace
    module = load_module()
    root = tmp_path / "phase1_research_copilot"
    root.mkdir()
    monkeypatch.setattr(module, "isolated_config", lambda *args: {})
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=1 if "build" in command else 0, stdout="", stderr="")
    monkeypatch.setattr(module.subprocess, "run", execute)
    output = tmp_path / "docs/research/failure.json"
    assert module.run(root, output) == 1
    assert "down" in calls[-1] and "--volumes" in calls[-1]
    assert calls[0][5] == calls[-1][5]
    assert '"cleanup": "OWNED_STACK_REMOVED"' in output.read_text()


def test_restart_refreshes_dynamic_endpoint():
    source = (Path(__file__).parents[1] / "scripts/research/verify_companion_stack.py").read_text()
    assert source.index('memory = base("memory-retrieval", 8007)', source.index('compose("restart"')) < source.index('for attempt in range(30)')


def test_isolated_configuration_preserves_existing_stack():
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location("stack_proof", root / "scripts/research/verify_companion_stack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = module.isolated_config(root / "phase1_research_copilot", "cbp-proof-fixture", "test-password", "test-token")
    for name, service in config["services"].items():
        assert service["container_name"] == "cbp-proof-fixture-" + name
        assert "env_file" not in service
        assert all(port.startswith("127.0.0.1::") for port in service.get("ports", []))
        if "build" in service:
            env = service["environment"]
            assert env["OPENAI_API_KEY"] == ""
            assert env["NO_TRADING"] == "true"
            assert env["SERVICE_TOKEN"] == "test-token"
            assert env["NEWS_RSS_URLS"] == ""
    assert all(not data or "external" not in data for data in config["volumes"].values())
    assert config["services"]["timescaledb"]["environment"]["POSTGRES_PASSWORD"] == "test-password"


@pytest.mark.parametrize("returncode", [0, 1])
def test_dashboard_failure_emits_and_retains_safe_receipt_before_rejection(tmp_path, monkeypatch, capsys, returncode):
    import json
    from types import SimpleNamespace
    module = load_module()
    secret = "private-fixture-do-not-retain"
    proof = {"source_cited": False, "execution_disabled": True, "provider": "dashboard_fallback",
             "headers": {"Authorization": secret}, "diagnostics": [
                 {"route": "companion", "stage": "transport", "outcome": "http_error", "http_status": 401,
                  "raw_body": secret}]}
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=returncode, stdout=json.dumps(proof), stderr=secret))
    with pytest.raises(module.DashboardProofError) as caught:
        module.dashboard_request(tmp_path, {}, "fixture")
    printed = json.loads(capsys.readouterr().out)
    assert printed["dashboard_diagnostic"] == caught.value.receipt
    assert caught.value.receipt["diagnostics"][0]["http_status"] == 401
    assert secret not in json.dumps(printed)


def test_dashboard_failed_child_without_json_has_safe_failure_receipt(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    module = load_module()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=1, stdout="untrusted traceback fixture", stderr="private fixture"))
    with pytest.raises(module.DashboardProofError, match="dashboard_client_failed") as caught:
        module.dashboard_request(tmp_path, {}, "fixture")
    assert caught.value.receipt["diagnostics"] == []
    assert "traceback" not in capsys.readouterr().out
