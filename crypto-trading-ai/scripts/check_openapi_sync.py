#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import app

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def parse_shared_openapi_paths(path: Path) -> dict[str, set[str]]:
    text = path.read_text(encoding="utf-8")
    in_paths = False
    current_path: str | None = None
    parsed: dict[str, set[str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")

        if line.strip() == "paths:":
            in_paths = True
            continue

        if not in_paths:
            continue

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", line):
            break

        path_match = re.match(r"^  (/[^:]+):\s*$", line)
        if path_match:
            current_path = path_match.group(1)
            parsed.setdefault(current_path, set())
            continue

        method_match = re.match(r"^    ([a-z]+):\s*$", line)
        if method_match and current_path:
            method = method_match.group(1).lower()
            if method in HTTP_METHODS:
                parsed[current_path].add(method)

    return parsed


def collect_runtime_paths() -> dict[str, set[str]]:
    runtime_openapi = app.openapi()
    runtime_paths: dict[str, set[str]] = {}

    for path, operations in runtime_openapi.get("paths", {}).items():
        if not (path.startswith("/api/v1") or path.startswith("/health")):
            continue
        runtime_paths[path] = {
            method.lower() for method in operations.keys() if method.lower() in HTTP_METHODS
        }

    return runtime_paths


def check_api_envelope_usage() -> list[str]:
    errors: list[str] = []
    api_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1")
    ]

    if not api_routes:
        return ["No /api/v1 routes found in runtime app."]

    for route in api_routes:
        response_model = route.response_model
        if response_model is None:
            errors.append(f"Missing response_model for {route.path}")
            continue

        model_name = getattr(response_model, "__name__", "")
        if not model_name.startswith("ApiEnvelope["):
            errors.append(
                f"Route {route.path} must use ApiEnvelope response_model, got {model_name!r}"
            )

    return errors


def check_openapi_sync() -> list[str]:
    errors: list[str] = []
    shared_spec_path = ROOT / "shared" / "openapi" / "api.yaml"
    if not shared_spec_path.exists():
        return ["shared/openapi/api.yaml is missing."]

    shared_paths = parse_shared_openapi_paths(shared_spec_path)
    if not shared_paths:
        return ["No API paths parsed from shared/openapi/api.yaml."]

    runtime_paths = collect_runtime_paths()
    if not runtime_paths:
        return ["No /api/v1 or /health runtime paths found in app OpenAPI."]

    shared_only = sorted(set(shared_paths) - set(runtime_paths))
    runtime_only = sorted(set(runtime_paths) - set(shared_paths))
    if shared_only:
        errors.append(f"Paths only in shared/openapi/api.yaml: {shared_only}")
    if runtime_only:
        errors.append(f"Paths only in runtime OpenAPI: {runtime_only}")

    for path in sorted(set(shared_paths) & set(runtime_paths)):
        shared_methods = shared_paths[path]
        runtime_methods = runtime_paths[path]
        if shared_methods != runtime_methods:
            errors.append(
                "Method drift for "
                f"{path}: shared={sorted(shared_methods)} runtime={sorted(runtime_methods)}"
            )

    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_api_envelope_usage())
    errors.extend(check_openapi_sync())

    if errors:
        print("OpenAPI/route contract checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("OpenAPI/route contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
