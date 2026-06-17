"""归一化对比（M2 核心差异化功能）。

以 base_date 各标的后复权 close 为基准，输出累计涨跌幅(%)序列（涨跌幅与复权方式无关，
用后复权最稳）。base_date 当天=0；之前留空；上市晚的标的从其自身起点 0% 起。
"""

from dataclasses import dataclass
from datetime import date

from app.providers.base import Bar


@dataclass
class NormalizedSeries:
    values: list[float | None]  # 与 trade_days 等长的累计涨跌幅(%)
    latest_pct: float | None  # 最新一天的累计涨跌幅，供图例显示


def default_base_date(aligned: dict[str, list[Bar | None]], trade_days: list[date]) -> date | None:
    """默认基准日 = 所有标的都已有数据的最早共同交易日（= 各标的首个有数据日的最大值）。"""
    firsts: list[int] = []
    for vals in aligned.values():
        idx = next((i for i, v in enumerate(vals) if v is not None), None)
        if idx is None:
            return None  # 有标的全程无数据
        firsts.append(idx)
    if not firsts:
        return None
    return trade_days[max(firsts)]


def normalize(
    aligned: dict[str, list[Bar | None]], trade_days: list[date], base_date: date
) -> dict[str, NormalizedSeries]:
    # base_date 不是交易日时，取其后第一个交易日
    bi = next((i for i, d in enumerate(trade_days) if d >= base_date), None)
    out: dict[str, NormalizedSeries] = {}
    for sym, vals in aligned.items():
        if bi is None:
            out[sym] = NormalizedSeries([None] * len(trade_days), None)
            continue
        # P0 = base 日(或其后首个有数据日)的后复权 close — 支撑上市晚的标的从自身起点起
        p0: float | None = None
        for i in range(bi, len(vals)):
            v = vals[i]
            if v is not None:
                p0 = float(v.close)
                break
        series_vals: list[float | None] = []
        latest: float | None = None
        for i, v in enumerate(vals):
            if i < bi or v is None or p0 is None:
                series_vals.append(None)
            else:
                pct = round((float(v.close) / p0 - 1) * 100, 4)
                series_vals.append(pct)
                latest = pct
        out[sym] = NormalizedSeries(series_vals, latest)
    return out
