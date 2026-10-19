"""Explicit operator opt-in: configure and verify only the local companion gateway."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import yaml

import httpx
from dotenv import dotenv_values


def deploy(root: Path):
    docker = ["/usr/local/bin/docker", "--host", "unix:///Users/baitus/.docker/run/docker.sock"]
    def inspect(name):
        return json.loads(subprocess.check_output(docker + ["inspect", name], text=True))[0]
    gateway, database = inspect("phase1-gateway"), inspect("phase1-timescaledb")
    old = dict(row.split("=", 1) for row in gateway["Config"]["Env"] if "=" in row)
    db = dict(row.split("=", 1) for row in database["Config"]["Env"] if "=" in row)
    bindings = gateway["NetworkSettings"]["Ports"].get("8001/tcp", [])
    if not bindings or any(row["HostIp"] != "127.0.0.1" for row in bindings):
        raise RuntimeError("nonlocal_gateway_refused")
    if old.get("NO_TRADING") != "true":
        raise RuntimeError("trading_enabled_refused")
    config = dotenv_values(root / ".env")
    if any(not old.get(key) or old[key] != config.get(key)
           for key in ("SERVICE_TOKEN", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY")):
        raise RuntimeError("credential_drift_refused")
    token = old.get("BROWSER_CHAT_TOKEN") or secrets.token_urlsafe(32)
    if token == old["SERVICE_TOKEN"]:
        raise RuntimeError("shared_credential_refused")
    token_path = root / ".browser-access-token"
    # Never overwrite an existing operator credential artifact.
    descriptor = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as file:
        file.write(token + "\n")
    environment = {k: v for k, v in os.environ.items() if not k.startswith("DOCKER_")}
    environment.update(old)
    environment.update(POSTGRES_PASSWORD=db["POSTGRES_PASSWORD"], BROWSER_CHAT_TOKEN=token)
    service = yaml.safe_load((root / "docker-compose.yml").read_text())["services"]["gateway"]
    service.pop("env_file", None)
    service.pop("depends_on", None)
    service["build"]["context"] = str(root)
    service["volumes"] = [f'{m["Source"]}:{m["Destination"]}' + (":ro" if not m["RW"] else "")
        for m in gateway["Mounts"]]
    networks = list(gateway["NetworkSettings"]["Networks"])
    if networks != ["phase1_research_copilot_default"]:
        raise RuntimeError("unexpected_gateway_network")
    def configuration(image, values):
        return {"services": {"gateway": dict(service, image=image,
            environment={k: v.replace("$", "$$") for k, v in values.items()})},
            "networks": {"default": {"external": True, "name": networks[0]}}}
    # Only the gateway is recreated; database and other services are not started or rebuilt.
    override = root / ".browser-compose-override.json"
    descriptor = os.open(override, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as file:
        json.dump(configuration("cryptkeep-browser-" + secrets.token_hex(6), dict(old, BROWSER_CHAT_TOKEN=token)), file)
    compose = docker + ["compose", "-p", "phase1_research_copilot", "-f", str(override)]
    def execute(args):
        result = subprocess.run(compose + args, cwd=root, env=environment,
            capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise RuntimeError("gateway_compose_failed")
    try:
        execute(["build", "gateway"])
        execute(["up", "-d", "--no-deps", "gateway"])
        deployed = inspect("phase1-gateway")
        deployed_env = dict(row.split("=", 1) for row in deployed["Config"]["Env"] if "=" in row)
        if deployed_env != dict(old, BROWSER_CHAT_TOKEN=token):
            raise RuntimeError("gateway_environment_changed")
        with httpx.Client(timeout=60, trust_env=False, follow_redirects=False) as client:
            for _ in range(30):
                try:
                    response = client.get("http://127.0.0.1:8001/healthz")
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise RuntimeError("gateway_unhealthy")
            query = {"asset": "BTC", "question": "What evidence is stored for Bitcoin?", "lookback_minutes": 60}
            refused = client.post("http://127.0.0.1:8001/v1/browser/chat", json=query)
            if refused.status_code != 401:
                raise RuntimeError("browser_auth_denial_failed")
            response = client.post("http://127.0.0.1:8001/v1/browser/chat", json=query,
                headers={"Authorization": "Bearer " + token})
            response.raise_for_status()
            data = response.json()
            if (data.get("execution_disabled") is not True or not data.get("assistant_response")
                    or data.get("chat_status", {}).get("upstream_fallback")
                    or not data.get("evidence")):
                raise RuntimeError("browser_response_invalid")
            page_response = client.get("http://127.0.0.1:8001/")
            page_response.raise_for_status()
            page = page_response.text
            if token in page or old["SERVICE_TOKEN"] in page:
                raise RuntimeError("credential_in_page")
        return {"status": "VERIFIED_LOCAL_BROWSER_ROUTE", "execution_disabled": True,
            "unauthorized_denied": True, "token_file": str(token_path), "token_mode": "0600",
            "other_services_recreated": False}
    except Exception:
        environment["BROWSER_CHAT_TOKEN"] = old.get("BROWSER_CHAT_TOKEN", "")
        # The override allows empty values for rollback to the prior disabled route.
        with override.open("w") as file:
            json.dump(configuration(gateway["Image"], dict(old, BROWSER_CHAT_TOKEN=old.get("BROWSER_CHAT_TOKEN", ""))), file)
        execute(["up", "-d", "--no-deps", "gateway"])
        restored = inspect("phase1-gateway")
        restored_env = dict(row.split("=", 1) for row in restored["Config"]["Env"] if "=" in row)
        if (restored["Image"] != gateway["Image"]
                or restored_env != dict(old, BROWSER_CHAT_TOKEN=old.get("BROWSER_CHAT_TOKEN", ""))):
            raise RuntimeError("rollback_not_verified")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deploy", action="store_true", required=True)
    parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    print(json.dumps(deploy(repo / "phase1_research_copilot")))
