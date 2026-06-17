"""盘后自动更新（真实 test 库 + 假 provider，不触网）。"""

from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.providers.base import Bar, DataProvider, Instrument
from app.services.updater import run_daily_update
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

A, B = "600519.SH", "000858.SZ"
TODAY = date(2024, 3, 15)


def _bar(d: date, c: float) -> Bar:
    v = Decimal(str(c))
    return Bar(d, v, v, v, v, Decimal("1"), Decimal("1"), v, 1)


class FakeProvider(DataProvider):
    def __init__(self, trading: bool = True, fail: set[str] | None = None) -> None:
        self.trading = trading
        self.fail = fail or set()

    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        if symbol in self.fail:
            raise RuntimeError("10002007 网络接收错误")
        return [_bar(TODAY, 100)]  # 新增最新一天

    def list_instruments(self) -> list[Instrument]:
        return []

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        return [TODAY] if self.trading else []


@pytest.fixture
async def clean() -> AsyncIterator[None]:
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE daily_bars, instruments RESTART IDENTITY CASCADE"))
    async with SessionMaker() as s:
        await repo.upsert_instruments(
            s,
            [
                Instrument(A, "贵州茅台", "SH", "stock", None, "listing"),
                Instrument(B, "五粮液", "SZ", "stock", None, "listing"),
            ],
        )
        for sym in (A, B):
            await repo.upsert_bars(s, sym, [_bar(date(2024, 3, 8), 90)])
            await repo.extend_coverage(s, sym, date(2024, 1, 1), date(2024, 3, 10))
    yield
    await engine.dispose()


async def test_update_advances_coverage_to_today(clean: None) -> None:
    res = await run_daily_update([FakeProvider(trading=True)], TODAY)
    assert res.ran and res.updated == 2 and res.failed == []
    async with SessionMaker() as s:
        assert (await repo.get_coverage(s, A))[1] == TODAY  # 覆盖推进到最新
        assert any(b.date == TODAY for b in await repo.get_bars(s, A, TODAY, TODAY))


async def test_one_failure_does_not_block_others(clean: None) -> None:
    res = await run_daily_update([FakeProvider(trading=True, fail={B})], TODAY)
    assert res.ran and res.updated == 1 and res.failed == [B]
    async with SessionMaker() as s:
        assert (await repo.get_coverage(s, A))[1] == TODAY  # A 仍更新
        assert (await repo.get_coverage(s, B))[1] == date(2024, 3, 10)  # B 未变


async def test_non_trading_day_skips(clean: None) -> None:
    res = await run_daily_update([FakeProvider(trading=False)], TODAY)
    assert res.ran is False and res.updated == 0
