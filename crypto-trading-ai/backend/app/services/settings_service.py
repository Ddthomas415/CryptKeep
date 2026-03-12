from copy import deepcopy

from backend.app.schemas.settings import SettingsPayload


class SettingsService:
    _store: dict | None = None

    @classmethod
    def _ensure_store(cls) -> None:
        if cls._store is None:
            cls._store = SettingsPayload.example()

    def get_settings(self) -> dict:
        self._ensure_store()
        return deepcopy(self._store)

    def update_settings(
        self,
        patch: dict | None = None,
        *,
        general: dict | None = None,
        notifications: dict | None = None,
        ai: dict | None = None,
        security: dict | None = None,
    ) -> dict:
        self._ensure_store()
        next_state = deepcopy(self._store)

        if patch is None:
            patch = {
                "general": general,
                "notifications": notifications,
                "ai": ai,
                "security": security,
            }

        for section, updates in patch.items():
            if updates is None or section not in next_state:
                continue
            if isinstance(next_state[section], dict) and isinstance(updates, dict):
                next_state[section].update(updates)
            else:
                next_state[section] = updates

        self._store = next_state
        return deepcopy(self._store)
