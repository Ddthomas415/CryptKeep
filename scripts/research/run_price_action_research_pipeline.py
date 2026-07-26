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
DEFAULT_OUTPUT_ROOT = REPO_ROOT / ".cbp_state" / "data" / "research" / "price_action_pipeline"


STEPS: tuple[tuple[str, str, str], ...] = (
    ("context_labels", "scripts/research/run_price_action_context_labels.py", "context_labels.json"),
    ("forward_returns", "scripts/research/run_price_action_forward_returns.py", "forward_returns.json"),
    ("window_stability", "scripts/research/run_price_action_window_stability.py", "window_stability.json"),
    ("candidate_triage", "scripts/research/run_price_action_candidate_triage.py", "candidate_triage.json"),
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the accepted price-action research reports as one read-only "
            "archive-backed pipeline. The pipeline writes research artifacts "
            "only and does not change strategy config, campaigns, gates, "
            "promotion evidence, ingestion, routing, or execution."
        )
    )
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--since", default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--window-bars", type=int, default=120)
    parser.add_argument("--step-bars", type=int, default=None)
    parser.add_argument("--min-windows", type=int, default=2)
    parser.add_argument("--min-labeled-rows", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--min-sample-size", type=int, default=10)
    parser.add_argument("--min-avg-delta-pct", type=float, default=0.0)
    parser.add_argument("--min-outperform-ratio", type=float, default=0.60)
    parser.add_argument("--max-underperform-ratio", type=float, default=0.40)
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


def _base_command(args: argparse.Namespace, script: str, output: Path) -> list[str]:
    cmd = [
        sys.executable,
        script,
        "--venue",
        str(args.venue),
        "--symbol",
        str(args.symbol),
        "--timeframe",
        str(args.timeframe),
        "--limit",
        str(int(args.limit)),
        "--output",
        str(output),
        "--fail-if-not-ok",
    ]
    _add_optional(cmd, "--since", args.since)
    _add_optional(cmd, "--archive-db", args.archive_db)
    return cmd


def _step_command(args: argparse.Namespace, script: str, output: Path) -> list[str]:
    cmd = _base_command(args, script, output)
    if script.endswith("run_price_action_context_labels.py"):
        return cmd
    cmd.extend(
        [
            "--horizon-bars",
            str(int(args.horizon_bars)),
            "--min-labeled-rows",
            str(int(args.min_labeled_rows)),
            "--fee-bps",
            str(float(args.fee_bps)),
            "--slippage-bps",
            str(float(args.slippage_bps)),
        ]
    )
    if script.endswith(("run_price_action_window_stability.py", "run_price_action_candidate_triage.py")):
        cmd.extend(
            [
                "--window-bars",
                str(int(args.window_bars)),
                "--min-windows",
                str(int(args.min_windows)),
            ]
        )
        _add_optional(cmd, "--step-bars", args.step_bars)
    if script.endswith("run_price_action_candidate_triage.py"):
        cmd.extend(
            [
                "--min-sample-size",
                str(int(args.min_sample_size)),
                "--min-avg-delta-pct",
                str(float(args.min_avg_delta_pct)),
                "--min-outperform-ratio",
                str(float(args.min_outperform_ratio)),
                "--max-underperform-ratio",
                str(float(args.max_underperform_ratio)),
            ]
        )
    return cmd


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def _load_json(path: Path, fallback_text: str) -> dict[str, Any] | None:
    candidates = []
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


def _summarize_step(
    name: str,
    cmd: list[str],
    output: Path,
    completed: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    payload = _load_json(output, completed.stdout)
    return {
        "name": name,
        "script": cmd[1] if len(cmd) > 1 else "",
        "returncode": int(completed.returncode),
        "ok": bool(payload.get("ok")) if isinstance(payload, dict) else False,
        "report_type": payload.get("report_type") if isinstance(payload, dict) else None,
        "output": str(output),
        "output_sha256": _sha256(output),
        "stdout_preview": completed.stdout[-2000:],
        "stderr_preview": completed.stderr[-2000:],
    }


def _summary(args: argparse.Namespace, output_dir: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    ok = bool(steps) and all(bool(step.get("ok")) and int(step.get("returncode") or 0) == 0 for step in steps)
    return {
        "schema_version": 1,
        "report_type": "price_action_research_pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "read_only": True,
        "not_strategy_config": True,
        "not_campaign_evidence": True,
        "not_promotion_evidence": True,
        "not_execution_input": True,
        "inputs": {
            "venue": str(args.venue),
            "symbol": str(args.symbol),
            "timeframe": str(args.timeframe),
            "limit": int(args.limit),
            "since": args.since,
            "archive_db": str(args.archive_db) if args.archive_db is not None else None,
            "horizon_bars": int(args.horizon_bars),
            "window_bars": int(args.window_bars),
            "step_bars": int(args.step_bars) if args.step_bars is not None else None,
            "min_windows": int(args.min_windows),
            "min_labeled_rows": int(args.min_labeled_rows),
            "fee_bps": float(args.fee_bps),
            "slippage_bps": float(args.slippage_bps),
        },
        "output_dir": str(output_dir),
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_dir = _output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, Any]] = []
    for name, script, filename in STEPS:
        output = output_dir / filename
        cmd = _step_command(args, script, output)
        completed = _run_command(cmd)
        step = _summarize_step(name, cmd, output, completed)
        steps.append(step)
        if completed.returncode != 0 or not bool(step.get("ok")):
            break

    summary = _summary(args, output_dir, steps)
    summary_path = output_dir / "pipeline_summary.json"
    summary["summary_path"] = str(summary_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if bool(summary.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
