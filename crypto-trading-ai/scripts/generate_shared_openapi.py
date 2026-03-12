#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "shared" / "openapi" / "api.yaml"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import app

HTTP_METHOD_ORDER = ("get", "post", "put", "patch", "delete", "options", "head")
HTTP_METHODS = set(HTTP_METHOD_ORDER)


def _yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _build_lines() -> list[str]:
    runtime_openapi = app.openapi()
    runtime_paths = runtime_openapi.get("paths", {})

    filtered_paths = [
        path
        for path in runtime_paths.keys()
        if path.startswith("/api/v1") or path.startswith("/health")
    ]

    filtered_paths.sort(key=lambda path: (0 if path.startswith("/health") else 1, path))

    lines: list[str] = [
        "openapi: 3.1.0",
        "info:",
        f"  title: {_yaml_string('Crypto Trading AI API')}",
        f"  version: {_yaml_string('0.1.0')}",
        f"  description: {_yaml_string('Generated from backend runtime OpenAPI. Do not edit manually.')}",
        "servers:",
        "  - url: http://localhost:8000",
        "paths:",
    ]

    for path in filtered_paths:
        lines.append(f"  {path}:")
        operations = runtime_paths[path]

        for method in HTTP_METHOD_ORDER:
            operation = operations.get(method)
            if operation is None or method not in HTTP_METHODS:
                continue

            summary = operation.get("summary") or f"{method.upper()} {path}"
            lines.append(f"    {method}:")
            lines.append(f"      summary: {_yaml_string(summary)}")
            lines.append("      responses:")

            responses = operation.get("responses", {})
            response_codes = sorted(str(code) for code in responses.keys())
            for response_code in response_codes:
                response = responses.get(response_code) or {}
                description = str(response.get("description", ""))
                lines.append(f"        {_yaml_string(response_code)}:")
                lines.append(f"          description: {_yaml_string(description)}")

    return lines


def _render_document() -> str:
    return "\n".join(_build_lines()) + "\n"


def _write_document(content: str) -> None:
    OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAPI_PATH.write_text(content, encoding="utf-8")


def _check_document(content: str) -> int:
    if not OPENAPI_PATH.exists():
        print(f"Missing file: {OPENAPI_PATH}")
        print("Run: python scripts/generate_shared_openapi.py")
        return 1

    existing = OPENAPI_PATH.read_text(encoding="utf-8")
    if existing == content:
        print("Shared OpenAPI file is in sync.")
        return 0

    print("Shared OpenAPI file is out of sync.")
    diff = difflib.unified_diff(
        existing.splitlines(),
        content.splitlines(),
        fromfile=str(OPENAPI_PATH),
        tofile="generated",
        lineterm="",
    )
    for line in diff:
        print(line)
    print("Run: python scripts/generate_shared_openapi.py")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate shared/openapi/api.yaml from backend runtime OpenAPI."
    )
    parser.add_argument("--check", action="store_true", help="Fail if shared OpenAPI is not in sync.")
    args = parser.parse_args()

    rendered = _render_document()
    if args.check:
        return _check_document(rendered)

    _write_document(rendered)
    print(f"Wrote {OPENAPI_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
