"""按需加载编排：查库优先 → 缺失/过期才抓取 → 复权换算 → 周/月聚合 → 返回。

容错（应对 baostock 网络抖动如 10002007）：
- 多源链 ``providers``（主 Baostock，备 AKShare）；逐个尝试，单源自身已带重试。
- 抓取全部失败时**降级读库**：库里已有该区间数据就返回（可能略旧），绝不因抓取失败而 500。
- 只有"所有源都失败且库里也没有任何可用数据"才抛 :class:`ProviderUnavailable`。

Baostock/AKShare 都是阻塞式同步库，统一用 ``asyncio.to_thread`` 丢线程池。
"""

import asyncio
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.adjust import apply_adjust
from app.core.align import align
from app.core.normalize import default_base_date, normalize
from app.core.resample import resample
from app.providers.base import Bar, DataProvider, Instrument
from app.storage import repository as repo

logger = logging.getLogger(__name__)

MAX_COMPARE_SYMBOLS = 8


class UnknownSymbol(Exception):
    """库中无此标的，且全市场列表里也找不到。"""


class ProviderUnavailable(Exception):
    """所有数据源都失败，且库里也没有可用数据可降级。"""


class _AllProvidersFailed(Exception):
    """内部：provider 链全部失败（用于触发降级读库）。"""


async def _with_fallback[T](
    providers: Sequence[DataProvider], op: Callable[[DataProvider], T]
) -> T:
    """按顺序尝试各 provider，返回首个成功结果；全失败抛 _AllProvidersFailed。"""
    last: Exception | None = None
    for p in providers:
        try:
            return await asyncio.to_thread(op, p)
        except Exception as e:  # noqa: BLE001 — 主备切换需吞掉单源异常
            last = e
            logger.warning("provider %s 失败，尝试下一个备源: %s", type(p).__name__, e)
    raise _AllProvidersFailed from last


async def _ensure_instrument(
    session: AsyncSession, providers: Sequence[DataProvider], symbol: str
) -> None:
    if await repo.get_instrument(session, symbol) is not None:
        return
    # 首次遇到未知标的且标的表为空 → 懒加载全市场列表(只做一次)
    if await repo.count_instruments(session) == 0:
        try:
            items: list[Instrument] = await _with_fallback(
                providers, lambda p: p.list_instruments()
            )
            await repo.upsert_instruments(session, items)
        except _AllProvidersFailed:
            logger.warning("标的列表全部源拉取失败，跳过预加载")
    if await repo.get_instrument(session, symbol) is None:
        raise UnknownSymbol(symbol)


def _covered(coverage: tuple[date, date] | None, start: date, end: date) -> bool:
    return coverage is not None and coverage[0] <= start and coverage[1] >= end


def _fetch_start(coverage: tuple[date, date] | None, start: date) -> date:
    """已覆盖到请求起点时只补尾部（缩小对抖动数据源的暴露面）；否则抓整段。"""
    if coverage is not None and coverage[0] <= start <= coverage[1]:
        return coverage[1] + timedelta(days=1)
    return start


async def get_kline(
    session: AsyncSession,
    providers: Sequence[DataProvider],
    symbol: str,
    start: date,
    end: date,
    period: str = "d",
    adjust: str = "hfq",
) -> list[Bar]:
    await _ensure_instrument(session, providers, symbol)

    # 1) 查库优先：已覆盖请求区间就完全不碰 provider
    coverage = await repo.get_coverage(session, symbol)
    if not _covered(coverage, start, end):
        fetch_start = _fetch_start(coverage, start)
        try:
            fetched = await _with_fallback(
                providers, lambda p: p.get_daily_bars(symbol, fetch_start, end)
            )
        except _AllProvidersFailed as exc:
            # 2) 降级读库：抓取失败但库里已有该区间数据 → 返回(可能略旧)，不 500
            if not await repo.get_bars(session, symbol, start, end):
                raise ProviderUnavailable(symbol) from exc
            logger.warning("所有源抓取失败，降级返回库内已有数据: %s", symbol)
        else:
            # 仅在确有数据时入库并标记覆盖；空返回不标记，否则会把"空"永久缓存住
            if fetched:
                await repo.upsert_bars(session, symbol, fetched)
                await repo.extend_coverage(session, symbol, fetch_start, end)
            else:
                logger.warning("数据源返回空，不标记覆盖（下次仍会重试）: %s", symbol)

    # 3) 取后复权日线
    bars = await repo.get_bars(session, symbol, start, end)

    # 4) 周/月聚合(在后复权上做，raw_close 透传，聚合后仍可换算)
    if period in ("w", "m"):
        bars = resample(bars, period.upper())

    # 5) 复权口径换算
    return apply_adjust(bars, adjust)


@dataclass
class CompareSeries:
    symbol: str
    name: str
    values: list[float | None]
    latest_pct: float | None


@dataclass
class CompareResult:
    base_date: date
    dates: list[date]
    series: list[CompareSeries]


async def compare(
    session: AsyncSession,
    providers: Sequence[DataProvider],
    symbols: list[str],
    base_date: date | None,
    start: date,
    end: date,
) -> CompareResult:
    """多股归一化对比：各取后复权日线 → 对齐统一交易日轴 → 以基准日算累计涨跌幅。"""
    if not 1 <= len(symbols) <= MAX_COMPARE_SYMBOLS:
        raise ValueError(f"对比标的数应为 1–{MAX_COMPARE_SYMBOLS} 只")

    bars_by_symbol: dict[str, list[Bar]] = {}
    names: dict[str, str] = {}
    for sym in symbols:
        bars_by_symbol[sym] = await get_kline(session, providers, sym, start, end, "d", "hfq")
        inst = await repo.get_instrument(session, sym)
        names[sym] = inst.name if inst else sym

    # 统一交易日轴 = 所有标的出现过的交易日并集（含指数即等价于 A 股日历，且无需触网）
    all_dates = sorted({b.date for bars in bars_by_symbol.values() for b in bars})
    if not all_dates:
        raise ProviderUnavailable(",".join(symbols))

    aligned = align(bars_by_symbol, all_dates)
    base = base_date or default_base_date(aligned, all_dates) or all_dates[0]
    norm = normalize(aligned, all_dates, base)
    # 实际生效基准日（snap 到 >= base 的首个交易日）
    actual_base = next((d for d in all_dates if d >= base), all_dates[0])

    return CompareResult(
        base_date=actual_base,
        dates=all_dates,
        series=[
            CompareSeries(sym, names[sym], norm[sym].values, norm[sym].latest_pct)
            for sym in symbols
        ],
    )
