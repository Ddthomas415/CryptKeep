"""services/control/runtime_identity.py

Runtime identity stamp and enforcement for strategy paper runs.

Every strategy-specific entrypoint must declare and verify its full identity
before launching child processes. Evidence from a mismatched run is invalid.

Identity fields: strategy_id, preset, symbol, venue, stage, commit
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.control.deployment_stage import get_current_stage
from services.logging.app_logger import get_logger

_LOG = get_logger("runtime_identity")


class RuntimeIdentityError(RuntimeError):
    """Raised when declared identity does not match runtime state."""


def _get_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parents[2],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


@dataclass
class RuntimeIdentity:
    """Full identity of a strategy paper run.

    All fields must be declared before any child process starts.
    All fields must match config + runtime state or the run is aborted.
    All evidence records produced by this run are stamped with as_dict().
    """
    strategy_id: str
    preset:      str
    symbol:      str
    venue:       str
    stage:       str
    commit:      str = field(default_factory=_get_commit)

    @classmethod
    def from_config(cls, strategy_id: str, cfg: dict[str, Any]) -> "RuntimeIdentity":
        """Build identity from strategy config dict and runtime state."""
        s = cfg.get("strategy", {})
        return cls(
            strategy_id = strategy_id,
            preset      = str(s.get("id") or strategy_id),
            symbol      = str(s.get("symbol") or "").strip(),
            venue       = str(s.get("venue")  or "").strip(),
            stage       = str(s.get("stage")  or "paper").strip(),
        )

    def verify(self) -> None:
        """Verify identity is complete and matches runtime stage.

        Raises RuntimeIdentityError if any field is missing or mismatched.
        """
        errors: list[str] = []

        if not self.strategy_id:
            errors.append("strategy_id is empty")
        if not self.symbol:
            errors.append("symbol is empty — set strategy.symbol in config")
        if not self.venue:
            errors.append("venue is empty — set strategy.venue in config")
        if not self.stage:
            errors.append("stage is empty")

        try:
            actual = get_current_stage(self.strategy_id).value
            if actual != self.stage:
                errors.append(
                    f"stage mismatch: config declares '{self.stage}' "
                    f"but runtime stage is '{actual}'"
                )
        except Exception as e:
            errors.append(f"could not read runtime stage: {e}")

        if errors:
            msg = (
                "RuntimeIdentityError for " + self.strategy_id + ":\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
            _LOG.error("runtime_identity.verification_failed strategy=%s errors=%s",
                       self.strategy_id, errors)
            raise RuntimeIdentityError(msg)

        _LOG.info(
            "runtime_identity.verified strategy=%s preset=%s symbol=%s "
            "venue=%s stage=%s commit=%s",
            self.strategy_id, self.preset, self.symbol,
            self.venue, self.stage, self.commit,
        )

    def log_stamp(self) -> None:
        """Print + log the full identity at INFO level."""
        _LOG.info(
            "runtime_identity.stamp strategy_id=%s preset=%s symbol=%s "
            "venue=%s stage=%s commit=%s",
            self.strategy_id, self.preset, self.symbol,
            self.venue, self.stage, self.commit,
        )
        _LOG.info(
            "\nRuntime Identity — %s\n"
            "  preset  : %s\n"
            "  symbol  : %s\n"
            "  venue   : %s\n"
            "  stage   : %s\n"
            "  commit  : %s",
            self.strategy_id, self.preset,
            self.symbol, self.venue, self.stage, self.commit,
        )

    def as_dict(self) -> dict[str, str]:
        """Return dict for stamping evidence records."""
        return {
            "_strategy_id": self.strategy_id,
            "_preset":      self.preset,
            "_symbol":      self.symbol,
            "_venue":       self.venue,
            "_stage":       self.stage,
            "_commit":      self.commit,
        }
