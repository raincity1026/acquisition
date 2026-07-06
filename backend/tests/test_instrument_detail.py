import pytest

from app.providers.base import DataProvider, Instrument, InstrumentDetail
from app.services import market_data as md
from app.services.market_data import UnknownSymbol, get_instrument_detail


class _Fake(DataProvider):
    def __init__(self, detail: InstrumentDetail | None) -> None:
        self._detail = detail

    def get_daily_bars(self, symbol, start, end):  # type: ignore[override]
        return []

    def list_instruments(self):  # type: ignore[override]
        return []

    def get_trade_calendar(self, start, end):  # type: ignore[override]
        return []

    def get_instrument_detail(self, symbol):  # type: ignore[override]
        return self._detail


@pytest.fixture
def patch_instrument(monkeypatch):
    from datetime import date

    inst = Instrument(
        symbol="600519.SH",
        name="贵州茅台",
        market="SH",
        type="stock",
        ipo_date=date(2001, 8, 27),
        status="listing",
    )

    async def _ensure(session, providers, symbol):
        if symbol != "600519.SH":
            raise UnknownSymbol(symbol)

    async def _get(session, symbol):
        return inst if symbol == "600519.SH" else None

    monkeypatch.setattr(md, "_ensure_instrument", _ensure)
    monkeypatch.setattr(md.repo, "get_instrument", _get)
    return inst


@pytest.mark.asyncio
async def test_merge_primary_wins_and_backup_fills(patch_instrument):
    primary = _Fake(InstrumentDetail(industry="白酒", pe_ttm=32.5, pb_mrq=9.8))
    backup = _Fake(InstrumentDetail(industry="酒", total_mv=1.98e12, circ_mv=1.98e12))
    r = await get_instrument_detail(None, [primary, backup], "600519.SH")
    assert r.name == "贵州茅台"
    assert r.industry == "白酒"  # 主源优先
    assert r.pe_ttm == 32.5
    assert r.total_mv == 1.98e12  # 备源补


@pytest.mark.asyncio
async def test_source_exception_is_not_fatal(patch_instrument):
    class _Boom(_Fake):
        def get_instrument_detail(self, symbol):
            raise RuntimeError("boom")

    providers = [_Boom(None), _Fake(InstrumentDetail(pe_ttm=10.0))]
    r = await get_instrument_detail(None, providers, "600519.SH")
    assert r.pe_ttm == 10.0


@pytest.mark.asyncio
async def test_unknown_symbol_raises(patch_instrument):
    with pytest.raises(UnknownSymbol):
        await get_instrument_detail(None, [_Fake(None)], "000000.SH")
