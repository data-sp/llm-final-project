from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()


def token_key(tg_user_id: int) -> str:
    return f"token:{tg_user_id}"


def _extract_user_id(message: Message) -> int | None:
    if message.from_user is None:
        return None
    return message.from_user.id


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    await message.answer(
        "Привет! Сначала получите JWT в Auth Service, затем отправьте его командой:\n"
        "/token <jwt>"
    )


@router.message(Command("token"))
async def token_command(
    message: Message,
    command: CommandObject | None = None,
) -> None:
    tg_user_id = _extract_user_id(message)
    if tg_user_id is None:
        await message.answer("Не удалось определить Telegram user_id.")
        return

    args = command.args if command and command.args else ""
    if not args and message.text:
        parts = message.text.split(maxsplit=1)
        args = parts[1] if len(parts) == 2 else ""

    token = args.strip()
    if not token:
        await message.answer("Передайте JWT так: /token <jwt>")
        return

    try:
        decode_and_validate(token)
    except ValueError:
        await message.answer(
            "Токен неверный или истек. Получите новый токен в Auth Service."
        )
        return

    redis_client = get_redis()
    await redis_client.set(token_key(tg_user_id), token)

    await message.answer("JWT-токен принят и сохранён.")


@router.message(F.text)
async def handle_text_message(message: Message) -> None:
    if message.text is None:
        return

    if message.text.startswith("/"):
        await message.answer("Неизвестная команда. Для сохранения токена используйте /token <jwt>.")
        return

    tg_user_id = _extract_user_id(message)
    if tg_user_id is None:
        await message.answer("Не удалось определить Telegram user_id.")
        return

    redis_client = get_redis()
    token = await redis_client.get(token_key(tg_user_id))

    if not token:
        await message.answer(
            "Доступ запрещен: JWT-токен не найден. "
            "Получите токен в Auth Service и отправьте /token <jwt>."
        )
        return

    try:
        decode_and_validate(token)
    except ValueError:
        await redis_client.delete(token_key(tg_user_id))
        await message.answer(
            "Доступ запрещен: JWT-токен неверный или истёк. "
            "Получите новый токен в Auth Service."
        )
        return

    llm_request.delay(message.chat.id, message.text)
    await message.answer("Запрос принят в очередь. Ответ придет после обработки.")
