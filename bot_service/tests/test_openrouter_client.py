import httpx
import pytest
import respx

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_returns_message_text(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "test-api-key")

    route = respx.post(
        f"{settings.openrouter_base_url}/chat/completions"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Тестовый ответ LLM"
                        }
                    }
                ]
            },
        )
    )

    answer = await call_openrouter("Привет")

    assert answer == "Тестовый ответ LLM"
    assert route.called
