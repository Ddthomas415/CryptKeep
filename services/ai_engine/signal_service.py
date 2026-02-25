from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from services.ai_engine.features import build_feature_map
from services.ai_engine.model import LinearSignalModel
from services.os.app_paths import data_dir, ensure_dirs


@dataclass(frozen=True)
class AISignalResult:
    ok: bool
    reason: str
    side: str
    proba_up: float
    threshold: float
    model_version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "reason": str(self.reason),
            "side": str(self.side),
            "proba_up": float(self.proba_up),
            "threshold": float(self.threshold),
            "model_version": int(self.model_version),
        }


class AISignalService:
    def __init__(self, model_path: str = "") -> None:
        ensure_dirs()
        self.model_path = (
            Path(model_path).expanduser().resolve()
            if str(model_path or "").strip()
            else (data_dir() / "ai_model.json")
        )
        self._model: LinearSignalModel | None = None

    def _load_model(self) -> LinearSignalModel | None:
        if self._model is not None:
            return self._model
        if not self.model_path.exists():
            return None
        try:
            payload = json.loads(self.model_path.read_text(encoding="utf-8"))
            self._model = LinearSignalModel.from_dict(payload)
            return self._model
        except Exception:
            return None

    def evaluate(
        self,
        *,
        side: str,
        context: Dict[str, Any] | None = None,
        buy_threshold: float = 0.55,
        sell_threshold: float = 0.45,
    ) -> AISignalResult:
        model = self._load_model()
        if model is None:
            return AISignalResult(
                ok=True,
                reason="model_missing_pass_through",
                side=str(side or ""),
                proba_up=0.5,
                threshold=float(buy_threshold if str(side).lower() == "buy" else sell_threshold),
                model_version=0,
            )

        feats = build_feature_map(context or {})
        ok, reason, proba = model.evaluate_side(
            side=str(side or ""),
            features=feats,
            buy_threshold=float(buy_threshold),
            sell_threshold=float(sell_threshold),
        )
        threshold = float(buy_threshold if str(side).lower() == "buy" else sell_threshold)
        return AISignalResult(
            ok=bool(ok),
            reason=str(reason),
            side=str(side or ""),
            proba_up=float(proba),
            threshold=threshold,
            model_version=int(model.version),
        )

