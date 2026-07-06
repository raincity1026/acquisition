"""备用数据源 AKShare（**走 sina 系端点**，避开易限流的 eastmoney）。

主源 Baostock 抖动/不可用时由 :mod:`app.services.market_data` 降级到这里。
- get_daily_bars: ``stock_zh_a_daily`` 取 hfq + 不复权两次再 merge。
- list_instruments: ``stock_info_a_code_name``（仅股票，无指数/ipo_date，属备源降级用）。
- get_trade_calendar: ``tool_trade_date_hist_sina``。

已知局限：sina 日线**跳过停牌日**（不像 Baostock 占位），故 trade_status 一律置 1；同一标的
今后固定单源，不与 Baostock 跨源拼接。
"""

import logging
import time
from collections.abc import Callable
from datetime import date
from decimal import Decimal

import akshare as ak
import pandas as pd

from app.symbols import to_akshare, to_akshare_daily

from .base import Bar, DataProvider, Instrument, InstrumentDetail

logger = logging.getLogger(__name__)
_RETRY_TRIES = 4


def _retry[T](op: Callable[[], T], label: str) -> T:
    """akshare 偶发连接重置/限流，递增退避重试。"""
    last: Exception | None = None
    for i in range(_RETRY_TRIES):
        try:
            return op()
        except Exception as e:  # noqa: BLE001 — 爬取型接口异常类型杂，统一重试
            last = e
            logger.warning("akshare %s 第 %d/%d 次失败: %s", label, i + 1, _RETRY_TRIES, e)
            time.sleep(1.5 * (i + 1))
    assert last is not None
    raise last


def _dec(v: object) -> Decimal | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return Decimal(str(v))


def _num(v: object) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(str(v))
    except (TypeError, ValueError):
        return None


def _market_from_code(code: str) -> str | None:
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    if code.startswith(("4", "8", "9")):
        return "BJ"
    return None


class AkshareProvider(DataProvider):
    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        sym = to_akshare_daily(symbol)
        s, e = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

        def _pull(adjust: str) -> pd.DataFrame:
            return ak.stock_zh_a_daily(symbol=sym, start_date=s, end_date=e, adjust=adjust)

        hfq = _retry(lambda: _pull("hfq"), "daily-hfq").reset_index()
        raw = _retry(lambda: _pull(""), "daily-none").reset_index()
        raw["date"] = pd.to_datetime(raw["date"]).dt.date
        raw_close_by_date = dict(zip(raw["date"], raw["close"], strict=False))

        bars: list[Bar] = []
        for row in hfq.itertuples(index=False):
            d = pd.to_datetime(row.date).date()
            close = _dec(row.close)
            rc = _dec(raw_close_by_date.get(d))
            if close is None or rc is None:
                continue
            amount = _dec(getattr(row, "amount", None))
            bars.append(
                Bar(
                    date=d,
                    open=_dec(row.open) or close,
                    high=_dec(row.high) or close,
                    low=_dec(row.low) or close,
                    close=close,
                    volume=_dec(row.volume),
                    amount=amount,
                    raw_close=rc,
                    trade_status=1,  # sina 跳过停牌日，返回的都是交易日
                )
            )
        bars.sort(key=lambda b: b.date)
        return bars

    def list_instruments(self) -> list[Instrument]:
        df = _retry(ak.stock_info_a_code_name, "code-name")
        out: list[Instrument] = []
        for row in df.itertuples(index=False):
            code = str(row.code)
            market = _market_from_code(code)
            if market is None:
                continue
            out.append(
                Instrument(
                    symbol=f"{code}.{market}",
                    name=str(row.name),
                    market=market,
                    type="stock",
                    ipo_date=None,
                    status="listing",
                )
            )
        return out

    def get_instrument_detail(self, symbol: str) -> InstrumentDetail:
        code = to_akshare(symbol)  # 纯 6 位
        df = _retry(lambda: ak.stock_individual_info_em(symbol=code), "individual-info")
        info = dict(zip(df["item"], df["value"], strict=False))
        return InstrumentDetail(
            total_mv=_num(info.get("总市值")),
            circ_mv=_num(info.get("流通市值")),
        )

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        df = _retry(ak.tool_trade_date_hist_sina, "trade-cal")
        days = pd.to_datetime(df["trade_date"]).dt.date
        return [d for d in days if start <= d <= end]
