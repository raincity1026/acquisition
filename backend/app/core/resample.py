"""日线 → 周/月线聚合。周/月线不入库，查询时实时聚合。

规则：open=组内首开、high=组内最高、low=组内最低、close=组内末收、volume/amount 求和。
停牌日（trade_status=0）不参与，避免占位价污染 high/low；若整组全停牌则退化为用全部。
``raw_close`` 取组内最后一个正常日，使聚合后仍可做前复权/不复权换算。
"""

from datetime import date
from decimal import Decimal
from itertools import groupby

from app.providers.base import Bar


def _period_key(d: date, period: str) -> tuple[int, int]:
    if period == "W":
        iso = d.isocalendar()
        return (iso.year, iso.week)
    if period == "M":
        return (d.year, d.month)
    raise ValueError(f"未知聚合周期: {period!r}（应为 W/M）")


def _sum_opt(values: list[Decimal | None]) -> Decimal | None:
    present = [v for v in values if v is not None]
    return sum(present, Decimal(0)) if present else None


def resample(daily: list[Bar], period: str) -> list[Bar]:
    if period not in ("W", "M"):
        raise ValueError(f"未知聚合周期: {period!r}（应为 W/M）")
    if not daily:
        return []

    out: list[Bar] = []
    for _, group in groupby(daily, key=lambda b: _period_key(b.date, period)):
        bars = list(group)
        normal = [b for b in bars if b.trade_status == 1]
        src = normal or bars
        out.append(
            Bar(
                date=src[-1].date,
                open=src[0].open,
                high=max(b.high for b in src),
                low=min(b.low for b in src),
                close=src[-1].close,
                volume=_sum_opt([b.volume for b in src]),
                amount=_sum_opt([b.amount for b in src]),
                raw_close=src[-1].raw_close,
                trade_status=1,
            )
        )
    return out
