"""账号 + 自选 服务。

隔离边界（设计规格 §3）：users / watchlist 按用户隔离；instruments / daily_bars 全局共享。
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import DataProvider
from app.security import create_access_token, hash_password, verify_password
from app.storage import repository as repo
from app.storage.database import SessionMaker

from .market_data import get_kline

logger = logging.getLogger(__name__)


class EmailTaken(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class GroupNameTaken(Exception):
    pass


class GroupNotFound(Exception):
    pass


class SymbolNotWatched(Exception):
    pass


@dataclass
class WatchItem:
    symbol: str
    name: str
    last_close: float | None
    change_pct: float | None  # 当日涨跌幅(%)
    date: date | None
    group_ids: list[int]  # 所属分组（空=未分组=默认分组）


async def register(session: AsyncSession, email: str, password: str) -> str:
    if await repo.get_user_auth_by_email(session, email) is not None:
        raise EmailTaken(email)
    user_id = await repo.create_user(session, email, hash_password(password))
    return create_access_token(user_id)


async def login(session: AsyncSession, email: str, password: str) -> str:
    rec = await repo.get_user_auth_by_email(session, email)
    if rec is None or not verify_password(password, rec[1]):
        raise InvalidCredentials(email)
    return create_access_token(rec[0])


async def get_watchlist(session: AsyncSession, user_id: int) -> list[WatchItem]:
    symbols = await repo.list_watch_symbols(session, user_id)
    groups_of = await repo.group_ids_by_symbol(session, user_id, symbols)
    items: list[WatchItem] = []
    for sym in symbols:
        inst = await repo.get_instrument(session, sym)
        name = inst.name if inst else sym
        gids = groups_of.get(sym, [])
        quote = await repo.latest_quote(session, sym)
        if quote is None:
            items.append(WatchItem(sym, name, None, None, None, gids))
        else:
            d, last, prev = quote
            pct = round((last / prev - 1) * 100, 2) if prev else 0.0
            items.append(WatchItem(sym, name, last, pct, d, gids))
    return items


# ---------- 分组 ----------
async def list_groups(session: AsyncSession, user_id: int) -> list[tuple[int, str]]:
    return await repo.list_groups(session, user_id)


async def create_group(session: AsyncSession, user_id: int, name: str) -> tuple[int, str]:
    name = name.strip()
    if not name:
        raise ValueError("分组名不能为空")
    if await repo.group_name_exists(session, user_id, name):
        raise GroupNameTaken(name)
    group_id = await repo.create_group(session, user_id, name)
    return (group_id, name)


async def rename_group(session: AsyncSession, user_id: int, group_id: int, name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("分组名不能为空")
    if await repo.get_group_owner(session, group_id) != user_id:
        raise GroupNotFound(group_id)
    if await repo.group_name_exists(session, user_id, name, exclude_id=group_id):
        raise GroupNameTaken(name)
    await repo.rename_group(session, group_id, name)


async def delete_group(session: AsyncSession, user_id: int, group_id: int) -> None:
    if await repo.get_group_owner(session, group_id) != user_id:
        raise GroupNotFound(group_id)
    await repo.delete_group(session, group_id)  # 成员级联清空 → 回默认分组


async def set_symbol_groups(
    session: AsyncSession, user_id: int, symbol: str, group_ids: list[int]
) -> None:
    if symbol not in await repo.list_watch_symbols(session, user_id):
        raise SymbolNotWatched(symbol)
    await repo.set_member_groups(session, user_id, symbol, group_ids)


async def prefetch_symbol(providers: Sequence[DataProvider], symbol: str) -> None:
    """加自选后异步把该股行情抓进库，让列表能显示最新价/涨跌幅。失败不影响加自选。"""
    end = date.today()
    start = end - timedelta(days=730)
    try:
        async with SessionMaker() as session:
            await get_kline(session, providers, symbol, start, end, "d", "hfq")
    except Exception as exc:  # noqa: BLE001 — 后台任务，吞掉异常只记录
        logger.warning("自选 %s 预抓取失败（不影响加自选）: %s", symbol, exc)
