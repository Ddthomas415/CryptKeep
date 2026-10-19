"""Opt-in isolated companion verification; never uses existing volumes or .env."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dashboard.services.views._explain_diagnostics import sanitize_events  # noqa: E402


class DashboardProofError(RuntimeError):
    def __init__(self, reason: str, receipt: dict):
        super().__init__(reason)
        self.receipt = receipt


def isolated_config(root: Path, project: str, password: str, token: str) -> dict:
    config = yaml.safe_load((root / "docker-compose.yml").read_text())
    config.pop("x-runtime-environment", None)
    for name, service in config["services"].items():
        service["container_name"] = project + "-" + name
        service.pop("env_file", None)
        if "build" in service:
            service["build"]["context"] = str(root)
            service["environment"].update(POSTGRES_PASSWORD=password, SERVICE_TOKEN=token,
                MINIO_ACCESS_KEY="proof", MINIO_SECRET_KEY=password, OPENAI_API_KEY="",
                BROWSER_CHAT_TOKEN="", NO_TRADING="true", EXCHANGE_ID="coinbase",
                EXCHANGE_SYMBOLS="BTC/USD", MARKET_WS_ENABLED="false", NEWS_RSS_URLS="")
        if name == "timescaledb":
            service["environment"]["POSTGRES_PASSWORD"] = password
        if name == "minio":
            service["environment"].update(MINIO_ROOT_USER="proof", MINIO_ROOT_PASSWORD=password)
        service["ports"] = ["127.0.0.1::" + port.rsplit(":", 1)[1] for port in service.get("ports", [])]
        service["volumes"] = [str(root / "db/init") + ":/docker-entrypoint-initdb.d:ro"
            if volume.startswith("./db/init:") else str(root.parent) + ":/repo:ro"
            if volume.startswith("../:") else volume for volume in service.get("volumes", [])]
    return config


def reserve_output(root: Path, output: Path):
    destination = output.resolve()
    allowed = (root.parent / "docs/research").resolve()
    if not destination.is_relative_to(allowed) or destination.suffix != ".json":
        raise ValueError("output_must_be_new_research_json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination.open("x")


def local_docker_command(project: str) -> list[str]:
    endpoint = "unix://" + str(Path.home() / ".docker/run/docker.sock")
    return ["docker", "--host", endpoint, "compose", "-p", project, "-f", "-"]


def dashboard_request(repo: Path, environment: dict, code: str) -> dict:
    process = subprocess.run([str(repo / ".venv/bin/python"), "-B", "-c", code],
        cwd=repo, env=environment, capture_output=True, text=True, timeout=90)
    try:
        proof = json.loads(process.stdout.strip().splitlines()[-1])
        if not isinstance(proof, dict):
            proof = {}
    except (ValueError, IndexError):
        proof = {}
    provider = proof.get("provider")
    receipt = {"source_cited": proof.get("source_cited") if type(proof.get("source_cited")) is bool else None,
               "execution_disabled": proof.get("execution_disabled") if type(proof.get("execution_disabled")) is bool else None,
               "provider": provider if isinstance(provider, str) and provider in
                   ("backend_api", "phase1_copilot", "dashboard_fallback", "openai", "fallback") else "missing_or_other",
               "diagnostics": sanitize_events(proof.get("diagnostics"))}
    # Retain a safe receipt before any acceptance check can discard the failure details.
    print(json.dumps({"dashboard_diagnostic": receipt}), flush=True)
    if process.returncode:
        raise DashboardProofError("dashboard_client_failed", receipt)
    if (proof.get("source_cited") is not True or proof.get("execution_disabled") is not True
            or proof.get("provider") in (None, "", "dashboard_fallback")):
        raise DashboardProofError("dashboard_client_invalid_proof", receipt)
    return receipt


def run(root: Path, output: Path) -> int:
    if sys.flags.optimize:
        raise RuntimeError("optimized_verification_refused")
    project = "cbp-proof-" + secrets.token_hex(6)
    password, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    config = isolated_config(root, project, password, token)
    payload = yaml.safe_dump(config)
    result = {"project": project, "status": "INCOMPLETE", "existing_state_used": False,
              "trading_enabled": False, "checks": {}, "cleanup": "UNVERIFIED"}
    command = local_docker_command(project)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("DOCKER_") and key != "COMPOSE_PROJECT_NAME"}
    evidence_file = reserve_output(root, output)

    def compose(*args, timeout=240):
        process = subprocess.run(command + list(args), input=payload, text=True,
                                 capture_output=True, timeout=timeout, env=environment)
        if process.returncode:
            # Retain diagnostics without exposing ephemeral credentials.
            diagnostic = (process.stdout + process.stderr).replace(password, "[redacted]").replace(token, "[redacted]")
            result["diagnostic"] = diagnostic[-12000:]
            raise RuntimeError("compose_command_failed")
        return process.stdout

    try:
        print("Building isolated companion image", flush=True)
        compose("build", timeout=600)
        print("Starting isolated stack with disposable volumes", flush=True)
        compose("up", "-d", "--wait", "--wait-timeout", "180", timeout=240)
        def base(service, port):
            address = compose("port", service, str(port)).strip()
            if not address.startswith("127.0.0.1:"):
                raise RuntimeError("unexpected_listener")
            return "http://" + address
        parser, memory = base("parser-normalizer", 8006), base("memory-retrieval", 8007)
        orchestrator, gateway = base("orchestrator", 8002), base("gateway", 8001)
        headers = {"Authorization": "Bearer " + token}
        with httpx.Client(timeout=90, follow_redirects=False, trust_env=False) as client:
            print("Checking authenticated source ingestion and persistent retrieval", flush=True)
            health = client.get(memory + "/healthz")
            health.raise_for_status()
            assert health.json()["ok"], "memory_dependencies_unhealthy"
            result["checks"]["storage_health"] = health.json()
            parsed = client.post(parser + "/v1/parse/url", headers=headers,
                json={"url": "https://bitcoin.org/en/faq", "source": "bitcoin.org",
                      "source_type": "archive", "timeline_hint": "past", "asset_hint": ["BTC"]})
            parsed.raise_for_status()
            doc = parsed.json()["document"]
            assert doc["content_text"] and doc["published_at"] is None
            stored = client.post(memory + "/v1/memory/documents", headers=headers, json=doc)
            stored.raise_for_status()
            assert stored.json()["ok"]
            duplicate = client.post(memory + "/v1/memory/documents", headers=headers, json=doc)
            duplicate.raise_for_status()
            assert duplicate.json()["duplicate"]
            query = {"asset": "BTC", "question": "Bitcoin FAQ", "lookback_minutes": 60}
            retrieved = client.post(memory + "/v1/memory/retrieve", headers=headers, json=query)
            retrieved.raise_for_status()
            assert any(row["url"] == doc["url"] for row in retrieved.json()["vector_matches"])
            result["checks"]["source"] = {"url": doc["url"], "content_hash": doc["content_hash"],
                "document_id": stored.json()["document_id"], "duplicate_retry": True,
                "publication_date": None, "asset_hint": "operator-specified BTC"}
            # Recreate service processes only; owned test volumes remain intact.
            compose("restart", "memory-retrieval", timeout=60)
            memory = base("memory-retrieval", 8007)
            for attempt in range(30):
                try:
                    response = client.get(memory + "/healthz")
                    if response.status_code == 200 and response.json().get("ok"):
                        break
                except httpx.TransportError:
                    pass
                time.sleep(1)
            else:
                raise RuntimeError("memory_restart_unhealthy")
            retrieved = client.post(memory + "/v1/memory/retrieve", headers=headers, json=query)
            retrieved.raise_for_status()
            assert any(row["url"] == doc["url"] for row in retrieved.json()["vector_matches"])
            result["checks"]["retrieved_after_service_restart"] = True
            print("Checking explanation and chat boundaries", flush=True)
            denied = client.post(orchestrator + "/v1/explain", json=query)
            assert denied.status_code == 401
            explain = client.post(orchestrator + "/v1/explain", headers=headers, json=query)
            explain.raise_for_status()
            evidence = explain.json()
            assert evidence["execution_disabled"] is True
            assert any(row.get("url") == doc["url"] for row in evidence["evidence"])
            chat = client.post(gateway + "/v1/chat", headers=headers, json=query)
            chat.raise_for_status()
            assert chat.json()["execution_disabled"] is True
            assert chat.json()["assistant_response"]
            result["checks"]["explanation"] = {"source_cited": True, "unauthorized_denied": True,
                "provider": evidence["assistant_status"]["provider"], "chat_response_present": True}
            print("Checking actual dashboard client", flush=True)
            dashboard_env = dict(os.environ)
            dashboard_env.update(CK_API_BASE_URL="http://127.0.0.1:1",
                CK_PHASE1_ORCHESTRATOR_URL=orchestrator,
                CK_PHASE1_SERVICE_TOKEN=token, CK_PHASE1_API_TIMEOUT_SECONDS="30")
            dashboard_code = (
                "import json\n"
                "from dashboard.services.views.market_view import get_research_explain\n"
                "from dashboard.services.views._explain_diagnostics import capture_explain_diagnostics\n"
                "with capture_explain_diagnostics() as diagnostics:\n"
                "    p=get_research_explain('BTC', 'What does the archived Bitcoin source say?')\n"
                "print(json.dumps({'source_cited': any(r.get('url') == 'https://bitcoin.org/en/faq' "
                "for r in p.get('evidence', [])), 'execution_disabled': p.get('execution_disabled'), "
                "'provider': p.get('assistant_status', {}).get('provider'), 'diagnostics': diagnostics}))"
            )
            dashboard_proof = dashboard_request(root.parent, dashboard_env, dashboard_code)
            result["checks"]["dashboard_client"] = dashboard_proof
            result["status"] = "PASSED_LOCAL_STACK_CHECKS"
    except Exception as exc:
        if isinstance(exc, DashboardProofError):
            result["checks"]["dashboard_client"] = exc.receipt
        result["error_type"] = type(exc).__name__
        if isinstance(exc, (RuntimeError, AssertionError)):
            result["error_message"] = str(exc).replace(password, "[redacted]").replace(token, "[redacted]")
        try:
            logs = compose("logs", "--no-color", "--tail", "60", timeout=30)
            result["service_diagnostics"] = logs.replace(password, "[redacted]").replace(token, "[redacted]")[-16000:]
        except Exception:
            result["service_diagnostics"] = "unavailable"
    finally:
        print("Removing only owned test containers and volumes", flush=True)
        try:
            compose("down", "--volumes", "--remove-orphans", timeout=120)
            result["cleanup"] = "OWNED_STACK_REMOVED"
        except Exception as exc:
            result["cleanup"] = "FAILED:" + type(exc).__name__
        with evidence_file:
            evidence_file.write(json.dumps(result, indent=2) + "\n")
    print(result["status"], result["cleanup"], flush=True)
    return 0 if result["status"] == "PASSED_LOCAL_STACK_CHECKS" and result["cleanup"] == "OWNED_STACK_REMOVED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(Path(__file__).resolve().parents[2] / "phase1_research_copilot", args.output))
