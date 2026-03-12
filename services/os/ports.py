from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class PortResolution:
    host: str
    requested_port: int
    resolved_port: int
    requested_available: bool
    auto_switched: bool


def can_bind(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def resolve_preferred_port(host: str, preferred_port: int, *, max_offset: int = 50) -> PortResolution:
    normalized_host = str(host or "127.0.0.1").strip() or "127.0.0.1"
    requested_port = max(1, int(preferred_port))
    requested_available = can_bind(normalized_host, requested_port)
    if requested_available:
        return PortResolution(
            host=normalized_host,
            requested_port=requested_port,
            resolved_port=requested_port,
            requested_available=True,
            auto_switched=False,
        )

    for offset in range(1, max(1, int(max_offset)) + 1):
        candidate = requested_port + offset
        if candidate > 65535:
            break
        if can_bind(normalized_host, candidate):
            return PortResolution(
                host=normalized_host,
                requested_port=requested_port,
                resolved_port=candidate,
                requested_available=False,
                auto_switched=True,
            )

    return PortResolution(
        host=normalized_host,
        requested_port=requested_port,
        resolved_port=requested_port,
        requested_available=False,
        auto_switched=False,
    )
