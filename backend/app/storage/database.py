"""异步数据库引擎与会话工厂。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, future=True)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每请求一个会话。"""
    async with SessionMaker() as session:
        yield session
