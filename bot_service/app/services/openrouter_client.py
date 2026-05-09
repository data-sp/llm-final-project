from typing import Any

import httpx

from app.core.config import settings


class OpenRouterError(RuntimeError):
    pass


async def call_openrouter(prompt: str) -> str:
    if not settings.openrouter_api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured")

    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }
    payload: dict[str, Any] = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты полезный русскоязычный ассистент для кратких "
                    "и точных LLM-консультаций."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise OpenRouterError(
            f"OpenRouter returned HTTP {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter response has unexpected format") from exc

    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("OpenRouter returned empty answer")

    return content.strip()
