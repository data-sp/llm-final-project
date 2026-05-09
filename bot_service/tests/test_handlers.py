from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from jose import jwt

from app.bot.handlers import handle_text_message, token_command, token_key
from app.core.config import settings


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int


class FakeMessage:
    def __init__(self, text: str, user_id: int = 777, chat_id: int = 999) -> None:
        self.text = text
        self.from_user = FakeUser(id=user_id)
        self.chat = FakeChat(id=chat_id)
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs: object) -> None:
        self.answers.append(text)


def make_token(sub: str = "123", role: str = "user") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def make_expired_token(sub: str = "123") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": "user",
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "exp": int((now - timedelta(minutes=1)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


@pytest.mark.asyncio
async def test_token_command_saves_token_in_redis(fake_redis, mocker) -> None:
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    token = make_token()
    message = FakeMessage(text=f"/token {token}", user_id=777)

    await token_command(message, SimpleNamespace(args=token))

    saved_token = await fake_redis.get(token_key(777))
    assert saved_token == token
    assert "принят" in message.answers[-1].lower()


@pytest.mark.asyncio
async def test_text_without_token_denies_access(fake_redis, mocker) -> None:
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    message = FakeMessage(text="Расскажи про FastAPI", user_id=777, chat_id=999)

    await handle_text_message(message)

    delay_mock.assert_not_called()
    assert "доступ запрещ" in message.answers[-1].lower()


@pytest.mark.asyncio
async def test_text_with_valid_token_sends_celery_task(fake_redis, mocker) -> None:
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    token = make_token(sub="123")
    await fake_redis.set(token_key(777), token)

    message = FakeMessage(text="Что такое JWT?", user_id=777, chat_id=999)

    await handle_text_message(message)

    delay_mock.assert_called_once_with(999, "Что такое JWT?")
    assert "запрос принят" in message.answers[-1].lower()


@pytest.mark.asyncio
async def test_text_with_garbage_token_in_redis_denies_and_skips_celery(
    fake_redis,
    mocker,
) -> None:
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    await fake_redis.set(token_key(777), "not-a-valid-jwt")

    message = FakeMessage(text="Проверка мусорного токена", user_id=777, chat_id=999)

    await handle_text_message(message)

    delay_mock.assert_not_called()
    assert "доступ запрещ" in message.answers[-1].lower()


@pytest.mark.asyncio
async def test_text_with_expired_token_in_redis_denies_and_clears_redis(
    fake_redis,
    mocker,
) -> None:
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    expired = make_expired_token()
    await fake_redis.set(token_key(777), expired)

    message = FakeMessage(text="Вопрос после истечения токена", user_id=777, chat_id=999)

    await handle_text_message(message)

    delay_mock.assert_not_called()
    assert "доступ запрещ" in message.answers[-1].lower()
    assert await fake_redis.get(token_key(777)) is None
