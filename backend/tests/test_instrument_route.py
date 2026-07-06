import pytest
from httpx import ASGITransport, AsyncClient

from app.api import routes
from app.main import app
from app.services.market_data import InstrumentDetailResult, UnknownSymbol


@pytest.mark.asyncio
async def test_instrument_route_ok(monkeypatch):
    from datetime import date

    async def _fake(session, providers, symbol):
        return InstrumentDetailResult(
            symbol=symbol,
            name="贵州茅台",
            market="SH",
            type="stock",
            ipo_date=date(2001, 8, 27),
            industry="白酒",
            pe_ttm=32.5,
            pb_mrq=9.8,
            total_mv=1.98e12,
            circ_mv=1.98e12,
        )

    monkeypatch.setattr(routes, "get_instrument_detail", _fake)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/api/instrument/600519.SH")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "贵州茅台"
    assert body["industry"] == "白酒"
    assert body["total_mv"] == 1.98e12


@pytest.mark.asyncio
async def test_instrument_route_unknown(monkeypatch):
    async def _fake(session, providers, symbol):
        raise UnknownSymbol(symbol)

    monkeypatch.setattr(routes, "get_instrument_detail", _fake)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/api/instrument/000000.SH")
    assert r.status_code == 404
