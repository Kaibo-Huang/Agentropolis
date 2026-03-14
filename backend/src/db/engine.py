from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=5,
    echo=False,
    # asyncpg requires SSL to be passed via connect_args, not the URL query string.
    connect_args={"ssl": True},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an AsyncSession per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Called at application startup. Validates the connection pool."""
    async with engine.begin() as conn:
        # Lightweight connectivity check — no DDL (Alembic owns the schema).
        await conn.run_sync(lambda _: None)


async def close_db() -> None:
    """Called at application shutdown. Drains the connection pool."""
    await engine.dispose()
