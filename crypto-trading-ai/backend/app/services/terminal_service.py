from __future__ import annotations

import secrets
import time

from backend.app.domain.policy.terminal_policy import (
    is_approved_terminal_command,
    is_dangerous_terminal_command,
    normalize_terminal_command,
)
CONFIRMATION_TTL_SECONDS = 300
MAX_PENDING_CONFIRMATIONS = 512


class TerminalService:
    def __init__(self) -> None:
        self._pending_confirmations: dict[str, dict[str, object]] = {}

    @staticmethod
    def _is_approved_command(normalized: str) -> bool:
        return is_approved_terminal_command(normalized)

    def _prune_expired_confirmations(self) -> None:
        now = time.time()
        for token, record in list(self._pending_confirmations.items()):
            expires_at = float(record.get("expires_at", 0))
            if expires_at <= now:
                self._pending_confirmations.pop(token, None)

    def _mint_confirmation_token(self, command: str) -> str:
        self._prune_expired_confirmations()

        token = f"confirm_{secrets.token_urlsafe(18)}"
        self._pending_confirmations[token] = {
            "command": command,
            "expires_at": time.time() + CONFIRMATION_TTL_SECONDS,
        }

        if len(self._pending_confirmations) > MAX_PENDING_CONFIRMATIONS:
            oldest_token = next(iter(self._pending_confirmations))
            self._pending_confirmations.pop(oldest_token, None)

        return token

    def execute(self, command: str) -> dict:
        normalized = normalize_terminal_command(command)

        if not normalized:
            return {
                "command": command,
                "output": [
                    {
                        "type": "error",
                        "value": "Command rejected. A non-empty command is required.",
                    }
                ],
                "requires_confirmation": False,
            }

        if not self._is_approved_command(normalized):
            return {
                "command": command,
                "output": [
                    {
                        "type": "error",
                        "value": (
                            "Command rejected. Only approved product terminal commands are allowed."
                        ),
                    }
                ],
                "requires_confirmation": False,
            }

        if is_dangerous_terminal_command(normalized):
            confirmation_token = self._mint_confirmation_token(normalized)
            warning_value = "Dangerous command requires explicit confirmation."
            if normalized == "kill-switch on":
                warning_value = "This will pause all strategy execution."
            return {
                "command": command,
                "output": [
                    {
                        "type": "warning",
                        "value": warning_value,
                    }
                ],
                "requires_confirmation": True,
                "confirmation_token": confirmation_token,
            }

        if normalized == "status":
            return {
                "command": command,
                "output": [
                    {
                        "type": "text",
                        "value": "System status (mock): mode=research_only risk=safe kill_switch=off",
                    }
                ],
                "requires_confirmation": False,
            }

        if normalized == "help":
            return {
                "command": command,
                "output": [
                    {
                        "type": "text",
                        "value": (
                            "Approved commands include: help, status, market <asset>, why <asset>, "
                            "news <asset>, risk show, connections test, approvals list, logs tail, "
                            "mode set ..., approve trade ..., kill-switch on/off, trading resume."
                        ),
                    }
                ],
                "requires_confirmation": False,
            }

        return {
            "command": command,
            "output": [
                {
                    "type": "text",
                    "value": f"Accepted approved product command (mock): {command}",
                }
            ],
            "requires_confirmation": False,
        }

    def confirm(self, confirmation_token: str) -> dict | None:
        self._prune_expired_confirmations()
        record = self._pending_confirmations.pop(confirmation_token, None)
        if not record:
            return None

        return {
            "confirmation_token": confirmation_token,
            "confirmed": True,
            "output": [
                {
                    "type": "text",
                    "value": "Confirmed mock command execution.",
                }
            ],
        }
