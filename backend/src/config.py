from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Path: backend/src/config.py
# .env is at PROJECT ROOT: /Users/patrickwei/genai-genesis/.env
# parent(0) = src/, parent(1) = backend/, parent(2) = genai-genesis/
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GOOGLE_CLOUD_PROJECT: str
    OPENAI_API_KEY: str
    NEON_DB: str
    YOUR_NEON_API_KEY: str | None = None

    @computed_field
    @property
    def database_url(self) -> str:
        """
        Convert postgresql:// to postgresql+asyncpg:// for asyncpg driver.

        asyncpg does not accept sslmode/channel_binding as query parameters.
        Instead:
          - sslmode=require  →  connect_args ssl=True  (handled via query_str trick)
          - channel_binding  →  dropped (asyncpg uses channel binding by default
                                when ssl is enabled and the server advertises it)

        The cleanest approach for SQLAlchemy+asyncpg is to pass ssl in
        connect_args via create_engine.  Here we strip the unsupported params
        and add ?ssl=true which asyncpg's SQLAlchemy dialect maps to
        connect_args={"ssl": True} automatically.
        """
        raw = self.NEON_DB

        # Normalise scheme
        if raw.startswith("postgresql://"):
            raw = "postgresql+asyncpg://" + raw[len("postgresql://"):]
        elif raw.startswith("postgres://"):
            raw = "postgresql+asyncpg://" + raw[len("postgres://"):]

        # The SQLAlchemy asyncpg dialect does NOT translate sslmode/channel_binding
        # from the query string into asyncpg kwargs.  Strip all SSL-related params
        # here; SSL is enabled via connect_args={"ssl": True} in create_async_engine.
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key in ("sslmode", "channel_binding", "ssl"):
            qs.pop(key, None)
        new_query = urlencode({k: v[0] for k, v in qs.items()})
        cleaned = parsed._replace(query=new_query)
        return urlunparse(cleaned)


settings = Settings()
