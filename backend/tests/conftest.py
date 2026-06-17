"""测试隔离：所有测试连独立的 marsian_test 库，绝不碰开发库 marsian。

必须在导入任何 app 模块之前设置 DATABASE_URL —— app.storage.database 在导入时即按
settings 建 engine。
"""

import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://marsian:marsian@localhost:5433/marsian_test"

import asyncpg  # noqa: E402
import pytest  # noqa: E402

from app.storage.database import engine  # noqa: E402
from app.storage.models import Base  # noqa: E402


async def _ensure_test_db() -> None:
    conn = await asyncpg.connect(
        user="marsian", password="marsian", host="localhost", port=5433, database="marsian"
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname='marsian_test'")
        if not exists:
            await conn.execute("CREATE DATABASE marsian_test")
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
async def _schema() -> None:
    await _ensure_test_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
