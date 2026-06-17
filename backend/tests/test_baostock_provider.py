from datetime import date

import pytest

from app.providers.baostock_provider import BaostockProvider

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def provider() -> BaostockProvider:
    return BaostockProvider()


def test_get_daily_bars_maotai(provider: BaostockProvider) -> None:
    bars = provider.get_daily_bars("600519.SH", date(2024, 6, 1), date(2024, 6, 30))
    assert len(bars) > 10
    # 升序
    assert [b.date for b in bars] == sorted(b.date for b in bars)
    # 字段完整 + 后复权与不复权不同(茅台 hfq 远大于真实价)
    b = bars[-1]
    assert b.close > b.raw_close
    assert b.trade_status in (0, 1)
    assert b.volume is not None


def test_list_instruments_has_maotai_and_index(provider: BaostockProvider) -> None:
    items = provider.list_instruments()
    assert len(items) > 4000
    by_symbol = {i.symbol: i for i in items}
    assert "600519.SH" in by_symbol
    assert by_symbol["600519.SH"].type == "stock"
    assert "000300.SH" in by_symbol  # 沪深300 指数
    assert by_symbol["000300.SH"].type == "index"


def test_get_trade_calendar_excludes_weekend(provider: BaostockProvider) -> None:
    days = provider.get_trade_calendar(date(2026, 1, 1), date(2026, 1, 31))
    assert all(d.weekday() < 5 for d in days)
    assert 15 <= len(days) <= 23
