"""Strict URL validation.

Business rule #4: a URL must be syntactically valid *and* its domain must
actually exist. Validation is split in two stages:

1. :func:`validate_url_syntax` - synchronous, pure parsing. It rejects strings
   such as ``http://asfasf`` or ``www.somedomain.ashgiasoghgiaso`` because they
   have no registrable public suffix.
2. :func:`ensure_domain_available` - asynchronous DNS resolution (mandatory)
   plus an optional HTTP probe. Private / loopback addresses are rejected to
   prevent SSRF.

Both are combined in :func:`validate_and_normalize_url`, which is what the
service layer calls.
"""

import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlsplit, urlunsplit

import httpx
import tldextract
from fastapi import HTTPException, status

from src.config import settings

logger = logging.getLogger(__name__)

MAX_URL_LENGTH = 2048

# Offline extractor: use the snapshot bundled with tldextract and never call
# the public suffix list endpoint at runtime.
_tld_extractor = tldextract.TLDExtract(
    cache_dir=None,
    suffix_list_urls=(),
    fallback_to_snapshot=True,
)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _ensure_public_address(host: str) -> None:
    """Reject loopback / private / link-local / reserved addresses."""
    if settings.allow_private_hosts or not _is_ip_address(host):
        return
    address = ipaddress.ip_address(host)
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    ):
        raise _bad_request("URLs pointing to private or reserved addresses are not allowed")


def validate_url_syntax(raw_url: str) -> str:
    """Validate and normalize a URL; raise ``HTTPException(400)`` on failure."""
    if not isinstance(raw_url, str):
        raise _bad_request("URL must be a string")

    candidate = raw_url.strip()
    if not candidate:
        raise _bad_request("URL must not be empty")
    if len(candidate) > MAX_URL_LENGTH:
        raise _bad_request(f"URL must not exceed {MAX_URL_LENGTH} characters")
    if any(char.isspace() for char in candidate):
        raise _bad_request("URL must not contain whitespace")

    # Be forgiving for user input like "example.com" but never for garbage.
    if "://" not in candidate:
        candidate = f"http://{candidate}"

    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise _bad_request("Malformed URL") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise _bad_request("Only http:// and https:// URLs are supported")

    if parsed.username or parsed.password:
        raise _bad_request("URLs with embedded credentials are not allowed")

    try:
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise _bad_request("Invalid hostname or port") from exc

    if not host:
        raise _bad_request("URL must contain a hostname")

    host = host.rstrip(".").lower()
    if len(host) > 253:
        raise _bad_request("Hostname is too long")

    if _is_ip_address(host):
        _ensure_public_address(host)
        netloc = host if port is None else f"{host}:{port}"
    else:
        if "_" in host:
            raise _bad_request("Hostname must not contain underscores")
        if host.startswith("-") or host.endswith("-"):
            raise _bad_request("Malformed hostname")

        parsed_host = _tld_extractor(host)
        # This rejects hosts like "asfasf" or unknown TLDs such as ".ashgiasoghgiaso".
        if not parsed_host.domain or not parsed_host.suffix:
            raise _bad_request(
                "URL must contain a valid public domain (e.g. example.com)"
            )
        netloc = host if port is None else f"{host}:{port}"

    path = parsed.path or "/"
    normalized = urlunsplit((scheme, netloc, path, parsed.query, parsed.fragment))
    return normalized


async def ensure_domain_available(host: str) -> None:
    """Resolve ``host`` via DNS and optionally probe it over HTTP."""
    if settings.allow_private_hosts and host in {"localhost"}:
        return

    if _is_ip_address(host):
        # Already checked for private ranges in validate_url_syntax.
        return

    loop = asyncio.get_running_loop()
    try:
        resolved = await asyncio.wait_for(
            loop.getaddrinfo(host, None, type=socket.SOCK_STREAM),
            timeout=settings.url_check_timeout_seconds,
        )
    except (socket.gaierror, asyncio.TimeoutError, OSError) as exc:
        logger.info("DNS resolution failed for %s: %s", host, exc)
        raise _bad_request(
            f"Domain '{host}' cannot be resolved; the URL does not exist"
        ) from exc

    if not resolved:
        raise _bad_request(f"Domain '{host}' cannot be resolved")

    if not settings.allow_private_hosts:
        for _family, _type, _proto, _canonname, sockaddr in resolved:
            address = ipaddress.ip_address(sockaddr[0])
            if address.is_private or address.is_loopback or address.is_reserved:
                raise _bad_request(
                    "URL resolves to a private or reserved address"
                )


async def ensure_http_reachable(url: str) -> None:
    """Best-effort HTTP HEAD probe.

    DNS availability is already guaranteed. This probe additionally rejects a
    host that resolves but has no HTTP server listening (``ConnectError``).
    Sites that block ``HEAD`` (403/405) are accepted, because they clearly
    exist.
    """
    if not settings.url_http_check_enabled:
        return

    try:
        # Redirects are intentionally not followed: a public URL must not be
        # able to make the backend probe an internal address (SSRF), and the
        # final redirect target is only ever used by the client's browser.
        async with httpx.AsyncClient(
            follow_redirects=False,
            trust_env=False,
            timeout=settings.url_check_timeout_seconds,
            headers={
                "User-Agent": "URLShortenerBot/1.0 (+https://example.com/bot)"
            },
        ) as client:
            await client.head(url)
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        logger.info("HTTP probe could not connect to %s: %s", url, exc)
        raise _bad_request(
            "The website does not accept connections; check the URL"
        ) from exc
    except httpx.HTTPError as exc:
        # TLS errors, blocked HEAD requests, proxy issues, ... The domain is
        # valid, so do not block the user.
        logger.debug("HTTP probe for %s was inconclusive: %s", url, exc)


async def validate_and_normalize_url(raw_url: str) -> str:
    """Full validation pipeline used by the link service."""
    normalized = validate_url_syntax(raw_url)
    host = urlsplit(normalized).hostname or ""
    await ensure_domain_available(host)
    await ensure_http_reachable(normalized)
    return normalized
