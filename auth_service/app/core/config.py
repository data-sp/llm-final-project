from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "auth-service"
    env: str = "local"

    jwt_secret: str = "change_me_super_secret"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    sqlite_path: str = "./auth.db"
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self._make_async_sqlite_url(self.database_url)

        sqlite_path = self.sqlite_path
        if sqlite_path == ":memory:":
            return "sqlite+aiosqlite:///:memory:"

        path = Path(sqlite_path)
        if path.is_absolute():
            return f"sqlite+aiosqlite:///{path}"

        return f"sqlite+aiosqlite:///{sqlite_path}"

    @staticmethod
    def _make_async_sqlite_url(url: str) -> str:
        if url.startswith("sqlite+aiosqlite"):
            return url
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return url


settings = Settings()
