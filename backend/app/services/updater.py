"""盘后自动更新：交易日盘后，把所有已入库标的增量刷新到最新。

要点（设计规格 §2）：
- 仅交易日执行（用交易日历判断）。
- 遍历**所有已入库**标的（coverage 非空），不是某用户自选——行情全局共享。
- 增量从 ``data_end - OVERLAP_DAYS`` 重叠拉，覆盖更新，防数据源对近期数据做修正。
- 单只失败隔离：记录并继续，失败的票下次再试；每只独立 session、独立提交。
- 容错沿用主备链（baostock 重试→AKShare 降级）。
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from app.providers.base import DataProvider
from app.storage import repository as repo
from app.storage.database import SessionMaker

from .market_data import _AllProvidersFailed, _with_fallback

logger = logging.getLogger(__name__)

OVERLAP_DAYS = 5


@dataclass
class UpdateResult:
    ran: bool  # 是否真的跑了(非交易日为 False)
    updated: int
    failed: list[str]


async def _is_trading_day(providers: Sequence[DataProvider], day: date) -> bool:
    try:
        days = await _with_fallback(providers, lambda p: p.get_trade_calendar(day, day))
    except _AllProvidersFailed:
        # 拿不到日历就别漏跑：宁可跑（非交易日每只只是空抓，无副作用）
        logger.warning("交易日历获取失败，按交易日处理继续更新")
        return True
    return day in days


async def update_one(
    providers: Sequence[DataProvider], symbol: str, data_end: date, today: date
) -> int:
    """单只增量刷新（独立 session）。返回写入的行数。"""
    fetch_start = data_end - timedelta(days=OVERLAP_DAYS)
    fetched = await _with_fallback(
        providers, lambda p: p.get_daily_bars(symbol, fetch_start, today)
    )
    if not fetched:
        return 0
    async with SessionMaker() as session:
        await repo.upsert_bars(session, symbol, fetched)
        await repo.extend_coverage(session, symbol, fetch_start, today)
    return len(fetched)


async def run_daily_update(providers: Sequence[DataProvider], today: date) -> UpdateResult:
    if not await _is_trading_day(providers, today):
        logger.info("非交易日 %s，跳过盘后更新", today)
        return UpdateResult(ran=False, updated=0, failed=[])

    async with SessionMaker() as session:
        covered = await repo.list_covered_symbols(session)

    updated = 0
    failed: list[str] = []
    for symbol, data_end in covered:
        try:
            await update_one(providers, symbol, data_end, today)
            updated += 1
        except Exception as exc:  # noqa: BLE001 — 单只失败隔离，继续跑
            logger.warning("盘后更新 %s 失败（跳过，下次重试）: %s", symbol, exc)
            failed.append(symbol)

    logger.info("盘后更新完成 %s：成功 %d，失败 %d", today, updated, len(failed))
    return UpdateResult(ran=True, updated=updated, failed=failed)
