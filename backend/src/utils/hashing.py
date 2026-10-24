"""Hashing and short-code generation utilities."""

import hashlib
import secrets

# URL-safe alphabet without visually ambiguous characters (0/O, 1/l/I).
SHORT_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def generate_short_code(length: int = 7) -> str:
    """Return a cryptographically random short code."""
    if length < 4:
        raise ValueError("Short code length must be at least 4 characters")
    return "".join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(length))


def sha256_hex(value: str) -> str:
    """Stable hex digest used for URL deduplication keys and limiter keys."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_token(token: str) -> str:
    """Never store raw bearer tokens in a rate-limiter key."""
    return sha256_hex(token)[:32]
