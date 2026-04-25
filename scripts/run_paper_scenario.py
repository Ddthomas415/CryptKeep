"""
scripts/run_paper_scenario.py

Paper-runtime harness entry point.
Contract: v1.3 — sections 1, 3, 5, 12, 13, 17, 18, 20, 21 blocking.

Single supported execution path:
    run_paper_scenario.py
        -> run_with_determinism_guard()
            -> RuntimeEntrypoint.run(finalizer=...)
                -> FinalizationController.finalize_and_exit()
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Exit codes — section 18
# ---------------------------------------------------------------------------

EXIT_SUCCESS          = 0
EXIT_STATE_INVALID    = 10
EXIT_ENV_INVALID      = 11
EXIT_SCENARIO_INVALID = 12
EXIT_INVARIANT        = 13
EXIT_EXECUTION        = 14
EXIT_PROMOTION        = 15
EXIT_MANIFEST_INVALID = 16

# ---------------------------------------------------------------------------
# Failure categories — section 16
# ---------------------------------------------------------------------------

class FailureClassifier:
    """Single authority for failure_category values. Section 16."""

    _MAP: dict[type, str] = {}  # populated below

    @classmethod
    def classify(cls, exc: Optional[BaseException]) -> Optional[str]:
        if exc is None:
            return None
        for exc_type, category in cls._MAP.items():
            if isinstance(exc, exc_type):
                return category
        return "EXECUTION_FAILURE"

    @classmethod
    def exit_code(cls, exc: Optional[BaseException]) -> int:
        if exc is None:
            return EXIT_SUCCESS
        for exc_type, code in _EXIT_CODE_MAP.items():
            if isinstance(exc, exc_type):
                return code
        return EXIT_EXECUTION


class StateInvalidError(RuntimeError):
    pass


class EnvInvalidError(RuntimeError):
    pass


class ScenarioInvalidError(RuntimeError):
    pass


class InvariantViolationError(RuntimeError):
    pass


class PromotionGateError(RuntimeError):
    pass


class ManifestInvalidError(RuntimeError):
    pass


FailureClassifier._MAP = {
    StateInvalidError:    "STATE_INVALID",
    EnvInvalidError:      "ENV_INVALID",
    ScenarioInvalidError: "SCENARIO_INVALID",
    InvariantViolationError: "INVARIANT_VIOLATION",
    PromotionGateError:   "PROMOTION_GATE_FAIL",
    ManifestInvalidError: "MANIFEST_INVALID",
}

_EXIT_CODE_MAP: dict[type, int] = {
    StateInvalidError:       EXIT_STATE_INVALID,
    EnvInvalidError:         EXIT_ENV_INVALID,
    ScenarioInvalidError:    EXIT_SCENARIO_INVALID,
    InvariantViolationError: EXIT_INVARIANT,
    PromotionGateError:      EXIT_PROMOTION,
    ManifestInvalidError:    EXIT_MANIFEST_INVALID,
}

# ---------------------------------------------------------------------------
# Environment construction — section 5
# ---------------------------------------------------------------------------

# Keys that may be passed through from the parent environment, opt-in only.
# Keep this list minimal. Every addition is a potential ambient-state leak.
_ALLOWLISTED_PASSTHROUGH = frozenset({
    "PATH",
    "PYTHONPATH",
})


def _build_allowlisted_env(
    *,
    state_root: Path,
    fixed_time: str,
    fixed_seed: int,
    include_path: bool = True,
) -> dict[str, str]:
    """
    Construct the subprocess/runtime environment from scratch.
    Never copies os.environ. Only explicitly allowlisted keys are included.
    Section 5: all subprocesses MUST use this env; no ambient inheritance.
    """
    env: dict[str, str] = {}

    # Harness-injected values — always set, not from os.environ
    env["CBP_STATE_ROOT"]  = str(state_root)
    env["CBP_FIXED_TIME"]  = fixed_time
    env["CBP_FIXED_SEED"]  = str(fixed_seed)

    # Opt-in passthrough: only keys in _ALLOWLISTED_PASSTHROUGH are eligible.
    # PATH is gated additionally by include_path to support test isolation.
    for key in _ALLOWLISTED_PASSTHROUGH:
        if key == "PATH" and not include_path:
            continue
        val = os.environ.get(key, "")
        if val:
            env[key] = val

    return env

# ---------------------------------------------------------------------------
# State-root layout — section 4
# ---------------------------------------------------------------------------

@dataclass
class StateRoot:
    root: Path
    strategy_id: str

    @property
    def config_path(self) -> Path:
        return self.root / "runtime" / "config" / "user.yaml"

    @property
    def scenario_dir(self) -> Path:
        return self.root / "scenario"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "data" / "evidence" / self.strategy_id

    @property
    def sqlite_dir(self) -> Path:
        return self.root / "data" / "sqlite"

    @property
    def manifest_path(self) -> Path:
        return self.evidence_dir / "manifest.json"

    @property
    def finalized_lock(self) -> Path:
        return self.root / ".finalized.lock"

    def initialize(self) -> None:
        """Create all required directories. Raises StateInvalidError if root exists."""
        if self.root.exists():
            raise StateInvalidError(
                f"state_root already exists: {self.root} — "
                "cross-run reuse is forbidden (section 4)"
            )
        for d in (
            self.config_path.parent,
            self.scenario_dir,
            self.logs_dir,
            self.evidence_dir,
            self.sqlite_dir,
        ):
            d.mkdir(parents=True, exist_ok=False)

# ---------------------------------------------------------------------------
# Finalization controller — sections 13, 14, 15, 17
# ---------------------------------------------------------------------------

@dataclass
class FinalizationController:
    """
    Single final-state authority. Section 13.
    Only this component may write manifest.json and emit the process exit code.
    """
    state_root_obj: StateRoot
    strategy_id: str
    scenario_name: str
    stage: str
    run_started_at: str

    _frozen: bool = field(default=False, init=False)
    _finalized: bool = field(default=False, init=False)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def finalize_and_exit(self, exc: Optional[BaseException] = None) -> None:
        """
        Only path that may emit a process exit code. Sections 12, 13, 18.
        Writes manifest on success and failure. Section 17.
        """
        if self._finalized:
            # Double-finalization guard — section 15
            sys.exit(EXIT_MANIFEST_INVALID)

        self._frozen = True
        self._finalized = True

        exit_code = FailureClassifier.exit_code(exc)
        failure_category = FailureClassifier.classify(exc)
        final_status = "SUCCESS" if exc is None else "FAILURE"

        run_finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        manifest = self._build_manifest(
            final_status=final_status,
            failure_category=failure_category,
            run_finished_at=run_finished_at,
            exc=exc,
        )

        # Fix 1: invariant failure must not exit 0. Section 10 / 18.
        # If exc is None (no exception) but artifacts fail invariants, escalate.
        if exit_code == EXIT_SUCCESS and not manifest["invariants_passed"]:
            exit_code = EXIT_INVARIANT
            manifest["final_status"] = "FAILURE"
            manifest["failure_category"] = "INVARIANT_VIOLATION"

        try:
            self._write_manifest(manifest)
            self._write_lock()
        except Exception as write_exc:
            # Manifest write failure — section 17
            sys.stderr.write(
                f"MANIFEST_INVALID: failed to write manifest: {write_exc}\n"
            )
            sys.exit(EXIT_MANIFEST_INVALID)

        sys.exit(exit_code)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_manifest(
        self,
        *,
        final_status: str,
        failure_category: Optional[str],
        run_finished_at: str,
        exc: Optional[BaseException],
    ) -> dict:
        """
        Artifact-derived fields are computed from persisted artifacts.
        Finalizer metadata fields come from explicit runner inputs. Section 17.
        """
        sr = self.state_root_obj

        # Artifact-derived fields — section 17
        signal_count  = self._count_jsonl(sr.evidence_dir / "signal.jsonl")
        order_count   = self._count_jsonl(sr.evidence_dir / "order.jsonl")
        fill_count    = self._count_jsonl(sr.evidence_dir / "fill.jsonl")
        session_count = self._count_jsonl(sr.evidence_dir / "session.jsonl")

        signal_ids, order_signal_refs, fill_order_refs = self._read_refs(sr)

        round_trip_count   = self._count_round_trips(sr)
        invariants_passed  = self._check_invariants(
            signal_count, order_count, fill_count, session_count, round_trip_count,
            order_signal_refs, fill_order_refs, signal_ids, sr,
        )
        promotion_gates_passed, promotion_gate_skipped_reason = (
            self._evaluate_promotion_gates(sr, final_status)
        )

        return {
            # Finalizer metadata — section 17
            "manifest_schema_version": "1.3",
            "strategy_id":             self.strategy_id,
            "scenario_name":           self.scenario_name,
            "stage":                   self.stage,
            "run_started_at":          self.run_started_at,
            "run_finished_at":         run_finished_at,
            "final_status":            final_status,
            "failure_category":        failure_category,
            "promotion_gate_skipped_reason": promotion_gate_skipped_reason,
            # Artifact-derived fields — section 17
            "signal_count":            signal_count,
            "order_count":             order_count,
            "fill_count":              fill_count,
            "session_count":           session_count,
            "round_trip_count":        round_trip_count,
            "invariants_passed":       invariants_passed,
            "promotion_gates_passed":  promotion_gates_passed,
            # Structural reference fields — for CI integrity checks
            "signal_ids":              signal_ids,
            "order_signal_refs":       order_signal_refs,
            "fill_order_refs":         fill_order_refs,
        }

    def _write_manifest(self, manifest: dict) -> None:
        path = self.state_root_obj.manifest_path
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, indent=2))
        tmp.replace(path)

    def _write_lock(self) -> None:
        self.state_root_obj.finalized_lock.write_text(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

    @staticmethod
    def _count_jsonl(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return sum(
                1 for line in path.read_text().splitlines()
                if line.strip()
            )
        except Exception:
            return 0

    @staticmethod
    def _read_refs(sr: StateRoot) -> tuple[list[str], dict[str, str], dict[str, str]]:
        """
        Read referential-integrity fields from artifacts.
        Returns (signal_ids, order_signal_refs, fill_order_refs).
        Used by CI for structural reference reconciliation.
        """
        signal_ids: list[str]        = []
        order_signal_refs: dict[str, str] = {}
        fill_order_refs: dict[str, str]   = {}

        for line in _iter_jsonl(sr.evidence_dir / "signal.jsonl"):
            sid = line.get("signal_id")
            if sid:
                signal_ids.append(str(sid))

        for line in _iter_jsonl(sr.evidence_dir / "order.jsonl"):
            oid = line.get("order_id")
            sid = line.get("signal_id")
            if oid and sid:
                order_signal_refs[str(oid)] = str(sid)

        for line in _iter_jsonl(sr.evidence_dir / "fill.jsonl"):
            fid = line.get("fill_id")
            oid = line.get("order_id")
            if fid and oid:
                fill_order_refs[str(fid)] = str(oid)

        return signal_ids, order_signal_refs, fill_order_refs

    @staticmethod
    def _count_round_trips(sr: StateRoot) -> int:
        count = 0
        for line in _iter_jsonl(sr.evidence_dir / "session.jsonl"):
            count += int(line.get("round_trip_count", 0))
        return count

    @staticmethod
    def _check_invariants(
        signal_count: int,
        order_count: int,
        fill_count: int,
        session_count: int,
        round_trip_count: int,
        order_signal_refs: dict[str, str],
        fill_order_refs: dict[str, str],
        signal_ids: list[str],
        sr: "StateRoot",
    ) -> bool:
        """Section 10 invariants. Returns False rather than raising — caller decides."""
        if not all([signal_count >= 1, order_count >= 1,
                    fill_count >= 1, session_count >= 1]):
            return False
        if round_trip_count < 1:
            return False
        known_signals = set(signal_ids)
        if any(v not in known_signals for v in order_signal_refs.values()):
            return False
        known_orders = set(order_signal_refs.keys())
        if any(v not in known_orders for v in fill_order_refs.values()):
            return False
        # Section 10: kill_switch_tested must be present in at least one session record
        kill_switch_found = False
        for line in _iter_jsonl(sr.evidence_dir / "session.jsonl"):
            if line.get("kill_switch_tested") is not None:
                kill_switch_found = True
                break
        if not kill_switch_found:
            return False
        return True

    @staticmethod
    def _evaluate_promotion_gates(
        sr: StateRoot,
        final_status: str,
    ) -> tuple[bool, Optional[str]]:
        """Section 11: promotion gate result. Placeholder for check_promotion_gates.py."""
        if final_status != "SUCCESS":
            return False, "upstream_execution_failure"
        # v1: gate script invocation is a stub — wired to check_promotion_gates.py in v1.1
        return False, "promotion_gate_check_not_yet_wired"


# ---------------------------------------------------------------------------
# Runtime entrypoint — section 1
# ---------------------------------------------------------------------------

@dataclass
class RuntimeEntrypoint:
    """
    Executes the paper scenario.
    Must not access os.environ. Receives env as an explicit dependency.
    Section 1, section 5.
    """
    env: dict[str, str]
    state_root_obj: StateRoot
    scenario_path: Path
    config_template: Path
    strategy_id: str
    stage: str

    def run(self, *, finalizer: FinalizationController) -> None:
        """
        Execute the paper scenario. All exceptions propagate to the caller
        (run_with_determinism_guard) which routes them to finalizer.finalize_and_exit.
        Section 12: no intermediate sys.exit calls.
        """
        self._materialize_config()
        self._copy_scenario()
        self._execute_scenario(finalizer=finalizer)

    def _materialize_config(self) -> None:
        import shutil
        dest = self.state_root_obj.config_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.config_template, dest)

    def _copy_scenario(self) -> None:
        import shutil
        dest = self.state_root_obj.scenario_dir / self.scenario_path.name
        shutil.copy2(self.scenario_path, dest)

    def _execute_scenario(self, *, finalizer: FinalizationController) -> None:
        """
        Placeholder: invoke the paper runner subprocess.
        Section 5: subprocess MUST receive env= explicitly — no ambient inheritance.
        """
        # v1 stub — replace with actual subprocess invocation when paper runner exists.
        # Pattern that MUST be followed for all subprocess calls:
        #
        #   import subprocess
        #   result = subprocess.run(
        #       [sys.executable, "services/execution/paper_runner.py", ...],
        #       env=self.env,          # explicit — never omit
        #       cwd=str(Path.cwd()),
        #       check=False,
        #   )
        #   if result.returncode != 0:
        #       raise InvariantViolationError(
        #           f"paper runner exited {result.returncode}"
        #       )
        pass


# ---------------------------------------------------------------------------
# Guard — section 1, 5, 12, 13
# ---------------------------------------------------------------------------

def run_with_determinism_guard(
    *,
    state_root: Path,
    scenario: Path,
    config_template: Path,
    strategy_id: str,
    stage: str,
    fixed_time: str,
    fixed_seed: int,
) -> None:
    """
    Only supported execution entry point. Sections 1, 5, 12, 13.

    Owns:
    - environment construction (allowlist only, no os.environ.copy)
    - FinalizationController construction (before run())
    - exception routing to finalize_and_exit
    """
    run_started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Section 5: environment built from scratch — never from os.environ.copy()
    env = _build_allowlisted_env(
        state_root=state_root,
        fixed_time=fixed_time,
        fixed_seed=fixed_seed,
    )

    sr = StateRoot(root=state_root, strategy_id=strategy_id)

    try:
        sr.initialize()
    except StateInvalidError:
        raise
    except Exception as exc:
        raise StateInvalidError(f"state_root initialization failed: {exc}") from exc

    # Section 13: FinalizationController constructed at guard boundary, before run()
    finalizer = FinalizationController(
        state_root_obj=sr,
        strategy_id=strategy_id,
        scenario_name=scenario.stem,
        stage=stage,
        run_started_at=run_started_at,
    )

    entrypoint = RuntimeEntrypoint(
        env=env,
        state_root_obj=sr,
        scenario_path=scenario,
        config_template=config_template,
        strategy_id=strategy_id,
        stage=stage,
    )

    try:
        entrypoint.run(finalizer=finalizer)
        finalizer.finalize_and_exit(exc=None)
    except SystemExit:
        raise  # finalize_and_exit already called sys.exit — do not intercept
    except BaseException as exc:
        finalizer.finalize_and_exit(exc=exc)


# ---------------------------------------------------------------------------
# CLI — section 3
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run_paper_scenario.py",
        description="Paper-runtime harness entry point (contract v1.3)",
    )
    p.add_argument("--state-root",      required=True, type=Path)
    p.add_argument("--scenario",        required=True, type=Path)
    p.add_argument("--config-template", required=True, type=Path)
    p.add_argument("--strategy",        required=True)
    p.add_argument("--stage",           required=True)
    p.add_argument("--fixed-time",      default=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    p.add_argument("--fixed-seed",      type=int, default=42)
    return p.parse_args(argv)


def _validate_cli(args: argparse.Namespace) -> None:
    """Section 3: all args required and must be valid before execution begins."""
    if not args.scenario.exists():
        raise ScenarioInvalidError(f"--scenario does not exist: {args.scenario}")
    if not args.scenario.is_file():
        raise ScenarioInvalidError(f"--scenario is not a file: {args.scenario}")
    if not args.config_template.exists():
        raise StateInvalidError(f"--config-template does not exist: {args.config_template}")
    if not args.strategy.strip():
        raise StateInvalidError("--strategy must not be empty")
    if args.stage not in {"paper", "live", "shadow"}:
        raise StateInvalidError(f"--stage must be paper|live|shadow, got: {args.stage!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> None:
    raw_argv = argv if argv is not None else sys.argv[1:]

    # Arg errors before guard is active: emit to stderr and exit STATE_INVALID
    try:
        args = _parse_args(raw_argv)
        _validate_cli(args)
    except ScenarioInvalidError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        sys.exit(EXIT_SCENARIO_INVALID)
    except StateInvalidError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        sys.exit(EXIT_STATE_INVALID)
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write(f"ERROR (arg parse): {exc}\n")
        sys.exit(EXIT_STATE_INVALID)

    # All subsequent failures route through the guard -> finalizer -> sys.exit.
    # StateInvalidError raised during state-root initialization fires before the
    # finalizer is constructed; catch it here and emit the correct exit code.
    try:
        run_with_determinism_guard(
            state_root=args.state_root,
            scenario=args.scenario,
            config_template=args.config_template,
            strategy_id=args.strategy,
            stage=args.stage,
            fixed_time=args.fixed_time,
            fixed_seed=args.fixed_seed,
        )
    except StateInvalidError as exc:
        sys.stderr.write(f"ERROR (state): {exc}\n")
        sys.exit(EXIT_STATE_INVALID)
    except SystemExit:
        raise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_jsonl(path: Path):
    """Yield parsed lines from a JSONL file. Skips blank and unparseable lines."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
