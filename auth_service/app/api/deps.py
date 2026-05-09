from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, PermissionDeniedError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_session
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def get_users_repo(db: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(db)


def get_auth_uc(
    users_repo: UsersRepository = Depends(get_users_repo),
) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError()

    payload = decode_token(credentials.credentials)
    subject = payload.get("sub")

    if subject is None:
        raise InvalidTokenError()

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
) -> User:
    return await auth_uc.me(user_id=user_id)


async def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise PermissionDeniedError()
    return current_user
