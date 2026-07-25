#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / ".cbp_state" / "data" / "research" / "funding_threshold_pipeline"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run accepted funding_extreme threshold research reports as one "
            "read-only pipeline. The pipeline writes research artifacts only "
            "and does not change collectors, strategy config, campaigns, "
            "gates, promotion evidence, routing, or execution."
        )
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--edge-db", type=Path, default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--context-source", default="live_public")
    parser.add_argument("--context-venue", default="okx")
    parser.add_argument("--context-symbol", default="BTC/USDT:USDT")
    parser.add_argument("--price-venue", default="okx")
    parser.add_argument("--price-symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--funding-limit", type=int, default=500)
    parser.add_argument("--ohlcv-limit", type=int, default=500)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--min-joined-rows", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--long-thresholds-pct", default="0.005,0.01,0.02,0.05")
    parser.add_argument("--short-thresholds-pct", default="-0.005,-0.01,-0.02,-0.05")
    parser.add_argument("--window-rows", type=int, default=100)
    parser.add_argument("--step-rows", type=int, default=None)
    parser.add_argument("--min-windows", type=int, default=2)
    parser.add_argument("--min-input-rows", type=int, default=100)
    parser.add_argument("--min-actionable-rows", type=int, default=5)
    parser.add_argument("--min-actionable-share", type=float, default=0.01)
    parser.add_argument("--min-positive-ratio", type=float, default=0.50)
    parser.add_argument("--min-avg-net-forward-return-pct", type=float, default=0.0)
    parser.add_argument("--min-window-count", type=int, default=2)
    parser.add_argument("--min-actionable-window-ratio", type=float, default=0.50)
    parser.add_argument("--min-positive-actionable-window-ratio", type=float, default=0.50)
    parser.add_argument("--min-worst-window-avg-net-forward-return-pct", type=float, default=0.0)
    return parser.parse_args(argv)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir is not None:
        return args.output_dir
    return DEFAULT_OUTPUT_ROOT / _timestamp()


def _add_optional(cmd: list[str], flag: str, value: Any) -> None:
    if value is not None:
        cmd.extend([flag, str(value)])


def _price_join_cmd(args: argparse.Namespace, output: Path) -> list[str]:
    cmd = [
        sys.executable,
        "scripts/research/run_funding_context_price_join.py",
        "--context-source",
        str(args.context_source),
        "--context-venue",
        str(args.context_venue),
        "--context-symbol",
        str(args.context_symbol),
        "--price-venue",
        str(args.price_venue),
        "--price-symbol",
        str(args.price_symbol),
        "--timeframe",
        str(args.timeframe),
        "--funding-limit",
        str(int(args.funding_limit)),
        "--ohlcv-limit",
        str(int(args.ohlcv_limit)),
        "--horizon-bars",
        str(int(args.horizon_bars)),
        "--min-joined-rows",
        str(int(args.min_joined_rows)),
        "--fee-bps",
        str(float(args.fee_bps)),
        "--slippage-bps",
        str(float(args.slippage_bps)),
        "--output",
        str(output),
        "--fail-if-not-ok",
    ]
    _add_optional(cmd, "--config", args.config)
    _add_optional(cmd, "--edge-db", args.edge_db)
    _add_optional(cmd, "--archive-db", args.archive_db)
    return cmd


def _sensitivity_cmd(args: argparse.Namespace, input_path: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/research/run_funding_threshold_sensitivity.py",
        "--input",
        str(input_path),
        "--output",
        str(output),
        "--long-thresholds-pct",
        str(args.long_thresholds_pct),
        "--short-thresholds-pct",
        str(args.short_thresholds_pct),
        "--fee-bps",
        str(float(args.fee_bps)),
        "--slippage-bps",
        str(float(args.slippage_bps)),
        "--fail-if-not-ok",
    ]


def _candidate_triage_cmd(args: argparse.Namespace, input_path: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/research/run_funding_threshold_candidate_triage.py",
        "--input",
        str(input_path),
        "--output",
        str(output),
        "--min-input-rows",
        str(int(args.min_input_rows)),
        "--min-actionable-rows",
        str(int(args.min_actionable_rows)),
        "--min-actionable-share",
        str(float(args.min_actionable_share)),
        "--min-positive-ratio",
        str(float(args.min_positive_ratio)),
        "--min-avg-net-forward-return-pct",
        str(float(args.min_avg_net_forward_return_pct)),
        "--fail-if-not-ok",
    ]


