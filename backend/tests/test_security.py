import pytest

from app.security import (
    InvalidToken,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext_and_verifies() -> None:
    h = hash_password("hunter2")
    assert h != "hunter2"
    assert "hunter2" not in h
    assert verify_password("hunter2", h) is True
    assert verify_password("wrong", h) is False


def test_token_roundtrip_returns_user_id() -> None:
    token = create_access_token(42)
    assert decode_token(token) == 42


def test_expired_token_raises() -> None:
    token = create_access_token(1, expires_minutes=-1)
    with pytest.raises(InvalidToken):
        decode_token(token)


def test_tampered_token_raises() -> None:
    token = create_access_token(1)
    with pytest.raises(InvalidToken):
        decode_token(token + "x")
