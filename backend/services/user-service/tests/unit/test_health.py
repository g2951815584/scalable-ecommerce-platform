"""Core unit tests for user-service (no external dependencies)."""

from app.services.password import hash_password, verify_password
from app.services.token_service import (
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    hash_verification_code,
    sign_access_token,
)
from common.ids import new_id, next_id
from common.masking import mask_email, mask_phone, mask_value


def test_snowflake_ids_are_unique_and_stringified():
    ids = {new_id() for _ in range(1000)}
    assert len(ids) == 1000
    assert all(isinstance(value, str) and value.isdigit() for value in ids)


def test_next_id_returns_int():
    value = next_id()
    assert isinstance(value, int)
    assert value > 0


def test_password_hash_and_verify():
    hashed = hash_password("Str0ngPass!2026")
    assert hashed.startswith("$argon2id$")
    assert hashed != "Str0ngPass!2026"
    assert verify_password(hashed, "Str0ngPass!2026") is True
    assert verify_password(hashed, "wrong-password") is False


def test_access_token_roundtrip():
    token = sign_access_token(1024, ["BUYER", "ADMIN"])
    payload = decode_access_token(token)
    assert payload["sub"] == "1024"
    assert payload["roles"] == ["BUYER", "ADMIN"]
    assert set(payload) >= {"sub", "roles", "jti", "iat", "exp"}


def test_refresh_token_is_opaque_and_high_entropy():
    first = generate_refresh_token()
    second = generate_refresh_token()
    assert first != second
    assert len(first) >= 40
    digest = hash_refresh_token(first)
    assert len(digest) == 64
    assert digest == hash_refresh_token(first)


def test_verification_code_hash_is_deterministic():
    digest = hash_verification_code("123456", "alice@example.com", "REGISTER")
    assert digest == hash_verification_code("123456", "alice@example.com", "REGISTER")
    assert digest != hash_verification_code("654321", "alice@example.com", "REGISTER")


def test_masking():
    assert mask_email("alice@example.com") == "ali***@example.com"
    assert mask_phone("+8613800138000") == "+861****8000"
    assert mask_value("password", "secret") == "***"
    assert mask_value("access_token", "jwt") == "***"
