from __future__ import annotations

from backend.app.domain.policy.terminal_policy import (
    DANGEROUS_PREFIXES,
    READ_ONLY_PREFIXES,
    SEMI_SENSITIVE_PREFIXES,
)

APPROVED_TERMINAL_PREFIXES = READ_ONLY_PREFIXES + SEMI_SENSITIVE_PREFIXES + DANGEROUS_PREFIXES


class TerminalService:
    @staticmethod
    def _is_approved_command(normalized: str) -> bool:
        return normalized.startswith(APPROVED_TERMINAL_PREFIXES)

    def execute(self, command: str) -> dict:
        normalized = command.strip().lower()

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

        if normalized == "kill-switch on":
            return {
                "command": command,
                "output": [
                    {
                        "type": "warning",
                        "value": "This will pause all strategy execution.",
                    }
                ],
                "requires_confirmation": True,
                "confirmation_token": "confirm_123",
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

    def confirm(self, confirmation_token: str) -> dict:
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
