from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics import managed_paper_campaign_planner as planner
from services.execution.ohlcv_preflight import check_ohlcv_reachable
from services.os.app_paths import code_root, data_dir
from services.os.file_utils import atomic_write
from services.security.exchange_factory import make_exchange
from services.signals.candidate_engine import build_candidate_list
from services.signals.candidate_strategy_mapper import map_candidate_to_strategy
from services.signals.market_ranker import rank_market
from services.signals.trade_type_classifier import classify_trade_type
from services.signals.universe_loader import load_universe


REPORT_TYPE = "multi_symbol_paper_campaign_plan"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _fetch_symbol_data(ex: Any, *, symbol: str, timeframe: str, limit: int) -> dict[str, Any] | None:
    ohlcv = ex.fetch_ohlcv(symbol, timeframe=str(timeframe), limit=int(limit))
    ticker = ex.fetch_ticker(symbol)
    return {
        "symbol": str(symbol),
        "symbol_return_pct": float(ticker.get("percentage") or 0.0),
        "ohlcv": list(ohlcv or []),
    }


def fetch_candidate_market_data(
    *,
    venue: str,
    symbols: list[str],
    timeframe: str,
    limit: int,
) -> dict[str, Any]:
    fetched: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    ex = make_exchange(str(venue), {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        for symbol in symbols:
            symbol_s = str(symbol or "").strip()
            if not symbol_s:
                continue
            try:
                row = _fetch_symbol_data(ex, symbol=symbol_s, timeframe=str(timeframe), limit=int(limit))
                if row is not None:
                    fetched.append(row)
            except Exception as exc:
                errors.append(
                    {
                        "symbol": symbol_s,
                        "type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass
    return {
        "ok": bool(fetched),
        "venue": str(venue),
        "timeframe": str(timeframe),
        "limit": int(limit),
        "requested": len(symbols),
        "fetched": len(fetched),
        "rows": fetched,
        "errors": errors,
    }


def _candidate_summary(candidate: dict[str, Any], *, index: int) -> dict[str, Any]:
    return {
        "candidate_index": int(index),
        "symbol": str(candidate.get("symbol") or "").strip().upper(),
        "strategy": str(candidate.get("preferred_strategy") or "").strip(),
        "score": float(candidate.get("composite_score") or 0.0),
        "trade_type": str(candidate.get("trade_type") or ""),
        "mapping_reason": str(candidate.get("mapping_reason") or ""),
    }


def _ranked_market_diagnostics(symbols_data: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for index, row in enumerate(rank_market(symbols_data=symbols_data)[: max(0, int(limit))], start=1):
        trade_type = classify_trade_type(scores=row.get("scores") or {})
        mapped = map_candidate_to_strategy(
            {
                **row,
                "trade_type": trade_type.get("trade_type"),
                "trade_type_reason": trade_type.get("reason"),
            }
        )
        diagnostics.append(
            {
                "rank": index,
                "symbol": str(row.get("symbol") or "").strip().upper(),
                "composite_score": float(row.get("composite_score") or 0.0),
                "symbol_return_pct": row.get("symbol_return_pct"),
                "trade_type": trade_type.get("trade_type"),
                "trade_type_reason": trade_type.get("reason"),
                "preferred_strategy": mapped.get("preferred_strategy"),
                "mapping_reason": mapped.get("reason"),
                "scores": row.get("scores") or {},
            }
        )
    return diagnostics


def build_multi_symbol_paper_campaign_plan(
    *,
    repo_root: Path | None = None,
    laptop_manifest: Path = planner.DEFAULT_LAPTOP_MANIFEST,
    hetzner_manifest: Path = planner.DEFAULT_HETZNER_MANIFEST,
    symbols: list[str] | None = None,
    tiers: list[str] | None = None,
    venue: str = "coinbase",
    timeframe: str = "5m",
    ohlcv_limit: int = 200,
    min_score: float = 38.0,
    max_candidates: int = 5,
    proposal_host: str = "laptop",
    preflight_probe_limit: int = 50,
    preflight_attempts: int = 1,
    symbols_data: list[dict[str, Any]] | None = None,
    preflight_fn: Any = check_ohlcv_reachable,
) -> dict[str, Any]:
    root = (repo_root or code_root()).resolve()
    manifest_paths = {
        "laptop": Path(laptop_manifest),
        "hetzner": Path(hetzner_manifest),
    }
    explicit_symbols = [str(item).strip() for item in (symbols or []) if str(item).strip()]
    universe_symbols = explicit_symbols or load_universe(tiers=tiers)

    if symbols_data is None:
        scan = fetch_candidate_market_data(
            venue=str(venue),
            symbols=list(universe_symbols),
            timeframe=str(timeframe),
            limit=int(ohlcv_limit),
        )
        market_rows = list(scan.get("rows") or [])
    else:
        market_rows = [dict(row) for row in symbols_data if isinstance(row, dict)]
        scan = {
            "ok": bool(market_rows),
            "venue": str(venue),
            "timeframe": str(timeframe),
            "limit": int(ohlcv_limit),
            "requested": len(universe_symbols),
            "fetched": len(market_rows),
            "rows": market_rows,
            "errors": [],
            "source": "injected_symbols_data",
        }

    market_diagnostics = _ranked_market_diagnostics(market_rows, limit=max_candidates)
    candidates = build_candidate_list(
        symbols_data=market_rows,
        min_composite_score=float(min_score),
    )[: max(0, int(max_candidates))]

    existing, manifest_errors = planner._load_existing_campaigns(  # noqa: SLF001
        manifests=manifest_paths,
        root=root,
    )
    existing_names = {str(row.get("name") or "") for row in existing}
    existing_state_dirs = {str(row.get("state_dir") or "") for row in existing}
    existing_owners = {planner._owner_key(row) for row in existing}  # noqa: SLF001
    proposed_names: set[str] = set()
    proposed_state_dirs: set[str] = set()
    proposed_owners: set[tuple[str, str, str, str]] = set()

    proposals: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    preflights: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates, start=1):
        manifest_row = planner._manifest_row_for_candidate(  # noqa: SLF001
            candidate,
            proposal_host=str(proposal_host),
        )
        reasons = planner._candidate_rejection_reasons(  # noqa: SLF001
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
        preflight = preflight_fn(
            venue=str(manifest_row.get("venue") or venue),
            symbol=str(manifest_row.get("symbol") or ""),
            signal_source=str(manifest_row.get("signal_source") or f"public_ohlcv_{timeframe}"),
            probe_limit=int(preflight_probe_limit),
            attempts=int(preflight_attempts),
        )
        preflight = dict(preflight or {})
        preflights.append(preflight)
        if not bool(preflight.get("ok")):
            reasons.append(f"ohlcv_preflight_failed:{preflight.get('status') or preflight.get('reason') or 'unknown'}")

        row = {
            "candidate": _candidate_summary(candidate, index=index),
            "host_owner": str(proposal_host) if str(proposal_host) in manifest_paths else "neither",
            "target_manifest": _rel(manifest_paths[proposal_host], root)
            if str(proposal_host) in manifest_paths
            else "",
            "proposed_manifest_row": manifest_row,
            "ohlcv_preflight": preflight,
        }
        if reasons:
            rejected.append({**row, "status": "rejected", "reasons": reasons})
            continue
        proposals.append({**row, "status": "proposed", "reasons": []})
        proposed_names.add(str(manifest_row.get("name") or ""))
        proposed_state_dirs.add(str(manifest_row.get("state_dir") or ""))
        proposed_owners.add(planner._owner_key(manifest_row))  # noqa: SLF001

    status = "ok"
    if manifest_errors:
        status = "invalid_manifest"
    elif not bool(scan.get("ok")):
        status = "scan_failed"
    elif not candidates:
        status = "no_ranked_candidates"
    elif not proposals:
        status = "no_eligible_proposals"

    return {
        "generated_at": _now_iso(),
        "report_type": REPORT_TYPE,
        "status": status,
        "read_only": True,
        "parameters": {
            "venue": str(venue),
            "timeframe": str(timeframe),
            "ohlcv_limit": int(ohlcv_limit),
            "min_score": float(min_score),
            "max_candidates": int(max_candidates),
            "proposal_host": str(proposal_host),
            "preflight_probe_limit": int(preflight_probe_limit),
            "preflight_attempts": int(preflight_attempts),
            "tiers": list(tiers or []),
            "explicit_symbols": list(explicit_symbols),
        },
        "universe": {
            "symbols": list(universe_symbols),
            "symbol_count": len(universe_symbols),
            "source": "explicit_symbols" if explicit_symbols else "universe_loader",
        },
        "scan": {
            "ok": bool(scan.get("ok")),
            "requested": int(scan.get("requested") or 0),
            "fetched": int(scan.get("fetched") or 0),
            "errors": list(scan.get("errors") or []),
            "source": str(scan.get("source") or "exchange_fetch"),
        },
        "manifest_errors": manifest_errors,
        "existing_campaigns": existing,
        "market_diagnostics": market_diagnostics,
        "ranked_candidates": candidates,
        "preflight_summary": {
            "checked": len(preflights),
            "passed": sum(1 for row in preflights if bool(row.get("ok"))),
            "failed": sum(1 for row in preflights if not bool(row.get("ok"))),
        },
        "proposals": proposals,
        "rejected_candidates": rejected,
        "summary": {
            "existing_campaigns": len(existing),
            "symbols_requested": len(universe_symbols),
            "symbols_fetched": int(scan.get("fetched") or 0),
            "ranked_candidate_count": len(candidates),
            "proposal_count": len(proposals),
            "rejected_count": len(rejected),
            "manifest_error_count": len(manifest_errors),
        },
        "safety": {
            "paper_only": True,
            "read_only": True,
            "campaigns_started": False,
            "campaigns_stopped": False,
            "restore_invoked": False,
            "manifest_files_written": False,
            "active_manifest_mutated": False,
            "state_dirs_created": False,
            "orders_routed": False,
            "promotion_gate_mutated": False,
            "live_trading_touched": False,
        },
    }


def render_multi_symbol_paper_campaign_plan_markdown(report: dict[str, Any]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# Multi-Symbol Paper Campaign Plan",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Status: `{report.get('status')}`",
        f"- Paper only: `{bool((report.get('safety') or {}).get('paper_only'))}`",
        f"- Symbols requested: `{summary.get('symbols_requested')}`",
        f"- Symbols fetched: `{summary.get('symbols_fetched')}`",
        f"- Ranked candidates: `{summary.get('ranked_candidate_count')}`",
        f"- Proposals: `{summary.get('proposal_count')}`",
        f"- Rejected: `{summary.get('rejected_count')}`",
        "",
        "## Market Diagnostics",
    ]
    for diagnostic in list(report.get("market_diagnostics") or []):
        lines.append(
            f"- #{diagnostic.get('rank')} symbol=`{diagnostic.get('symbol')}` "
            f"score=`{diagnostic.get('composite_score')}` trade_type=`{diagnostic.get('trade_type')}` "
            f"strategy=`{diagnostic.get('preferred_strategy')}` reason=`{diagnostic.get('trade_type_reason')}`"
        )
    lines.extend(
        [
            "",
            "## Proposed Campaign Rows",
        ]
    )
    for proposal in list(report.get("proposals") or []):
        campaign = dict((proposal or {}).get("proposed_manifest_row") or {})
        preflight = dict((proposal or {}).get("ohlcv_preflight") or {})
        lines.append(
            f"- `{campaign.get('name')}` strategy=`{campaign.get('strategy')}` "
            f"symbol=`{campaign.get('symbol')}` source=`{campaign.get('signal_source')}` "
            f"state_dir=`{campaign.get('state_dir')}` preflight=`{preflight.get('status')}`"
        )
    lines.extend(["", "## Rejected"])
    for rejected in list(report.get("rejected_candidates") or []):
        candidate = dict((rejected or {}).get("candidate") or {})
        lines.append(
            f"- symbol=`{candidate.get('symbol')}` strategy=`{candidate.get('strategy')}` "
            f"score=`{candidate.get('score')}` reasons=`{', '.join(rejected.get('reasons') or [])}`"
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


def write_multi_symbol_paper_campaign_plan(report: dict[str, Any]) -> dict[str, str]:
    root = (data_dir() / "multi_symbol_paper_campaign_plans").resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_json = root / "multi_symbol_paper_campaign_plan.latest.json"
    dated_json = root / f"multi_symbol_paper_campaign_plan_{stamp}.json"
    latest_md = root / "multi_symbol_paper_campaign_plan.latest.md"
    dated_md = root / f"multi_symbol_paper_campaign_plan_{stamp}.md"
    json_text = json.dumps(report, indent=2, sort_keys=True, default=str)
    markdown_text = render_multi_symbol_paper_campaign_plan_markdown(report)
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
