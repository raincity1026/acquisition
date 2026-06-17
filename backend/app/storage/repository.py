"""入库 / 查询。ORM ⇄ 标准数据类（Bar / Instrument）的转换都收敛在这里。"""

from datetime import date
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import Bar, Instrument

from .models import DailyBarORM, InstrumentORM, UserORM, WatchlistORM


# asyncpg 单条语句参数上限 32767；按 列数 切块，留余量。
def _chunks(values: list[dict[str, Any]], cols: int) -> list[list[dict[str, Any]]]:
    size = max(1, 30000 // cols)
    return [values[i : i + size] for i in range(0, len(values), size)]


def _to_instrument(row: InstrumentORM) -> Instrument:
    return Instrument(
        symbol=row.symbol,
        name=row.name,
        market=row.market,
        type=row.type,
        ipo_date=row.ipo_date,
        status=row.status,
    )


def _to_bar(row: DailyBarORM) -> Bar:
    return Bar(
        date=row.date,
        open=row.open,
        high=row.high,
        low=row.low,
        close=row.close,
        volume=row.volume,
        amount=row.amount,
        raw_close=row.raw_close,
        trade_status=row.trade_status,
    )


async def upsert_instruments(session: AsyncSession, items: list[Instrument]) -> None:
    if not items:
        return
    values = [
        {
            "symbol": i.symbol,
            "name": i.name,
            "market": i.market,
            "type": i.type,
            "ipo_date": i.ipo_date,
            "status": i.status,
        }
        for i in items
    ]
    for chunk in _chunks(values, cols=6):
        stmt = insert(InstrumentORM).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "name": stmt.excluded.name,
                "market": stmt.excluded.market,
                "type": stmt.excluded.type,
                "ipo_date": stmt.excluded.ipo_date,
                "status": stmt.excluded.status,
            },
        )
        await session.execute(stmt)
    await session.commit()


async def count_instruments(session: AsyncSession) -> int:
    result = await session.scalar(select(func.count()).select_from(InstrumentORM))
    return result or 0


async def get_instrument(session: AsyncSession, symbol: str) -> Instrument | None:
    row = await session.get(InstrumentORM, symbol)
    return _to_instrument(row) if row else None


async def search_instruments(session: AsyncSession, q: str, limit: int = 20) -> list[Instrument]:
    pattern = f"%{q}%"
    stmt = (
        select(InstrumentORM)
        .where(or_(InstrumentORM.symbol.ilike(pattern), InstrumentORM.name.ilike(pattern)))
        .order_by(InstrumentORM.symbol)
        .limit(limit)
    )
    rows = (await session.scalars(stmt)).all()
    return [_to_instrument(r) for r in rows]


async def upsert_bars(session: AsyncSession, symbol: str, bars: list[Bar]) -> None:
    if not bars:
        return
    values = [
        {
            "symbol": symbol,
            "date": b.date,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "amount": b.amount,
            "raw_close": b.raw_close,
            "trade_status": b.trade_status,
        }
        for b in bars
    ]
    for chunk in _chunks(values, cols=10):
        stmt = insert(DailyBarORM).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "amount": stmt.excluded.amount,
                "raw_close": stmt.excluded.raw_close,
                "trade_status": stmt.excluded.trade_status,
            },
        )
        await session.execute(stmt)
    await session.commit()


async def extend_coverage(session: AsyncSession, symbol: str, start: date, end: date) -> None:
    """把本次抓取的**请求区间** [start,end] 并入 instruments 的已覆盖区间。

    用请求区间而非实际 bar 的 min/max：节假日/停牌/未上市会让首个 bar 晚于请求 start，
    若按实际 min 记录，下次同样请求会判定未覆盖而反复抓取。
    """
    await session.execute(
        update(InstrumentORM)
        .where(InstrumentORM.symbol == symbol)
        .values(
            data_start=func.least(func.coalesce(InstrumentORM.data_start, start), start),
            data_end=func.greatest(func.coalesce(InstrumentORM.data_end, end), end),
        )
    )
    await session.commit()


async def get_bars(session: AsyncSession, symbol: str, start: date, end: date) -> list[Bar]:
    stmt = (
        select(DailyBarORM)
        .where(
            DailyBarORM.symbol == symbol,
            DailyBarORM.date >= start,
            DailyBarORM.date <= end,
        )
        .order_by(DailyBarORM.date)
    )
    rows = (await session.scalars(stmt)).all()
    return [_to_bar(r) for r in rows]


async def get_coverage(session: AsyncSession, symbol: str) -> tuple[date, date] | None:
    row = await session.get(InstrumentORM, symbol)
    if row is None or row.data_start is None or row.data_end is None:
        return None
    return (row.data_start, row.data_end)


async def list_covered_symbols(session: AsyncSession) -> list[tuple[str, date]]:
    """已入库（coverage 非空）的标的及其 data_end，供盘后增量更新遍历。"""
    stmt = select(InstrumentORM.symbol, InstrumentORM.data_end).where(
        InstrumentORM.data_end.is_not(None)
    )
    return [(r[0], r[1]) for r in (await session.execute(stmt)).all()]


# ---------- 用户 ----------
async def create_user(session: AsyncSession, email: str, password_hash: str) -> int:
    user = UserORM(email=email, password_hash=password_hash)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id


async def get_user_auth_by_email(session: AsyncSession, email: str) -> tuple[int, str] | None:
    row = (
        await session.execute(select(UserORM).where(UserORM.email == email))
    ).scalar_one_or_none()
    return (row.id, row.password_hash) if row else None


async def get_user_email(session: AsyncSession, user_id: int) -> str | None:
    row = await session.get(UserORM, user_id)
    return row.email if row else None


# ---------- 自选 ----------
async def add_watch(session: AsyncSession, user_id: int, symbol: str) -> None:
    stmt = (
        insert(WatchlistORM)
        .values(user_id=user_id, symbol=symbol)
        .on_conflict_do_nothing(index_elements=["user_id", "symbol"])
    )
    await session.execute(stmt)
    await session.commit()


async def remove_watch(session: AsyncSession, user_id: int, symbol: str) -> None:
    await session.execute(
        delete(WatchlistORM).where(WatchlistORM.user_id == user_id, WatchlistORM.symbol == symbol)
    )
    await session.commit()


async def list_watch_symbols(session: AsyncSession, user_id: int) -> list[str]:
    stmt = (
        select(WatchlistORM.symbol)
        .where(WatchlistORM.user_id == user_id)
        .order_by(WatchlistORM.added_at)
    )
    return list((await session.scalars(stmt)).all())


async def latest_quote(session: AsyncSession, symbol: str) -> tuple[date, float, float] | None:
    """最新两根不复权收盘，用于自选列表的最新价 + 当日涨跌幅。"""
    stmt = (
        select(DailyBarORM.date, DailyBarORM.raw_close)
        .where(DailyBarORM.symbol == symbol, DailyBarORM.trade_status == 1)
        .order_by(DailyBarORM.date.desc())
        .limit(2)
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return None
    last_date, last_close = rows[0]
    prev_close = rows[1][1] if len(rows) > 1 else last_close
    return (last_date, float(last_close), float(prev_close))