def _window_stability_cmd(args: argparse.Namespace, input_path: Path, output: Path) -> list[str]:
    cmd = [
        sys.executable,
        "scripts/research/run_funding_threshold_window_stability.py",
        "--input",
        str(input_path),
        "--output",
        str(output),
        "--long-thresholds-pct",
        str(args.long_thresholds_pct),
        "--short-thresholds-pct",
        str(args.short_thresholds_pct),
        "--window-rows",
        str(int(args.window_rows)),
        "--min-windows",
        str(int(args.min_windows)),
        "--fail-if-not-ok",
    ]
    _add_optional(cmd, "--step-rows", args.step_rows)
    return cmd


def _stability_triage_cmd(args: argparse.Namespace, input_path: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/research/run_funding_threshold_stability_triage.py",
        "--input",
        str(input_path),
        "--output",
        str(output),
        "--min-window-count",
        str(int(args.min_window_count)),
        "--min-actionable-window-ratio",
        str(float(args.min_actionable_window_ratio)),
        "--min-positive-actionable-window-ratio",
        str(float(args.min_positive_actionable_window_ratio)),
        "--min-avg-net-forward-return-pct",
        str(float(args.min_avg_net_forward_return_pct)),
        "--min-worst-window-avg-net-forward-return-pct",
        str(float(args.min_worst_window_avg_net_forward_return_pct)),
        "--fail-if-not-ok",
    ]


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def _load_json(path: Path, fallback_text: str) -> dict[str, Any] | None:
    candidates: list[str] = []
    if path.exists():
        candidates.append(path.read_text(encoding="utf-8"))
    if fallback_text.strip():
        candidates.append(fallback_text)
    for text in candidates:
        try:
            payload = json.loads(text)
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _step(name: str, cmd: list[str], output: Path) -> dict[str, Any]:
    completed = _run_command(cmd)
    payload = _load_json(output, completed.stdout)
    return {
        "name": name,
        "script": cmd[1] if len(cmd) > 1 else "",
        "returncode": int(completed.returncode),
        "ok": bool(payload.get("ok")) if isinstance(payload, dict) else False,
        "artifact_type": payload.get("artifact_type") if isinstance(payload, dict) else None,
        "output": str(output),
        "output_sha256": _sha256(output),
        "stdout_preview": completed.stdout[-2000:],
        "stderr_preview": completed.stderr[-2000:],
    }


def _summary(args: argparse.Namespace, output_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    ok = bool(steps) and all(bool(step.get("ok")) and int(step.get("returncode") or 0) == 0 for step in steps)
    return {
        "schema_version": 1,
        "report_type": "funding_threshold_research_pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "read_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "inputs": {
            "context_source": str(args.context_source),
            "context_venue": str(args.context_venue),
            "context_symbol": str(args.context_symbol),
            "price_venue": str(args.price_venue),
            "price_symbol": str(args.price_symbol),
            "timeframe": str(args.timeframe),
            "funding_limit": int(args.funding_limit),
            "ohlcv_limit": int(args.ohlcv_limit),
            "horizon_bars": int(args.horizon_bars),
            "fee_bps": float(args.fee_bps),
            "slippage_bps": float(args.slippage_bps),
            "long_thresholds_pct": str(args.long_thresholds_pct),
            "short_thresholds_pct": str(args.short_thresholds_pct),
        },
        "output_dir": str(output_dir),
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_dir = _output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    price_join = output_dir / "funding_context_price_join.json"
    sensitivity = output_dir / "funding_threshold_sensitivity.json"
    candidate_triage = output_dir / "funding_threshold_candidate_triage.json"
    window_stability = output_dir / "funding_threshold_window_stability.json"
    stability_triage = output_dir / "funding_threshold_stability_triage.json"

    planned = [
        ("price_join", _price_join_cmd(args, price_join), price_join),
        ("threshold_sensitivity", _sensitivity_cmd(args, price_join, sensitivity), sensitivity),
        ("candidate_triage", _candidate_triage_cmd(args, sensitivity, candidate_triage), candidate_triage),
        ("window_stability", _window_stability_cmd(args, price_join, window_stability), window_stability),
        ("stability_triage", _stability_triage_cmd(args, window_stability, stability_triage), stability_triage),
    ]

    steps: list[dict[str, Any]] = []
    for name, cmd, output in planned:
        step = _step(name, cmd, output)
        steps.append(step)
        if int(step.get("returncode") or 0) != 0 or not bool(step.get("ok")):
            break

    summary = _summary(args, output_dir, steps)
    summary_path = output_dir / "pipeline_summary.json"
    summary["summary_path"] = str(summary_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if bool(summary.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
