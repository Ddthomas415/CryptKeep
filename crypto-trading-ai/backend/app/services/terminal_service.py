from __future__ import annotations

import secrets
import time

from backend.app.domain.workflows.execute_terminal_command import execute_terminal_workflow
CONFIRMATION_TTL_SECONDS = 300
MAX_PENDING_CONFIRMATIONS = 512


class TerminalService:
    def __init__(self) -> None:
        self._pending_confirmations: dict[str, dict[str, object]] = {}

    def _prune_expired_confirmations(self) -> None:
        now = time.time()
        for token, record in list(self._pending_confirmations.items()):
            expires_at = float(record.get("expires_at", 0))
            if expires_at <= now:
                self._pending_confirmations.pop(token, None)

    def _mint_confirmation_token(self, command: str, *, subject: str, role: str) -> str:
        self._prune_expired_confirmations()

        token = f"confirm_{secrets.token_urlsafe(18)}"
        self._pending_confirmations[token] = {
            "command": command,
            "subject": subject,
            "role": role,
            "expires_at": time.time() + CONFIRMATION_TTL_SECONDS,
        }

        if len(self._pending_confirmations) > MAX_PENDING_CONFIRMATIONS:
            oldest_token = next(iter(self._pending_confirmations))
            self._pending_confirmations.pop(oldest_token, None)

        return token

    def execute(
        self,
        command: str,
        *,
        role: str,
        subject: str,
        mode: str,
        risk_state: str,
        kill_switch_on: bool,
    ) -> dict:
        result = execute_terminal_workflow(
            {
                "command": command,
                "role": role,
                "mode": mode,
                "risk_state": risk_state,
                "kill_switch_on": kill_switch_on,
            }
        )

        if not bool(result.success):
            return {
                "command": command,
                "output": [
                    {
                        "type": "error",
                        "value": str(result.message or "Command rejected."),
                    }
                ],
                "requires_confirmation": False,
            }

        normalized = " ".join(str(command or "").strip().lower().split())
        requires_confirmation = "Require user confirmation" in list(result.next_actions or [])
        if requires_confirmation:
            confirmation_token = self._mint_confirmation_token(normalized, subject=subject, role=role)
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
                        "value": f"System status (mock): mode={mode} risk={risk_state} kill_switch={'on' if kill_switch_on else 'off'}",
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

    def confirm(self, confirmation_token: str, *, subject: str) -> dict | None:
        self._prune_expired_confirmations()
        record = self._pending_confirmations.pop(confirmation_token, None)
        if not record:
            return None
        if str(record.get("subject") or "") != str(subject or ""):
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
