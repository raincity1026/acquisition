"""compare 服务的端到端（真实 PostgreSQL，数据预置在库，provider 不参与）。"""

from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.providers.base import Bar, DataProvider, Instrument
from app.services.market_data import compare
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

A, B = "600519.SH", "000858.SZ"
D = [date(2024, 1, d) for d in (2, 3, 4)]


def _bar(d: date, close: float) -> Bar:
    v = Decimal(str(close))
    return Bar(d, v, v, v, v, Decimal("1"), Decimal("1"), v, 1)


class _UnusedProvider(DataProvider):
    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        raise AssertionError("库已覆盖，不应触发抓取")

    def list_instruments(self) -> list[Instrument]:
        return []

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        return []


@pytest.fixture
async def clean() -> AsyncIterator[None]:
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE daily_bars, instruments RESTART IDENTITY CASCADE"))
    yield
    await engine.dispose()


async def test_compare_normalizes_to_common_base(clean: None) -> None:
    async with SessionMaker() as s:
        await repo.upsert_instruments(
            s,
            [
                Instrument(A, "贵州茅台", "SH", "stock", None, "listing"),
                Instrument(B, "五粮液", "SZ", "stock", None, "listing"),
            ],
        )
        # 量纲悬殊：A ~100、B ~10，但都 +10% 再 +20%
        await repo.upsert_bars(s, A, [_bar(D[0], 100), _bar(D[1], 110), _bar(D[2], 120)])
        await repo.extend_coverage(s, A, D[0], D[2])
        await repo.upsert_bars(s, B, [_bar(D[0], 10), _bar(D[1], 11), _bar(D[2], 12)])
        await repo.extend_coverage(s, B, D[0], D[2])

        result = await compare(s, [_UnusedProvider()], [A, B], None, D[0], D[2])

        assert result.base_date == D[0]
        assert result.dates == D
        by = {x.symbol: x for x in result.series}
        # 归一化生效：量纲悬殊但曲线一致
        assert by[A].values == [0.0, 10.0, 20.0]
        assert by[B].values == [0.0, 10.0, 20.0]
        assert by[A].latest_pct == 20.0
        assert by[A].name == "贵州茅台"
