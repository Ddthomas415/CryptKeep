from copy import deepcopy

from backend.app.schemas.risk import RiskLimits, RiskSummary


class RiskService:
    _limits: dict | None = None

    @classmethod
    def _ensure_limits(cls) -> None:
        if cls._limits is None:
            cls._limits = RiskLimits.default()

    def get_summary(self) -> dict:
        return RiskSummary.example()

    def get_limits(self) -> dict:
        self._ensure_limits()
        return deepcopy(self._limits)

    def update_limits(self, patch: dict) -> dict:
        self._ensure_limits()
        next_limits = deepcopy(self._limits)
        next_limits.update(patch)
        # Validate merged payload against the full schema before storing.
        validated = RiskLimits(**next_limits).model_dump()
        self._limits = validated
        return deepcopy(self._limits)
