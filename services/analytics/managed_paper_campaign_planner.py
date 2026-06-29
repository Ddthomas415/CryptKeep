from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.paper_campaign_recovery import PaperCampaignSpec, load_campaign_specs
from services.os.app_paths import code_root, data_dir, runtime_dir
from services.os.file_utils import atomic_write
from services.strategies.strategy_registry import SUPPORTED as SUPPORTED_STRATEGIES

REPORT_TYPE = "managed_paper_campaign_plan"
DEFAULT_LAPTOP_MANIFEST = code_root() / "configs" / "paper_evidence_campaigns.laptop.json"
DEFAULT_HETZNER_MANIFEST = code_root() / "configs" / "paper_evidence_campaigns.hetzner.example.json"
DEFAULT_CANDIDATE_ARTIFACT = runtime_dir() / "candidates" / "latest_candidates.json"
DEFAULT_CANDIDATE_OUTCOMES_ARTIFACT = data_dir() / "candidate_outcomes" / "candidate_outcomes.latest.json"
DEFAULT_SIGNAL_QUALITY_ARTIFACT = data_dir() / "signal_quality" / "signal_quality.latest.json"
HOST_MANIFESTS = {
    "laptop": DEFAULT_LAPTOP_MANIFEST,
    "hetzner": DEFAULT_HETZNER_MANIFEST,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> tuple[Any | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), "loaded"
    except (OSError, json.JSONDecodeError):
        return None, "invalid_json"


def _candidate_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("candidates") or payload.get("rows") or []
    else:
        rows = []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _safe_id(*parts: str) -> str:
    raw = "_".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())
    cleaned = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return cleaned or "candidate"


