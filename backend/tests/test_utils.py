"""Unit tests for utilities that do not require PostgreSQL/Redis."""

import pytest
from fastapi import HTTPException

from src.utils.hashing import (
    SHORT_CODE_ALPHABET,
    generate_short_code,
    sha256_hex,
)
from src.utils.qr import generate_qr_data_uri, generate_qr_svg
from src.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.utils.url_validator import validate_url_syntax


def test_short_code_length_and_alphabet():
    code = generate_short_code(7)
    assert len(code) == 7
    assert set(code) <= set(SHORT_CODE_ALPHABET)
    assert generate_short_code(7) != generate_short_code(7)


def test_short_code_rejects_too_short_length():
    with pytest.raises(ValueError):
        generate_short_code(3)


def test_sha256_is_stable():
    assert sha256_hex("https://example.com") == sha256_hex("https://example.com")
    assert sha256_hex("a") != sha256_hex("b")


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_password_longer_than_72_bytes_is_truncated_consistently():
    password = "x" * 100
    hashed = hash_password(password)
    assert verify_password(password, hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-id")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-id"
    assert decode_access_token("not-a-token") is None


def test_qr_generation():
    svg = generate_qr_svg("http://localhost:8080/l/abc1234")
    assert svg.lstrip().startswith(b"<?xml") or svg.lstrip().startswith(b"<svg")
    uri = generate_qr_data_uri("http://localhost:8080/l/abc1234")
    assert uri.startswith("data:image/svg+xml;base64,")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://example.com", "https://example.com/"),
        ("example.com/path?q=1", "http://example.com/path?q=1"),
        ("http://sub.example.co.uk/a#section", "http://sub.example.co.uk/a#section"),
    ],
)
def test_valid_urls_are_normalized(raw, expected):
    assert validate_url_syntax(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "http://asfasf",
        "www.somedomain.ashgiasoghgiaso",
        "ftp://example.com/file",
        "http://exa mple.com",
        "http://-broken.com",
        "http://127.0.0.1/admin",
        "http://localhost:8000",
        "https://user:password@example.com",
        "http://example.com:not-a-port",
        "",
    ],
)
def test_invalid_urls_are_rejected(raw):
    with pytest.raises(HTTPException) as exc_info:
        validate_url_syntax(raw)
    assert exc_info.value.status_code == 400
