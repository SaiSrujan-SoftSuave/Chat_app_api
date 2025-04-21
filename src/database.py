from typing import Any, AsyncGenerator

from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from src.config import Config

async_engine = create_async_engine(
    url= Config.DATABASE_URL, echo=True
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


redis_client: Redis = Redis(host="redis", port=6379, decode_responses=True)

async def init_db() -> None:
    """initializing database"""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession | Any, Any]:
    """getting async database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_redis() -> Redis:
    """getting redis client"""
    return redis_client