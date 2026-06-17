"""按需加载的容错行为：查库优先、备源降级、全失败时降级读库、彻底无数据才报错。

用真实 PostgreSQL + 假 provider（不触网），快。标记 integration（需 docker PG）。
"""

from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.providers.base import Bar, DataProvider, Instrument
from app.services.market_data import ProviderUnavailable, get_kline
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

SYMBOL = "600519.SH"


def _bar(d: str, close: float) -> Bar:
    v = Decimal(str(close))
    return Bar(
        date=date.fromisoformat(d),
        open=v,
        high=v,
        low=v,
        close=v,
        volume=Decimal("1"),
        amount=Decimal("1"),
        raw_close=v,
        trade_status=1,
    )


class FakeProvider(DataProvider):
    def __init__(self, bars: list[Bar] | None = None, fail: bool = False) -> None:
        self.bars = bars or []
        self.fail = fail
        self.calls = 0

    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("baostock 查询失败: 10002007 网络接收错误")
        return [b for b in self.bars if start <= b.date <= end]

    def list_instruments(self) -> list[Instrument]:
        return [Instrument(SYMBOL, "贵州茅台", "SH", "stock", None, "listing")]

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        return []


@pytest.fixture
async def session() -> AsyncIterator[None]:
    await engine.dispose()  # 清掉上一个测试 event loop 残留的池连接
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE daily_bars, instruments RESTART IDENTITY CASCADE"))
    yield
    await engine.dispose()


async def _seed_instrument(s) -> None:  # type: ignore[no-untyped-def]
    await repo.upsert_instruments(
        s, [Instrument(SYMBOL, "贵州茅台", "SH", "stock", None, "listing")]
    )


async def test_covered_range_does_not_call_provider(session: None) -> None:
    async with SessionMaker() as s:
        await _seed_instrument(s)
        await repo.upsert_bars(s, SYMBOL, [_bar("2024-03-01", 10), _bar("2024-03-29", 11)])
        await repo.extend_coverage(s, SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        failing = FakeProvider(fail=True)
        bars = await get_kline(s, [failing], SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        assert len(bars) == 2
        assert failing.calls == 0  # 查库优先，没碰 provider


async def test_falls_back_to_secondary_when_primary_fails(session: None) -> None:
    async with SessionMaker() as s:
        await _seed_instrument(s)
        primary = FakeProvider(fail=True)
        backup = FakeProvider(bars=[_bar("2024-03-01", 10), _bar("2024-03-04", 12)])
        bars = await get_kline(s, [primary, backup], SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        assert primary.calls == 1
        assert backup.calls == 1
        assert len(bars) == 2  # 用了备源数据
        # 备源数据已入库
        assert len(await repo.get_bars(s, SYMBOL, date(2024, 3, 1), date(2024, 3, 31))) == 2


async def test_degrades_to_db_when_all_providers_fail(session: None) -> None:
    async with SessionMaker() as s:
        await _seed_instrument(s)
        await repo.upsert_bars(s, SYMBOL, [_bar("2024-03-01", 10), _bar("2024-03-29", 11)])
        await repo.extend_coverage(s, SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        # 请求到 6 月(尾部过期) + 所有源都挂 → 不应 500, 应返回库里已有
        bars = await get_kline(
            s, [FakeProvider(fail=True)], SYMBOL, date(2024, 3, 1), date(2024, 6, 30)
        )
        assert len(bars) == 2  # 库里那两根, 没抛异常


async def test_raises_when_all_fail_and_db_empty(session: None) -> None:
    async with SessionMaker() as s:
        await _seed_instrument(s)
        with pytest.raises(ProviderUnavailable):
            await get_kline(
                s, [FakeProvider(fail=True)], SYMBOL, date(2024, 3, 1), date(2024, 3, 31)
            )


async def test_empty_fetch_does_not_cache_emptiness(session: None) -> None:
    # provider 成功但返回 [] 时，不能把该区间标记为已覆盖（否则空被永久缓存、再不重抓）
    async with SessionMaker() as s:
        await _seed_instrument(s)
        empty = FakeProvider(bars=[])  # 成功返回空
        r1 = await get_kline(s, [empty], SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        assert r1 == []
        assert await repo.get_coverage(s, SYMBOL) is None  # 未标记覆盖
        # 第二次仍会再抓，而不是当成"已覆盖"
        await get_kline(s, [empty], SYMBOL, date(2024, 3, 1), date(2024, 3, 31))
        assert empty.calls == 2
