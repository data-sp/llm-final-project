from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersRepository


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def register(self, *, email: str, password: str) -> User:
        normalized_email = email.lower().strip()

        existing_user = await self.users_repo.get_by_email(normalized_email)
        if existing_user is not None:
            raise UserAlreadyExistsError()

        password_hash = hash_password(password)

        try:
            user = await self.users_repo.create(
                email=normalized_email,
                password_hash=password_hash,
                role="user",
            )
            await self.users_repo.commit()
        except IntegrityError as exc:
            await self.users_repo.rollback()
            raise UserAlreadyExistsError() from exc

        return user

    async def login(self, *, email: str, password: str) -> str:
        normalized_email = email.lower().strip()

        user = await self.users_repo.get_by_email(normalized_email)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        return create_access_token(subject=user.id, role=user.role)

    async def me(self, *, user_id: int) -> User:
        user = await self.users_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user
