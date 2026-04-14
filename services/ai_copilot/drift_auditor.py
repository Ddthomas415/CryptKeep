from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dashboard.services import view_data as dashboard_view_data
from services.ai_copilot.policy import report_root
from services.os.app_paths import code_root


def _root() -> Path:
    return code_root()


def _read_text(rel_path: str) -> str:
    path = _root() / rel_path
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _python_assignment_literal(rel_path: str, name: str, default: Any) -> Any:
    path = _root() / rel_path
    if not path.exists():
        return default
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return default
    return default


def _dashboard_venue_options() -> list[str]:
    rel_path = "dashboard/pages/50_Automation.py"
    path = _root() / rel_path
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported_names: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local_name = alias.asname or alias.name
                imported_names[local_name] = f"{node.module.replace('.', '/')}.py::{alias.name}"
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "venue_options":
                continue
            try:
                value = ast.literal_eval(node.value)
                return sorted(value)
            except Exception:
                pass
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "list"
                and len(node.value.args) == 1
                and isinstance(node.value.args[0], ast.Name)
            ):
                imported_ref = imported_names.get(node.value.args[0].id)
                if imported_ref:
                    module_rel_path, imported_name = imported_ref.split("::", 1)
                    imported_value = _python_assignment_literal(module_rel_path, imported_name, [])
                    return sorted(imported_value)
            return []
    return []


def _python_assignment_dict_keys(rel_path: str, name: str) -> list[str]:
    path = _root() / rel_path
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name and isinstance(node.value, ast.Dict):
                    keys: list[str] = []
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            keys.append(key.value)
                    return sorted(keys)
    return []


def _python_function_names(rel_path: str) -> list[str]:
    path = _root() / rel_path
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]


def _markdown_bullets_after_heading(rel_path: str, heading: str) -> list[str]:
    lines = _read_text(rel_path).splitlines()
    out: list[str] = []
    capture = False
    for raw in lines:
        line = raw.strip()
        if line == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("- "):
            out.append(line[2:].strip())
    return out


def _extract_watchlist_assets(view_data_text: str) -> list[str]:
    assets: list[str] = []
    marker = '"watchlist": ['
    idx = view_data_text.find(marker)
    if idx < 0:
        return assets
    window = view_data_text[idx : idx + 500]
    for candidate in ("BTC", "ETH", "SOL"):
        if f'"asset": "{candidate}"' in window:
            assets.append(candidate)
    return assets


def _extract_trading_symbols() -> list[str]:
    text = _read_text("config/trading.yaml")
    symbols: list[str] = []
    capture = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "symbols:":
            capture = True
            continue
        if capture and stripped.startswith("- "):
            symbols.append(stripped[2:].strip())
            continue
        if capture and stripped and not raw.startswith("  "):
            break
    return symbols


def _exchange_support_check() -> dict[str, Any]:
    docs_exchanges = sorted(_markdown_bullets_after_heading("docs/EXCHANGES.md", "## Venues configured"))
    preflight_supported = sorted(_python_assignment_literal("services/preflight/preflight.py", "SUPPORTED_EXCHANGES", set()))
    dashboard_venues = _dashboard_venue_options()
    venue_caps = _python_assignment_dict_keys("services/execution/venue_capabilities.py", "_CAPS")

    mismatch = not (
        set(docs_exchanges) == set(preflight_supported)
        and set(preflight_supported).issuperset(set(venue_caps))
        and set(dashboard_venues) == set(preflight_supported)
    )
    issues: list[str] = []
    if set(dashboard_venues) != set(preflight_supported):
        issues.append("dashboard venue options do not match backend supported exchanges")
    if set(venue_caps) != set(preflight_supported):
        issues.append("venue capability coverage does not match backend supported exchanges")
    if set(docs_exchanges) != set(preflight_supported):
        issues.append("docs exchange list does not match backend supported exchanges")
    return {
        "name": "exchange_support_drift",
        "ok": not mismatch,
        "severity": "warn" if mismatch else "ok",
        "docs_exchanges": docs_exchanges,
        "preflight_supported": preflight_supported,
        "dashboard_venues": dashboard_venues,
        "venue_capabilities": venue_caps,
        "issues": issues,
    }


