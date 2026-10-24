"""Helpers for extracting request metadata behind the Nginx reverse proxy."""

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Return the real client IP.

    The backends are only reachable through Nginx, which sets
    ``X-Forwarded-For`` / ``X-Real-IP``. Trusting these headers is therefore
    safe in this deployment topology and keeps per-IP rate limiting working
    instead of putting every visitor into the proxy's bucket.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first[:64]

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()[:64]

    return request.client.host if request.client else "unknown"
