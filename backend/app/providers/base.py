"""DataProvider 抽象与标准化数据类。

所有市场/数据源实现此接口，对上层只暴露标准化结果；symbol 一律用内部规范
（见 :mod:`app.symbols`）。价格统一用 ``Decimal``，避免浮点误差污染复权/涨跌幅。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Bar:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal  # 后复权
    volume: Decimal | None  # 停牌日为 None
    amount: Decimal | None
    raw_close: Decimal  # 不复权收盘，用于换算前复权/不复权
    trade_status: int  # 1=正常, 0=停牌


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    market: str  # SH / SZ / BJ
    type: str  # stock / index
    ipo_date: date | None
    status: str  # listing / delisted


@dataclass(frozen=True)
class InstrumentDetail:
    """个股低频信息（不含逐日行情）。各源只填自己能取到的字段，缺失留 None。"""

    industry: str | None = None
    pe_ttm: float | None = None
    pb_mrq: float | None = None
    total_mv: float | None = None  # 总市值(元)
    circ_mv: float | None = None  # 流通市值(元)


class DataProvider(ABC):
    """各数据源实现此接口；symbol 用内部规范，返回标准化结果。"""

    @abstractmethod
    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        """返回标准化日线：后复权 OHLC + raw_close + trade_status，按 date 升序。"""

    @abstractmethod
    def list_instruments(self) -> list[Instrument]:
        """全市场标的列表（股票 + 指数）。"""

    @abstractmethod
    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        """交易日序列（已排除周末与节假日）。"""

    def get_instrument_detail(self, symbol: str) -> InstrumentDetail | None:
        """低频基本面；不支持的源返回 None（默认）。"""
        return None
