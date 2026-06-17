"""多股对齐到统一交易日轴（M2）。

规则（设计规格 §3.3）：
- 正常交易日：用当天数据。
- 停牌日（trade_status=0）或缺口（超长停牌整天缺）：用**前值横线填充**，不被占位价污染。
- 上市前：留空（None），不参与。
输出每只票与 ``trade_days`` 等长、对齐的序列（填充位 trade_status=0、volume=None）。
"""

from dataclasses import replace
from datetime import date

from app.providers.base import Bar


def align(
    series_by_symbol: dict[str, list[Bar]], trade_days: list[date]
) -> dict[str, list[Bar | None]]:
    out: dict[str, list[Bar | None]] = {}
    for sym, bars in series_by_symbol.items():
        by_date = {b.date: b for b in bars}
        first_date = min(by_date) if by_date else None
        aligned: list[Bar | None] = []
        last: Bar | None = None
        for d in trade_days:
            if first_date is None or d < first_date:
                aligned.append(None)  # 上市前
                continue
            b = by_date.get(d)
            if b is not None and b.trade_status == 1:
                last = b
                aligned.append(b)
            elif last is not None:
                # 停牌占位 / 缺口 → 前值横线填充
                aligned.append(replace(last, date=d, trade_status=0, volume=None, amount=None))
            else:
                aligned.append(None)
        out[sym] = aligned
    return out
