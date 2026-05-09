import asyncio

from aiogram import Bot

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterError, call_openrouter


async def _send_llm_answer(tg_chat_id: int, prompt: str) -> None:
    try:
        answer = await call_openrouter(prompt)
    except OpenRouterError as exc:
        answer = f"Не удалось получить ответ от LLM: {exc}"

    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(chat_id=tg_chat_id, text=answer)
    finally:
        await bot.session.close()


@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> dict[str, int | str]:
    asyncio.run(_send_llm_answer(tg_chat_id=tg_chat_id, prompt=prompt))
    return {"status": "sent", "tg_chat_id": tg_chat_id}
