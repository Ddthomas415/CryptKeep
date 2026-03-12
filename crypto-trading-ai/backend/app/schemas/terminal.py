from pydantic import BaseModel


class TerminalExecuteRequest(BaseModel):
    command: str


class TerminalConfirmRequest(BaseModel):
    confirmation_token: str


class TerminalOutputItem(BaseModel):
    type: str
    value: str


class TerminalExecuteResponse(BaseModel):
    command: str
    output: list[TerminalOutputItem]
    requires_confirmation: bool
    confirmation_token: str | None = None


class TerminalConfirmResponse(BaseModel):
    confirmation_token: str
    confirmed: bool
    output: list[TerminalOutputItem]