def _score(row: dict[str, Any]) -> float:
    try:
        return float(row.get("composite_score") or row.get("candidate_score") or row.get("score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _strategy(row: dict[str, Any]) -> str:
    return str(row.get("preferred_strategy") or row.get("strategy") or "").strip()


def _signal_source(strategy: str) -> str:
    return "public_ohlcv_1d" if strategy == "sma_200_trend" else "public_ohlcv_5m"


def _candidate_advisor_disabled(root: Path) -> bool:
    path = root / "configs" / "strategies" / "es_daily_trend_v1.yaml"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return bool(re.search(r"^\s*use_candidate_advisor:\s*false\b", text, flags=re.MULTILINE))


def _spec_row(spec: PaperCampaignSpec, *, host: str, manifest_path: Path, root: Path) -> dict[str, Any]:
    return {
        "name": spec.name,
        "host_owner": host,
        "manifest_path": _rel(manifest_path, root),
        "state_dir": _rel(spec.state_dir, root),
        "strategy": spec.strategy,
        "session_strategy_id": spec.session_strategy_id,
        "symbol": spec.symbol,
        "venue": spec.venue,
        "signal_source": spec.signal_source,
        "runtime_sec": spec.runtime_sec,
        "strategy_drain_sec": spec.strategy_drain_sec,
        "poll_interval_sec": spec.poll_interval_sec,
        "max_daily_attempts": spec.max_daily_attempts,
        "desktop_notify": spec.desktop_notify,
    }


def _load_existing_campaigns(
    *,
    manifests: dict[str, Path],
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for host, manifest_path in manifests.items():
        try:
            specs = load_campaign_specs(manifest_path, repo_root=root)
        except Exception as exc:
            errors.append(
                {
                    "type": "invalid_manifest",
                    "host_owner": host,
                    "manifest_path": _rel(manifest_path, root),
                    "reason": f"{type(exc).__name__}:{exc}",
                }
            )
            continue
        rows.extend(_spec_row(spec, host=host, manifest_path=manifest_path, root=root) for spec in specs)
    errors.extend(_duplicate_errors(rows))
    return rows, errors


def _duplicate_errors(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    checks = [
        ("duplicate_campaign_name", lambda row: str(row.get("name") or "")),
        ("duplicate_state_dir", lambda row: str(row.get("state_dir") or "")),
        (
            "duplicate_strategy_session_symbol_venue_owner",
            lambda row: "|".join(
                [
                    str(row.get("strategy") or ""),
                    str(row.get("session_strategy_id") or ""),
                    str(row.get("symbol") or "").upper(),
                    str(row.get("venue") or "").lower(),
                ]
            ),
        ),
    ]
    for error_type, key_fn in checks:
        seen: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = key_fn(row)
            if not key:
                continue
            if key in seen:
                errors.append(
                    {
                        "type": error_type,
                        "key": key,
                        "first": str(seen[key].get("name") or ""),
                        "second": str(row.get("name") or ""),
                    }
                )
            else:
                seen[key] = row
    return errors


def _manifest_row_for_candidate(
    row: dict[str, Any],
    *,
    proposal_host: str,
) -> dict[str, Any]:
    strategy = _strategy(row)
    symbol = str(row.get("symbol") or "").strip().upper()
    campaign_id = _safe_id(strategy, symbol, "default")
    return {
        "name": campaign_id,
        "enabled": True,
        "state_dir": f".cbp_state_challengers/{campaign_id}_daily",
        "strategy": strategy,
        "session_strategy_id": campaign_id,
        "symbol": symbol,
        "venue": str(row.get("venue") or "coinbase").strip().lower(),
        "signal_source": _signal_source(strategy),
        "runtime_sec": 900,
        "strategy_drain_sec": 2,
        "poll_interval_sec": 300,
        "max_daily_attempts": 2,
        "desktop_notify": proposal_host != "hetzner",
    }


def _owner_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("strategy") or ""),
        str(row.get("session_strategy_id") or ""),
        str(row.get("symbol") or "").upper(),
        str(row.get("venue") or "").lower(),
    )


def _candidate_rejection_reasons(
    candidate: dict[str, Any],
    *,
    manifest_row: dict[str, Any],
    proposal_host: str,
    min_score: float,
    existing_names: set[str],
    existing_state_dirs: set[str],
    existing_owners: set[tuple[str, str, str, str]],
    proposed_names: set[str],
    proposed_state_dirs: set[str],
    proposed_owners: set[tuple[str, str, str, str]],
) -> list[str]:
    reasons: list[str] = []
    strategy = str(manifest_row.get("strategy") or "")
    symbol = str(manifest_row.get("symbol") or "")
    if not strategy:
        reasons.append("missing_strategy")
    elif strategy not in SUPPORTED_STRATEGIES:
        reasons.append("unsupported_strategy")
    if not symbol:
        reasons.append("missing_symbol")
    if _score(candidate) < float(min_score):
        reasons.append("candidate_score_below_threshold")
    if proposal_host not in {"laptop", "hetzner"}:
        reasons.append("host_not_selected")
    if str(manifest_row.get("name") or "") in existing_names:
        reasons.append("duplicate_campaign_name")
    if str(manifest_row.get("state_dir") or "") in existing_state_dirs:
        reasons.append("duplicate_state_dir")
    owner = _owner_key(manifest_row)
    if owner in existing_owners:
        reasons.append("duplicate_strategy_session_symbol_venue_owner")
    if str(manifest_row.get("name") or "") in proposed_names:
        reasons.append("duplicate_candidate_campaign_name")
    if str(manifest_row.get("state_dir") or "") in proposed_state_dirs:
        reasons.append("duplicate_candidate_state_dir")
    if owner in proposed_owners:
        reasons.append("duplicate_candidate_strategy_session_symbol_venue_owner")
    return reasons


def _candidate_artifact_status(
    *,
    candidate_status: str,
    candidate_count: int,
    outcome_status: str,
    signal_quality_status: str,
) -> str:
    if candidate_status != "loaded" or candidate_count <= 0:
        return "insufficient_candidate_evidence"
    if outcome_status != "loaded" and signal_quality_status != "loaded":
        return "candidate_snapshot_only"
    return "candidate_evidence_loaded"


def build_managed_paper_campaign_plan(
    *,
    repo_root: Path | None = None,
    laptop_manifest: Path = DEFAULT_LAPTOP_MANIFEST,
    hetzner_manifest: Path = DEFAULT_HETZNER_MANIFEST,
    candidate_artifact: Path = DEFAULT_CANDIDATE_ARTIFACT,
    candidate_outcomes_artifact: Path = DEFAULT_CANDIDATE_OUTCOMES_ARTIFACT,
    signal_quality_artifact: Path = DEFAULT_SIGNAL_QUALITY_ARTIFACT,
    proposal_host: str = "neither",
    min_score: float = 50.0,
    max_candidates: int = 5,
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    manifests = {
        "laptop": Path(laptop_manifest),
        "hetzner": Path(hetzner_manifest),
    }
    existing, manifest_errors = _load_existing_campaigns(manifests=manifests, root=root)

    candidate_payload, candidate_status = _read_json(Path(candidate_artifact))
    outcome_payload, outcome_status = _read_json(Path(candidate_outcomes_artifact))
    signal_quality_payload, signal_quality_status = _read_json(Path(signal_quality_artifact))
    candidates = _candidate_rows(candidate_payload)[: int(max_candidates)]

    existing_names = {str(row.get("name") or "") for row in existing}
    existing_state_dirs = {str(row.get("state_dir") or "") for row in existing}
    existing_owners = {_owner_key(row) for row in existing}
    proposed_names: set[str] = set()
    proposed_state_dirs: set[str] = set()
    proposed_owners: set[tuple[str, str, str, str]] = set()
    proposals: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates, start=1):
        manifest_row = _manifest_row_for_candidate(candidate, proposal_host=proposal_host)
        reasons = _candidate_rejection_reasons(
            candidate,
            manifest_row=manifest_row,
            proposal_host=str(proposal_host),
            min_score=float(min_score),
            existing_names=existing_names,
            existing_state_dirs=existing_state_dirs,
            existing_owners=existing_owners,
            proposed_names=proposed_names,
            proposed_state_dirs=proposed_state_dirs,
            proposed_owners=proposed_owners,
        )
        candidate_summary = {
            "candidate_index": index,
            "symbol": str(candidate.get("symbol") or "").strip().upper(),
            "strategy": _strategy(candidate),
            "score": _score(candidate),
            "trade_type": str(candidate.get("trade_type") or ""),
        }
        row = {
            "candidate": candidate_summary,
            "host_owner": proposal_host if proposal_host in HOST_MANIFESTS else "neither",
            "target_manifest": _rel(manifests[proposal_host], root)
            if proposal_host in manifests
            else "",
            "proposed_manifest_row": manifest_row,
            "evidence": {
                "candidate_artifact": _rel(Path(candidate_artifact), root),
                "candidate_outcomes_artifact_status": outcome_status,
                "signal_quality_artifact_status": signal_quality_status,
            },
        }
        if reasons:
            rejected.append({**row, "status": "rejected", "reasons": reasons})
            continue
        proposals.append({**row, "status": "proposed", "reasons": []})
        proposed_names.add(str(manifest_row.get("name") or ""))
        proposed_state_dirs.add(str(manifest_row.get("state_dir") or ""))
        proposed_owners.add(_owner_key(manifest_row))

    candidate_evidence_status = _candidate_artifact_status(
        candidate_status=candidate_status,
        candidate_count=len(candidates),
        outcome_status=outcome_status,
        signal_quality_status=signal_quality_status,
    )
    status = "ok"
    if manifest_errors:
        status = "invalid_manifest"
    elif candidate_evidence_status == "insufficient_candidate_evidence":
        status = "insufficient_candidate_evidence"
    elif not proposals:
        status = "no_eligible_proposals"

    return {
        "generated_at": _now_iso(),
        "report_type": REPORT_TYPE,
        "status": status,
        "read_only": True,
        "parameters": {
            "proposal_host": proposal_host,
            "min_score": float(min_score),
            "max_candidates": int(max_candidates),
        },
        "artifact_inputs": {
            "candidate_artifact": {
                "path": _rel(Path(candidate_artifact), root),
                "status": candidate_status,
                "candidate_count": len(candidates),
            },
            "candidate_outcomes_artifact": {
                "path": _rel(Path(candidate_outcomes_artifact), root),
                "status": outcome_status,
                "report_type": dict(outcome_payload).get("report_type")
                if isinstance(outcome_payload, dict)
                else "",
            },
            "signal_quality_artifact": {
                "path": _rel(Path(signal_quality_artifact), root),
                "status": signal_quality_status,
                "strategy_id": dict(signal_quality_payload).get("strategy_id")
                if isinstance(signal_quality_payload, dict)
                else "",
            },
        },
        "candidate_evidence_status": candidate_evidence_status,
        "manifest_errors": manifest_errors,
        "existing_campaigns": existing,
        "proposals": proposals,
        "rejected_candidates": rejected,
        "summary": {
            "existing_campaigns": len(existing),
            "candidate_rows_reviewed": len(candidates),
            "proposal_count": len(proposals),
            "rejected_count": len(rejected),
            "manifest_error_count": len(manifest_errors),
        },
        "safety": {
            "read_only": True,
            "campaigns_started": False,
            "campaigns_stopped": False,
            "restore_invoked": False,
            "manifest_files_written": False,
            "state_dirs_created": False,
            "candidate_advisor_enabled": False,
            "candidate_advisor_config_disabled": _candidate_advisor_disabled(root),
            "orders_routed": False,
            "promotion_gate_mutated": False,
        },
        "do_not_touch": [
            "do_not_start_or_stop_campaigns",
            "do_not_call_restore_paper_campaigns_restore",
            "do_not_mutate_campaign_manifests",
            "do_not_create_or_delete_state_dirs",
            "do_not_enable_candidate_advisor",
            "do_not_route_orders",
        ],
    }


def render_managed_paper_campaign_plan_markdown(report: dict[str, Any]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# Managed Paper Campaign Plan",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Status: `{report.get('status')}`",
        f"- Read-only: `{bool(report.get('read_only'))}`",
        f"- Existing campaigns: `{summary.get('existing_campaigns')}`",
        f"- Candidate rows reviewed: `{summary.get('candidate_rows_reviewed')}`",
        f"- Proposals: `{summary.get('proposal_count')}`",
        f"- Rejected: `{summary.get('rejected_count')}`",
        "",
        "## Proposals",
    ]
    for proposal in list(report.get("proposals") or []):
        if not isinstance(proposal, dict):
            continue
        campaign = dict(proposal.get("proposed_manifest_row") or {})
        lines.append(
            f"- `{campaign.get('name')}` host=`{proposal.get('host_owner')}` "
            f"strategy=`{campaign.get('strategy')}` symbol=`{campaign.get('symbol')}`"
        )
    lines.extend(["", "## Rejected Candidates"])
    for rejected in list(report.get("rejected_candidates") or []):
        if not isinstance(rejected, dict):
            continue
        candidate = dict(rejected.get("candidate") or {})
        reasons = ", ".join(str(reason) for reason in rejected.get("reasons") or [])
        lines.append(
            f"- strategy=`{candidate.get('strategy')}` symbol=`{candidate.get('symbol')}` "
            f"score=`{candidate.get('score')}` reasons=`{reasons}`"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "```json",
            json.dumps(report.get("safety") or {}, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def write_managed_paper_campaign_plan(report: dict[str, Any]) -> dict[str, str]:
    root = (data_dir() / "managed_paper_campaign_plans").resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_json = root / "managed_paper_campaign_plan.latest.json"
    dated_json = root / f"managed_paper_campaign_plan_{stamp}.json"
    latest_md = root / "managed_paper_campaign_plan.latest.md"
    dated_md = root / f"managed_paper_campaign_plan_{stamp}.md"
    json_text = json.dumps(report, indent=2, sort_keys=True, default=str)
    markdown_text = render_managed_paper_campaign_plan_markdown(report)
    for path, text in (
        (latest_json, json_text),
        (dated_json, json_text),
        (latest_md, markdown_text),
        (dated_md, markdown_text),
    ):
        atomic_write(path, text)
    return {
        "latest_json": str(latest_json),
        "dated_json": str(dated_json),
        "latest_markdown": str(latest_md),
        "dated_markdown": str(dated_md),
    }
