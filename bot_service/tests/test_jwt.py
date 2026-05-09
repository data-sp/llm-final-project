from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def make_token(sub: str = "123", role: str = "user") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def test_decode_and_validate_valid_token() -> None:
    token = make_token(sub="42")

    payload = decode_and_validate(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "user"


def test_decode_and_validate_invalid_token_raises_error() -> None:
    with pytest.raises(ValueError):
        decode_and_validate("not-a-jwt-token")
