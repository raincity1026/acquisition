"""FastAPI 路由。GET /api/kline（单股, M0）、/api/search、/api/compare（多股归一化, M2）。"""

from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.akshare_provider import AkshareProvider
from app.providers.baostock_provider import BaostockProvider
from app.providers.base import Bar, DataProvider
from app.services.market_data import (
    ProviderUnavailable,
    UnknownSymbol,
    compare,
    get_kline,
)
from app.storage import repository as repo
from app.storage.database import get_session

router = APIRouter(prefix="/api")

# 主源 Baostock，备源 AKShare(sina)。主源抖动时服务层自动降级。
_providers: list[DataProvider] = [BaostockProvider(), AkshareProvider()]


def get_providers() -> list[DataProvider]:
    return _providers


class KlineBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    amount: float | None
    trade_status: int


class InstrumentOut(BaseModel):
    symbol: str
    name: str
    market: str
    type: str


def _to_out(b: Bar) -> KlineBar:
    return KlineBar(
        date=b.date,
        open=float(b.open),
        high=float(b.high),
        low=float(b.low),
        close=float(b.close),
        volume=None if b.volume is None else float(b.volume),
        amount=None if b.amount is None else float(b.amount),
        trade_status=b.trade_status,
    )


@router.get("/kline", response_model=list[KlineBar])
async def kline(
    session: Annotated[AsyncSession, Depends(get_session)],
    providers: Annotated[list[DataProvider], Depends(get_providers)],
    symbol: str,
    period: Literal["d", "w", "m"] = "d",
    adjust: Literal["hfq", "qfq", "none"] = "hfq",
    start: date | None = None,
    end: date | None = None,
) -> list[KlineBar]:
    end = end or date.today()
    start = start or (end - timedelta(days=730))  # 默认近 2 年
    try:
        bars = await get_kline(session, providers, symbol, start, end, period, adjust)
    except UnknownSymbol as exc:
        raise HTTPException(status_code=404, detail=f"未知标的: {exc}") from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"数据源暂不可用且库中无数据: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_to_out(b) for b in bars]


@router.get("/search", response_model=list[InstrumentOut])
async def search(
    session: Annotated[AsyncSession, Depends(get_session)],
    q: Annotated[str, Query(min_length=1)],
    limit: int = 20,
) -> list[InstrumentOut]:
    items = await repo.search_instruments(session, q, limit)
    return [
        InstrumentOut(symbol=i.symbol, name=i.name, market=i.market, type=i.type) for i in items
    ]


class CompareSeriesOut(BaseModel):
    symbol: str
    name: str
    values: list[float | None]  # 累计涨跌幅(%)，与 dates 对齐，基准日=0、之前/未上市=null
    latest_pct: float | None


class CompareOut(BaseModel):
    base_date: date
    dates: list[date]
    series: list[CompareSeriesOut]


@router.get("/compare", response_model=CompareOut)
async def compare_route(
    session: Annotated[AsyncSession, Depends(get_session)],
    providers: Annotated[list[DataProvider], Depends(get_providers)],
    symbols: Annotated[str, Query(description="逗号分隔，如 600519.SH,000858.SZ,000300.SH")],
    base_date: date | None = None,
    start: date | None = None,
    end: date | None = None,
) -> CompareOut:
    syms = [s.strip() for s in symbols.split(",") if s.strip()]
    end = end or date.today()
    start = start or (end - timedelta(days=730))
    try:
        result = await compare(session, providers, syms, base_date, start, end)
    except UnknownSymbol as exc:
        raise HTTPException(status_code=404, detail=f"未知标的: {exc}") from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"数据源暂不可用且库中无数据: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CompareOut(
        base_date=result.base_date,
        dates=result.dates,
        series=[
            CompareSeriesOut(symbol=s.symbol, name=s.name, values=s.values, latest_pct=s.latest_pct)
            for s in result.series
        ],
    )
