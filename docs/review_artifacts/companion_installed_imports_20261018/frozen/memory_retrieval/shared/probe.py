"""Opt-in request-local compatibility policy, not a network sandbox."""
from __future__ import annotations

from contextvars import ContextVar
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

PROBE_HEADER = "X-CryptKeep-Probe"
PROBE_PROFILE = "single-cited-query-v1"
_active: ContextVar[bool] = ContextVar("cryptkeep_strict_probe", default=False)
_ORIGINS = frozenset({
    ("http", "memory-retrieval:8007"),
    ("http", "risk-stub:8008"),
    ("http", "audit-log:8009"),
})
_STORAGE_ENDPOINTS = {"qdrant": "http://qdrant:6333", "minio": "http://minio:9000"}


def probe_active() -> bool:
    return _active.get()


def probe_headers() -> dict[str, str]:
    return {PROBE_HEADER: PROBE_PROFILE} if probe_active() else {}


def require_probe_origin(url: str) -> None:
    if not probe_active():
        return
    target = urlsplit(url)
    if (target.scheme, target.netloc) not in _ORIGINS or target.username is not None or target.password is not None:
        raise RuntimeError("probe_origin_forbidden")


def require_storage_endpoint(service: str, url: str) -> None:
    """Accept only the exact storage endpoint, optionally with a trailing slash."""
    base = _STORAGE_ENDPOINTS.get(service)
    if base is None or url not in (base, base + "/"):
        raise RuntimeError("restricted_storage_endpoint_forbidden")


class ProbePolicyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        values = [value for name, value in scope.get("headers", [])
                  if name.lower() == PROBE_HEADER.lower().encode("ascii")]
        # Do not silently fall through to the unrestricted path on a typo.
        if values and values != [PROBE_PROFILE.encode("ascii")]:
            await JSONResponse({"detail": "unsupported_probe_profile"}, status_code=400)(scope, receive, send)
            return
        enabled = bool(values)
        token = _active.set(enabled)

        async def send_response(message):
            if enabled and message["type"] == "http.response.start":
                message = {**message, "headers": [*message.get("headers", []),
                    (PROBE_HEADER.lower().encode("ascii"), PROBE_PROFILE.encode("ascii"))]}
            await send(message)

        try:
            await self.app(scope, receive, send_response)
        finally:
            _active.reset(token)