def _dashboard_fallback_truth_check() -> dict[str, Any]:
    # view_data.py is a facade; helpers are split across views/_shared_*.py
    rel_path = "dashboard/services/view_data.py"
    from pathlib import Path as _Path
    views_dir = _Path("dashboard/services/views")
    shared_texts = [_read_text(rel_path)]
    shared_fns = _python_function_names(rel_path)
    for _sp in sorted(views_dir.glob("_shared*.py")):
        _sp_rel = str(_sp)
        shared_texts.append(_read_text(_sp_rel))
        shared_fns += _python_function_names(_sp_rel)
    view_data_text = "\n".join(shared_texts)
    function_names = shared_fns
    fallback_functions = sorted(name for name in function_names if name.startswith("_default_"))
    watchlist_assets = sorted(dashboard_view_data._repo_default_watchlist_assets())
    summary_fallback_labeled = '"data_provenance"' in view_data_text and '"dashboard_fallback"' in view_data_text
    has_unlabeled_fallback_truth = bool(fallback_functions) and not summary_fallback_labeled
    return {
        "name": "dashboard_fallback_truth",
        "ok": not has_unlabeled_fallback_truth,
        "severity": "warn" if has_unlabeled_fallback_truth else "ok",
        "fallback_functions": fallback_functions,
        "summary_fallback_labeled": summary_fallback_labeled,
        "watchlist_assets": watchlist_assets,
        "issue": "dashboard summary fallback truth is not explicitly labeled" if has_unlabeled_fallback_truth else "",
    }


def _default_universe_check() -> dict[str, Any]:
    trading_symbols = _extract_trading_symbols()
    watchlist_assets = sorted(dashboard_view_data._repo_default_watchlist_assets())
    symbol_bases = sorted({item.split("/")[0].upper() for item in trading_symbols})
    drift = sorted(set(watchlist_assets) - set(symbol_bases))
    return {
        "name": "default_universe_drift",
        "ok": not bool(drift),
        "severity": "warn" if drift else "ok",
        "trading_symbols": trading_symbols,
        "trading_symbol_bases": symbol_bases,
        "dashboard_watchlist_assets": watchlist_assets,
        "assets_only_in_dashboard_defaults": drift,
    }


def build_drift_report() -> dict[str, Any]:
    checks = [
        _exchange_support_check(),
        _dashboard_fallback_truth_check(),
        _default_universe_check(),
    ]
    severity = "ok"
    for check in checks:
        if check["severity"] == "warn":
            severity = "warn"
            break

    issues: list[str] = []
    for check in checks:
        if check["severity"] != "ok":
            name = str(check.get("name") or "check")
            if isinstance(check.get("issues"), list) and check.get("issues"):
                issues.extend(f"{name}: {item}" for item in check["issues"])
            elif str(check.get("issue") or "").strip():
                issues.append(f"{name}: {str(check.get('issue'))}")
            elif isinstance(check.get("assets_only_in_dashboard_defaults"), list) and check.get("assets_only_in_dashboard_defaults"):
                issues.append(
                    f"{name}: dashboard defaults include assets absent from trading.yaml ({', '.join(check['assets_only_in_dashboard_defaults'])})"
                )

    summary = (
        "No concrete repo drift was detected in the current fixed checks."
        if severity == "ok"
        else "Concrete repo drift was detected in exchange support or dashboard truth/default surfaces."
    )
    recommendations: list[str] = []
    failing_checks = {str(check.get("name") or "") for check in checks if check.get("severity") != "ok"}
    if "exchange_support_drift" in failing_checks:
        recommendations.append("Make dashboard venue options derive from the same backend-supported exchange registry.")
    if "dashboard_fallback_truth" in failing_checks:
        recommendations.append("Label or remove dashboard fallback/sample data where runtime truth is unavailable.")
    if "default_universe_drift" in failing_checks:
        recommendations.append("Align default dashboard watchlist assets with configured trading symbols or a declared universe source.")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "ok": severity == "ok",
        "summary": summary,
        "checks": checks,
        "issues": issues,
        "recommendations": recommendations,
    }


def render_drift_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CryptKeep Drift Audit",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Severity: {report.get('severity')}",
        f"- Drift OK: {bool(report.get('ok'))}",
        "",
        "## Summary",
        str(report.get("summary") or ""),
        "",
        "## Issues",
    ]
    issues = list(report.get("issues") or [])
    if issues:
        lines.extend(f"- {item}" for item in issues)
    else:
        lines.append("- `(none)`")

    lines.append("")
    lines.append("## Checks")
    for check in list(report.get("checks") or []):
        lines.append(f"- `{check.get('name')}` -> `{check.get('severity')}`")

    lines.extend(["", "## Recommendations"])
    lines.extend(f"- {item}" for item in list(report.get("recommendations") or []))
    return "\n".join(lines) + "\n"


def write_drift_report(report: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_stem = str(stem or f"drift_audit_{ts}").strip().replace(" ", "_")
    json_path = root / f"{safe_stem}.json"
    markdown_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_drift_markdown(report), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}
