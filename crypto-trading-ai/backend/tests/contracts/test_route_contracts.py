import re
from pathlib import Path

from fastapi.routing import APIRoute

from backend.app.main import app


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _parse_shared_openapi_paths(path: Path) -> dict[str, set[str]]:
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

        # Leave the top-level paths block when a new top-level key starts.
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


def test_api_v1_routes_use_api_envelope_response_models() -> None:
    api_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1")
    ]

    assert api_routes, "No /api/v1 routes found."

    for route in api_routes:
        assert route.response_model is not None, f"Missing response_model for {route.path}"
        model_name = getattr(route.response_model, "__name__", "")
        assert model_name.startswith(
            "ApiEnvelope["
        ), f"Route {route.path} must use ApiEnvelope response model, got {model_name!r}"


def test_shared_openapi_paths_match_runtime_routes() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    shared_spec_path = repo_root / "shared" / "openapi" / "api.yaml"
    assert shared_spec_path.exists(), "shared/openapi/api.yaml is missing."

    shared_paths = _parse_shared_openapi_paths(shared_spec_path)
    assert shared_paths, "No API paths parsed from shared/openapi/api.yaml."

    runtime_openapi = app.openapi()
    runtime_paths: dict[str, set[str]] = {}
    for path, operations in runtime_openapi.get("paths", {}).items():
        if not (path.startswith("/api/v1") or path.startswith("/health")):
            continue
        runtime_paths[path] = {
            method.lower() for method in operations.keys() if method.lower() in HTTP_METHODS
        }

    assert shared_paths == runtime_paths, (
        "shared/openapi/api.yaml paths/methods are out of sync with runtime OpenAPI.\n"
        f"shared={shared_paths}\n"
        f"runtime={runtime_paths}"
    )
