"""M0 最小闭环验收（设计规格 §6）。触网 + 真实 PostgreSQL，标记 integration。

跑前需：docker compose up -d 且 alembic upgrade head。
"""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import get_providers
from app.main import app
from app.providers.baostock_provider import BaostockProvider
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

START, END = "2024-01-01", "2024-12-31"
SYMBOL = "600519.SH"


class CountingProvider(BaostockProvider):
    """统计 get_daily_bars 被调用次数，用于验证"二次请求命中库不再抓取"。"""

    daily_calls = 0

    def get_daily_bars(self, symbol: str, start: date, end: date) -> list:  # type: ignore[type-arg]
        type(self).daily_calls += 1
        return super().get_daily_bars(symbol, start, end)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # 清空数据，确保从"空库 → 按需加载"走完整链路
    await engine.dispose()  # 清掉上一个测试 event loop 残留的池连接
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE daily_bars, instruments RESTART IDENTITY CASCADE"))
    CountingProvider.daily_calls = 0
    provider = CountingProvider()
    app.dependency_overrides[get_providers] = lambda: [provider]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_m0_full_closeout(client: AsyncClient) -> None:
    # §6.1 首次请求 → 自动抓取入库 → 返回后复权日线
    r1 = await client.get(
        "/api/kline", params={"symbol": SYMBOL, "period": "d", "start": START, "end": END}
    )
    assert r1.status_code == 200
    daily = r1.json()
    assert len(daily) > 200
    assert daily == sorted(daily, key=lambda b: b["date"])  # 升序
    assert CountingProvider.daily_calls == 1  # 抓了一次

    # §6.2 二次请求命中库，不再抓取
    r2 = await client.get(
        "/api/kline", params={"symbol": SYMBOL, "period": "d", "start": START, "end": END}
    )
    assert r2.status_code == 200
    assert CountingProvider.daily_calls == 1  # 仍是 1，没有再抓

    # §6.3 周/月聚合行数合理（远少于日线）
    wk = (
        await client.get(
            "/api/kline", params={"symbol": SYMBOL, "period": "w", "start": START, "end": END}
        )
    ).json()
    mo = (
        await client.get(
            "/api/kline", params={"symbol": SYMBOL, "period": "m", "start": START, "end": END}
        )
    ).json()
    assert 40 <= len(wk) <= 55  # 2024 约 50 个交易周
    assert len(mo) == 12

    # §6.4 adjust=qfq 最新日 == 不复权最新价（none 口径下的最新 close）
    qfq = (
        await client.get(
            "/api/kline", params={"symbol": SYMBOL, "adjust": "qfq", "start": START, "end": END}
        )
    ).json()
    none = (
        await client.get(
            "/api/kline", params={"symbol": SYMBOL, "adjust": "none", "start": START, "end": END}
        )
    ).json()
    assert qfq[-1]["close"] == pytest.approx(none[-1]["close"], rel=1e-9)

    # §6.5 停牌日可识别（trade_status 字段透传，取值 0/1）
    assert all(b["trade_status"] in (0, 1) for b in daily)

    # §6.6 instruments 表有该票元数据与 coverage
    async with SessionMaker() as session:
        row = (
            await session.execute(
                text("SELECT name, type, data_start, data_end FROM instruments WHERE symbol=:s"),
                {"s": SYMBOL},
            )
        ).one()
    name, typ, data_start, data_end = row
    assert "茅台" in name
    assert typ == "stock"
    assert data_start is not None and data_end is not None
