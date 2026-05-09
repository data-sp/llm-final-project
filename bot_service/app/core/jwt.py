from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


def decode_and_validate(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    if not payload.get("sub"):
        raise ValueError("Token payload does not contain sub")

    return payload
