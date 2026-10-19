"""Offline review bundle only: no executable approval, Docker, imports of targets or secrets."""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile

from scripts.research import companion_runtime_adapter as adapter


def read_source(root, path):
    if path.suffix != ".py" or path.resolve(strict=True) != path or not path.is_relative_to(root):
        raise ValueError("source_path_refused")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("source_type_refused")
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("source_size_refused")
    return raw


def static_sources(root, seeds):
    """Conservative static import inventory, including package initializers and lazy imports.

    Not a runtime resolver: external packages, dynamic loading and data files remain
    separate evidence. Target modules are parsed, never imported.
    """
    root = root.resolve()
    phase = root / "phase1_research_copilot"
    pending, files, external, dynamic = list(seeds), {}, set(), []

    def resolve(module):
        if not module or any(not word.isidentifier() for word in module.split(".")):
            return None
        for base in (phase, root):
            stem = base.joinpath(*module.split("."))
            for path in (stem.with_suffix(".py"), stem / "__init__.py"):
                if path.is_file() or path.is_symlink():
                    return path
        return None

    while pending:
        path = pending.pop()
        local = path.relative_to(root).as_posix()
        if local in files:
            continue
        if len(files) >= 1024:
            raise ValueError("static_inventory_limit")
        raw = read_source(root, path)
        files[local] = raw
        base = phase if path.is_relative_to(phase) else root
        for parent in path.parents:
            if parent == base:
                break
            init = parent / "__init__.py"
            if init.is_file() or init.is_symlink():
                pending.append(init)
        package = list(path.relative_to(base).parts[:-1])
        for node in ast.walk(ast.parse(raw, filename=local)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level > len(package):
                        raise ValueError("relative_import_outside_package")
                    prefix = package[:len(package) - node.level + 1]
                    module = ".".join(prefix + ([node.module] if node.module else []))
                else:
                    module = node.module or ""
                modules = [module]
                modules.extend(module + "." + alias.name for alias in node.names
                               if alias.name != "*" and resolve(module + "." + alias.name))
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in {"__import__", "import_module", "exec", "eval"}:
                    dynamic.append({"local": local, "line": node.lineno, "kind": name})
            for module in modules:
                imported = resolve(module)
                if imported:
                    pending.append(imported)
                elif module:
                    external.add(module)
    return files, sorted(external), sorted(dynamic, key=lambda r: (r["local"], r["line"]))


def prepare(root, output):
    root = root.resolve()
    base_path = root / "docs/review_artifacts/companion_compatibility_20261016.json"
    baseline = json.loads(base_path.read_bytes())
    compose_path = root / "phase1_research_copilot/docker-compose.yml"
    import yaml
    # Parse the template only; never interpolate or render its env_file/credentials.
    compose = yaml.safe_load(compose_path.read_bytes())["services"]
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": "companion-install-review-v2", "state": "READY_FOR_INDEPENDENT_REVIEW",
                "installation_authorized": False, "compatible_with_executable_plan_loader": False,
                "baseline_evidence": {"path": str(base_path.relative_to(root)),
                                      "sha256": hashlib.sha256(base_path.read_bytes()).hexdigest(),
                                      "observed_at": baseline["recorded_at_utc"]},
                "baseline_observations": baseline["targets"], "applications": [],
                "unresolved": ["Exact current StartedAt, network IDs/aliases/IPAM and full recreation metadata",
                               "Expected replacement preservation digests derived from verified metadata",
                               "Mounted repo import precedence and runtime identity; static hashes are not isolation",
                               "Hard registry isolation; prior single build was prefer-local, not a no-egress proof",
                               "Complete installed SDK/startup policy and external review bindings"],
                "policy_evidence": {"env_stdin_lossless": "SHOWN for covered native CLI fixtures",
                                    "image_provenance": "SHOWN for selected prior inspections",
                                    "builder_local_only": "UNVERIFIED as a hard no-pull guarantee",
                                    "recreation_complete": "UNVERIFIED", "sdk_startup_compatible": "UNVERIFIED as a whole",
                                    "source_imports_frozen": "UNVERIFIED at runtime; static bytes frozen here"}}
    for name, module in adapter.APP_MODULES.items():
        required = adapter.required_app_sources(name)
        seeds = [root / "phase1_research_copilot" / path.removeprefix("/app/") for path in sorted(required)]
        files, external, dynamic = static_sources(root, seeds)
        app_sources, repo_sources = [], []
        context = io.BytesIO()
        parent = next(row["image_id"] for row in baseline["targets"] if row["name"] == name)
        with tarfile.open(fileobj=context, mode="w") as archive:
            for local, raw in sorted(files.items()):
                phase_source = local.startswith("phase1_research_copilot/")
                destination = "/app/" + local.split("/", 1)[1] if phase_source else "/repo/" + local
                row = {"local": local, "destination": destination,
                       "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                (app_sources if phase_source else repo_sources).append(row)
                info = tarfile.TarInfo(local)
                info.size, info.mode, info.mtime = len(raw), 0o644, 0
                archive.addfile(info, io.BytesIO(raw))
        snapshot = context.getvalue()
        filename = name + "-sources.tar"
        (output / filename).write_bytes(snapshot)
        service = compose[adapter.ALIASES[name]]
        manifest["applications"].append({"name": name, "parent_image": parent,
            "sources": app_sources, "mounted_repo_sources": repo_sources,
            "source_snapshot": filename, "snapshot_sha256": hashlib.sha256(snapshot).hexdigest(),
            "external_imports_not_resolved": external, "dynamic_loading_sites": dynamic,
            "template_only_not_runtime_proof": {"ports": service.get("ports", []),
                "volumes": service.get("volumes", []), "healthcheck": service.get("healthcheck"),
                "environment_keys": sorted(service.get("environment", {})),
                "service_module": module + ".main"},
            "missing_executable_fields": ["create_options", "network_options", "replacement_metadata"],
            "non_python_data_not_in_snapshot": ["article_archive and optional .required marker"] if name == "phase1-memory" else []})
    manifest["template_sha256"] = hashlib.sha256(compose_path.read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.root, args.output)
    print(json.dumps({"state": result["state"], "installation_authorized": False,
                      "applications": [{"name": row["name"], "application_sources": len(row["sources"]),
                                        "repo_sources": len(row["mounted_repo_sources"]),
                                        "dynamic_sites": len(row["dynamic_loading_sites"])} for row in result["applications"]]}))


if __name__ == "__main__":
    main()
