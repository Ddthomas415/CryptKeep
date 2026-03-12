import uuid
from typing import Any


def success(data: Any, meta: dict | None = None, request_id: str | None = None) -> dict:
    return {
        "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
        "status": "success",
        "data": data,
        "error": None,
        "meta": meta or {},
    }


def failure(
    code: str,
    message: str,
    details: dict | None = None,
    request_id: str | None = None,
) -> dict:
    return {
        "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
        "status": "error",
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": {},
    }
