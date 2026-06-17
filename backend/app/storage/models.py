"""ORM 模型。日线存后复权 OHLC + 不复权 close + 停牌标记；周/月线不建表。"""

import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, SmallInteger, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WatchlistORM(Base):
    __tablename__ = "watchlist"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("instruments.symbol"), primary_key=True)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InstrumentORM(Base):
    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)  # 600519.SH
    name: Mapped[str] = mapped_column(String)
    market: Mapped[str] = mapped_column(String)  # SH / SZ / BJ
    type: Mapped[str] = mapped_column(String)  # stock / index
    ipo_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String)  # listing / delisted
    data_start: Mapped[datetime.date | None] = mapped_column(nullable=True)
    data_end: Mapped[datetime.date | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DailyBarORM(Base):
    __tablename__ = "daily_bars"

    symbol: Mapped[str] = mapped_column(ForeignKey("instruments.symbol"), primary_key=True)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    open: Mapped[Decimal] = mapped_column(Numeric)  # 后复权
    high: Mapped[Decimal] = mapped_column(Numeric)
    low: Mapped[Decimal] = mapped_column(Numeric)
    close: Mapped[Decimal] = mapped_column(Numeric)
    volume: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)  # 停牌日 NULL
    amount: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    raw_close: Mapped[Decimal] = mapped_column(Numeric)  # 不复权收盘
    trade_status: Mapped[int] = mapped_column(SmallInteger)  # 1 正常 / 0 停牌
