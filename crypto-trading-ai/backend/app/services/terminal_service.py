class TerminalService:
    def execute(self, command: str) -> dict:
        normalized = command.strip().lower()

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

        return {
            "command": command,
            "output": [
                {
                    "type": "text",
                    "value": f"Executed mock terminal command: {command}",
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
