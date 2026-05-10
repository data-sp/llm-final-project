# llm-final-project

Итоговый проект: двухсервисная система LLM-консультаций.

## Архитектура

Проект разделён на два независимых сервиса:

1. **Auth Service** — FastAPI-сервис регистрации, логина и выпуска JWT.
2. **Bot Service** — Telegram-бот на aiogram, который валидирует JWT, сохраняет токен в Redis и отправляет LLM-запросы в Celery через RabbitMQ.

Auth Service не знает ничего о Telegram и LLM.  
Bot Service не регистрирует пользователей, не логинит их и не ходит в базу Auth Service.  
JWT создаётся только в Auth Service. Bot Service только валидирует JWT по общему `JWT_SECRET`.

## Схема работы

```text
User -> Auth Service /auth/register
User -> Auth Service /auth/login -> JWT
User -> Telegram Bot /token <JWT>
Bot -> Redis: сохранить JWT по token:<telegram_user_id>
User -> Telegram Bot: вопрос
Bot -> Redis: получить JWT
Bot -> JWT validation
Bot -> RabbitMQ/Celery: llm_request.delay(...)
Celery Worker -> OpenRouter
Celery Worker -> Telegram API: отправить ответ пользователю
```

## Демонстрация (скриншоты)

![Регистрация в Swagger](screenshots/auth-swagger-register.png)
![Логин и JWT](screenshots/auth-swagger-login.png)
![Профиль /auth/me](screenshots/auth-swagger-me.png)
![Сценарий в Telegram](screenshots/telegram-bot-flow.png)
![Очереди RabbitMQ](screenshots/rabbitmq-queues.png)
![Тесты Auth Service](screenshots/tests-auth-passed.png)
![Тесты Bot Service](screenshots/tests-bot-passed.png)

## Структура

```text
.
├── docker-compose.yml
├── README.md
├── screenshots
├── auth_service
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── repositories
│   │   ├── schemas
│   │   └── usecases
│   └── tests
└── bot_service
    ├── app
    │   ├── bot
    │   ├── core
    │   ├── infra
    │   ├── services
    │   └── tasks
    └── tests
```

## Быстрый запуск через Docker Compose

Перед запуском создайте локальные `.env` файлы:

```bash
cp auth_service/.env.example auth_service/.env
cp bot_service/.env.example bot_service/.env
```

В `bot_service/.env` задаются:

```text
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENROUTER_API_KEY=ваш_openrouter_api_key
```

`JWT_SECRET` и `JWT_ALG` в `auth_service/.env` и `bot_service/.env` должны совпадать.

Запуск:

```bash
docker compose up --build
```

После запуска:

- Auth Swagger: http://localhost:8000/docs
- Bot health: http://localhost:8001/health
- RabbitMQ UI: http://localhost:15672  
  Логин/пароль: `guest` / `guest`

## Локальный запуск Auth Service

```bash
cd auth_service
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Локальный запуск Bot Service

В локальном режиме удобнее поднимать Redis и RabbitMQ через Docker:

```bash
docker compose up redis rabbitmq
```

Затем:

```bash
cd bot_service
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
uv run celery -A app.infra.celery_app.celery_app worker --loglevel=info
uv run python -m app.bot.run_bot
```

Для запуска Bot Service вне Docker используются значения:

```text
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
```

## Пользовательский сценарий

1. Откройте Swagger Auth Service
2. Выполните `POST /auth/register`

Пример:

```json
{
  "email": "ivanov@email.com",
  "password": "StrongPassword123"
}
```

3. Выполните `POST /auth/login` через form-data:
   - `username`: `ivanov@email.com`
   - `password`: `StrongPassword123`

4. Скопируйте `access_token`.
5. В Telegram отправьте боту:

```text
/token <access_token>
```

6. После подтверждения отправьте обычный вопрос.
7. Бот поставит задачу в очередь и ответит после обработки Celery worker.

Дополнительно в Auth Service есть ручка `GET /auth/admin/ping`: она отвечает только если у пользователя в базе роль `admin` (обычный пользователь после регистрации получает `user` и получит `403`). Это демонстрирует использование доменного `PermissionDeniedError`.