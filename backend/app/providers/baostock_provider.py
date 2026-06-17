"""主数据源 Baostock 的 DataProvider 实现。

要点（焊入 spike 结论）：
- 后复权(adjustflag=1) 与 不复权(adjustflag=3) **两次查询再按 date merge**，因为单次只能取
  一种复权口径。
- ``tradestatus`` 直接映射 ``trade_status``（1 正常 / 0 停牌）；停牌占位行 volume 为空 → None。
- 复权标志显式指定，绝不用默认。代码格式转换走 :mod:`app.symbols`。
"""

import contextlib
import logging
import time
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal

import baostock as bs  # pandas 垫片在 app.providers.__init__ 已先行

from app.symbols import from_baostock, market_of, to_baostock

from .base import Bar, DataProvider, Instrument

logger = logging.getLogger(__name__)
_KLINE_FIELDS = "date,open,high,low,close,volume,amount,tradestatus"
_RETRY_TRIES = 3


def _retry[T](op: Callable[[], T]) -> T:
    """baostock 网络抖动(如 10002007 网络接收错误)/登录失败时重试，递增退避。"""
    last: Exception | None = None
    for i in range(_RETRY_TRIES):
        try:
            return op()
        except RuntimeError as e:
            last = e
            logger.warning("baostock 第 %d/%d 次失败，重试: %s", i + 1, _RETRY_TRIES, e)
            time.sleep(1.0 * (i + 1))
    assert last is not None
    raise last


@contextlib.contextmanager
def _session() -> Iterator[None]:
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock 登录失败: {lg.error_code} {lg.error_msg}")
    try:
        yield
    finally:
        bs.logout()


def _dec(s: str) -> Decimal | None:
    s = s.strip()
    return Decimal(s) if s else None


def _rows(rs: object) -> list[list[str]]:
    if rs.error_code != "0":  # type: ignore[attr-defined]
        raise RuntimeError(f"baostock 查询失败: {rs.error_code} {rs.error_msg}")  # type: ignore[attr-defined]
    out: list[list[str]] = []
    while rs.next():  # type: ignore[attr-defined]
        out.append(rs.get_row_data())  # type: ignore[attr-defined]
    return out


class BaostockProvider(DataProvider):
    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        code = to_baostock(symbol)
        s, e = start.isoformat(), end.isoformat()

        def _fetch() -> tuple[list[list[str]], list[list[str]]]:
            with _session():
                hfq = _rows(
                    bs.query_history_k_data_plus(
                        code, _KLINE_FIELDS, start_date=s, end_date=e, frequency="d", adjustflag="1"
                    )
                )
                raw = _rows(
                    bs.query_history_k_data_plus(
                        code, "date,close", start_date=s, end_date=e, frequency="d", adjustflag="3"
                    )
                )
            return hfq, raw

        hfq, raw = _retry(_fetch)
        raw_close_by_date = {r[0]: r[1] for r in raw}
        bars: list[Bar] = []
        for d, o, h, low, c, vol, amt, status in hfq:
            rc = _dec(raw_close_by_date.get(d, ""))
            close = _dec(c)
            if close is None or rc is None:
                continue  # 无收盘的异常行跳过
            bars.append(
                Bar(
                    date=date.fromisoformat(d),
                    open=_dec(o) or close,
                    high=_dec(h) or close,
                    low=_dec(low) or close,
                    close=close,
                    volume=_dec(vol),
                    amount=_dec(amt),
                    raw_close=rc,
                    trade_status=int(status) if status.strip() else 0,
                )
            )
        bars.sort(key=lambda b: b.date)
        return bars

    def list_instruments(self) -> list[Instrument]:
        def _fetch() -> list[list[str]]:
            with _session():
                return _rows(bs.query_stock_basic())

        rows = _retry(_fetch)
        # 列: code, code_name, ipoDate, outDate, type, status
        out: list[Instrument] = []
        for code, name, ipo, _out, typ, status in rows:
            kind = {"1": "stock", "2": "index"}.get(typ)
            if kind is None:  # 跳过其它(可转债/ETF 等)
                continue
            try:
                symbol = from_baostock(code)
            except ValueError:
                continue
            out.append(
                Instrument(
                    symbol=symbol,
                    name=name,
                    market=market_of(symbol),
                    type=kind,
                    ipo_date=date.fromisoformat(ipo) if ipo.strip() else None,
                    status="listing" if status.strip() == "1" else "delisted",
                )
            )
        return out

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        def _fetch() -> list[list[str]]:
            with _session():
                return _rows(
                    bs.query_trade_dates(start_date=start.isoformat(), end_date=end.isoformat())
                )

        rows = _retry(_fetch)
        # 列: calendar_date, is_trading_day
        return [date.fromisoformat(d) for d, is_open in rows if is_open.strip() == "1"]
